#!/usr/bin/env python3
"""
VaultGuard CLI Agent
=====================
Command-line interface for running VaultGuard private reasoning sessions,
powered by the MoonPay CLI as its primary crypto action layer.

Supports:
  - Private portfolio / treasury analysis
  - Governance proposal deliberation
  - Deal evaluation
  - Session verification and proof export
  - Live wallet balances via MoonPay CLI (mp mcp)
  - Token swaps and cross-chain bridges via MoonPay CLI
  - Token discovery and market data via MoonPay CLI
  - Prediction market operations via MoonPay CLI

The MoonPay CLI runs as an MCP server (`mp mcp`) and VaultGuard communicates
with it over stdio JSON-RPC 2.0. All sensitive data stays in VaultGuard's
private reasoning layer; only public-safe actions are forwarded to MoonPay.

Usage:
    python cli_agent.py analyze --task treasury_strategy --data "Portfolio: ..."
    python cli_agent.py analyze --task governance_analysis --file proposal.txt
    python cli_agent.py verify  --session-id vg-0001-185954
    python cli_agent.py report
    python cli_agent.py describe
    python cli_agent.py moonpay-status
    python cli_agent.py balances --wallet 0x... --chain ethereum
    python cli_agent.py swap --wallet main --chain ethereum --from ETH --to USDC --amount 0.1
    python cli_agent.py portfolio-live --wallet 0x... --chains ethereum,base,polygon
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import os
import shutil
import threading
from datetime import datetime
from typing import Optional

# Allow running from the src/ directory or project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from private_reasoner import PrivateReasoner, PrivateReasoning


# ---------------------------------------------------------------------------
# MoonPay CLI MCP Bridge
# ---------------------------------------------------------------------------

class MoonPayMCPBridge:
    """
    Bridge to the MoonPay CLI running as an MCP server.

    Spawns `mp mcp` as a child process and communicates via JSON-RPC 2.0
    over stdio (Content-Length framed messages). Provides typed Python
    methods for wallet balances, token swaps, bridges, market data, and
    prediction market operations.

    Privacy model:
      - VaultGuard never sends raw sensitive data to MoonPay
      - MoonPay is used only for public on-chain actions (balances, swaps)
      - Private reasoning stays in PrivateReasoner (hashed, in-memory only)
    """

    MCP_PROTOCOL_VERSION = "2024-11-05"

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._buffer = ""
        self._connected = False
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._connected

    @staticmethod
    def is_available() -> bool:
        """Check if the MoonPay CLI (`mp`) is installed."""
        return shutil.which("mp") is not None

    def connect(self) -> bool:
        """
        Spawn `mp mcp` and perform the MCP handshake.
        Returns True if connected, False on error.
        """
        if not self.is_available():
            return False

        try:
            self._process = subprocess.Popen(
                ["mp", "mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # MCP initialize handshake
            result = self._request("initialize", {
                "protocolVersion": self.MCP_PROTOCOL_VERSION,
                "clientInfo": {
                    "name": "vaultguard-cli-agent",
                    "version": "1.0.0",
                },
                "capabilities": {},
            })

            # Send initialized notification
            self._notify("notifications/initialized", {})

            self._connected = result is not None
            return self._connected

        except (OSError, FileNotFoundError):
            self._connected = False
            return False

    def disconnect(self):
        """Shut down the MCP server process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
        self._connected = False

    # -- MoonPay tool wrappers -----------------------------------------------

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call any MoonPay MCP tool by name."""
        result = self._request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return self._parse_tool_result(result)

    def list_tools(self) -> list:
        """List all available MCP tools from the MoonPay server."""
        result = self._request("tools/list", {})
        if result and isinstance(result, dict):
            return result.get("tools", [])
        return []

    def get_balances(self, wallet: str, chain: str) -> dict:
        """Fetch token balances for a wallet on a given chain."""
        return self.call_tool("token_balance_list", {
            "wallet": wallet,
            "chain": chain,
        })

    def get_multi_chain_balances(self, wallet: str, chains: list[str]) -> dict:
        """Fetch balances across multiple chains."""
        all_balances = {}
        for chain in chains:
            try:
                all_balances[chain] = self.get_balances(wallet, chain)
            except Exception as e:
                all_balances[chain] = {"error": str(e)}
        return all_balances

    def swap_tokens(self, wallet: str, chain: str,
                    from_token: str, to_token: str,
                    amount: str) -> dict:
        """Swap tokens on the same chain."""
        return self.call_tool("token_swap", {
            "wallet": wallet,
            "chain": chain,
            "from_token": from_token,
            "to_token": to_token,
            "from_amount": amount,
        })

    def bridge_tokens(self, wallet: str, from_chain: str, to_chain: str,
                      from_token: str, to_token: str,
                      amount: str) -> dict:
        """Bridge tokens across chains."""
        return self.call_tool("token_bridge", {
            "from_wallet": wallet,
            "from_chain": from_chain,
            "from_token": from_token,
            "from_amount": amount,
            "to_chain": to_chain,
            "to_token": to_token,
        })

    def search_tokens(self, query: str, chain: str) -> dict:
        """Search for tokens by name or symbol."""
        return self.call_tool("token_search", {
            "query": query,
            "chain": chain,
        })

    def get_trending_tokens(self, chain: str) -> dict:
        """Get trending tokens on a chain."""
        return self.call_tool("token_trending_list", {
            "chain": chain,
        })

    def search_prediction_markets(self, query: str,
                                  provider: str = "polymarket") -> dict:
        """Search prediction markets."""
        return self.call_tool("prediction_market_market_search", {
            "provider": provider,
            "query": query,
        })

    def get_trending_markets(self, provider: str = "polymarket",
                             limit: int = 10) -> dict:
        """Get trending prediction markets."""
        return self.call_tool("prediction_market_market_trending_list", {
            "provider": provider,
            "limit": limit,
        })

    # -- JSON-RPC transport --------------------------------------------------

    def _next_id(self) -> int:
        with self._lock:
            self._request_id += 1
            return self._request_id

    def _request(self, method: str, params: dict) -> Optional[dict]:
        """Send a JSON-RPC request and wait for the response."""
        if not self._process:
            return None

        msg_id = self._next_id()
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params,
        })
        frame = f"Content-Length: {len(payload.encode('utf-8'))}\r\n\r\n{payload}"

        try:
            self._process.stdin.write(frame.encode("utf-8"))
            self._process.stdin.flush()
            return self._read_response(msg_id)
        except (BrokenPipeError, OSError):
            self._connected = False
            return None

    def _notify(self, method: str, params: dict):
        """Send a JSON-RPC notification (no response expected)."""
        if not self._process:
            return
        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        })
        frame = f"Content-Length: {len(payload.encode('utf-8'))}\r\n\r\n{payload}"
        try:
            self._process.stdin.write(frame.encode("utf-8"))
            self._process.stdin.flush()
        except (BrokenPipeError, OSError):
            self._connected = False

    def _read_response(self, expected_id: int, timeout: float = 30.0) -> Optional[dict]:
        """Read a JSON-RPC response with Content-Length framing."""
        if not self._process or not self._process.stdout:
            return None

        import select

        deadline = __import__("time").time() + timeout

        while __import__("time").time() < deadline:
            # Try to read more data
            ready, _, _ = select.select([self._process.stdout], [], [], 0.1)
            if ready:
                chunk = self._process.stdout.read1(4096) if hasattr(self._process.stdout, 'read1') else b""
                if chunk:
                    self._buffer += chunk.decode("utf-8", errors="replace")

            # Try to parse a complete message from the buffer
            while True:
                sep = self._buffer.find("\r\n\r\n")
                if sep < 0:
                    break

                header = self._buffer[:sep]
                match = None
                for line in header.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        try:
                            match = int(line.split(":", 1)[1].strip())
                        except ValueError:
                            pass

                if match is None:
                    # Skip malformed header
                    self._buffer = self._buffer[sep + 4:]
                    continue

                body_start = sep + 4
                full_length = body_start + match

                if len(self._buffer) < full_length:
                    break  # Need more data

                body = self._buffer[body_start:full_length]
                self._buffer = self._buffer[full_length:]

                try:
                    msg = json.loads(body)
                except json.JSONDecodeError:
                    continue

                if msg.get("id") == expected_id:
                    if "error" in msg:
                        raise RuntimeError(
                            f"MoonPay MCP error: {msg['error'].get('message', msg['error'])}"
                        )
                    return msg.get("result")

        return None

    @staticmethod
    def _parse_tool_result(result: Optional[dict]) -> dict:
        """Parse MCP tool result, extracting text content if present."""
        if result is None:
            return {}
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and content:
                first = content[0]
                if isinstance(first, dict) and "text" in first:
                    try:
                        return json.loads(first["text"])
                    except (json.JSONDecodeError, TypeError):
                        return {"text": first["text"]}
        return result if isinstance(result, dict) else {"raw": result}


# ---------------------------------------------------------------------------
# Shared instances (persist across commands in interactive mode)
# ---------------------------------------------------------------------------

_reasoner: Optional[PrivateReasoner] = None
_moonpay: Optional[MoonPayMCPBridge] = None


def get_reasoner(api_key: str = "") -> PrivateReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = PrivateReasoner(api_key)
    return _reasoner


def get_moonpay() -> MoonPayMCPBridge:
    """Get or create the MoonPay MCP bridge (lazy connection)."""
    global _moonpay
    if _moonpay is None:
        _moonpay = MoonPayMCPBridge()
    return _moonpay


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_analyze(args):
    """Run a private reasoning session."""
    reasoner = get_reasoner(args.api_key or "")

    # Get sensitive data from --data or --file
    if args.file:
        with open(args.file) as f:
            data = f.read().strip()
    elif args.data:
        data = args.data
    else:
        # Read from stdin if neither flag provided
        print("Enter sensitive data (Ctrl-D to finish):", file=sys.stderr)
        data = sys.stdin.read().strip()

    if not data:
        print("Error: no data provided. Use --data, --file, or pipe via stdin.", file=sys.stderr)
        sys.exit(1)

    task = args.task
    privacy = args.privacy_mode

    print(f"\n  VaultGuard Private Analysis")
    print(f"  Task:    {task}")
    print(f"  Privacy: {privacy}")
    print(f"  {'=' * 42}\n")

    session = reasoner.reason_privately(data, task, privacy)

    print(f"  Session ID:     {session.session_id}")
    print(f"  Input hash:     {session.input_hash[:32]}...")
    print(f"  Reasoning hash: {session.reasoning_hash[:32]}...")
    print(f"  Model:          {session.model_used}")
    print(f"  Privacy mode:   {session.privacy_mode}")
    print()
    print(f"  Summary:")
    print(f"    {session.output_summary[:120]}...")
    print()
    print(f"  Recommended actions:")
    for i, action in enumerate(session.output_actions, 1):
        print(f"    {i}. {action}")
    print()

    # Export proof if requested
    if args.output:
        proof = {
            "session_id": session.session_id,
            "input_hash": session.input_hash,
            "reasoning_hash": session.reasoning_hash,
            "output_actions": session.output_actions,
            "output_summary": session.output_summary,
            "privacy_mode": session.privacy_mode,
            "model": session.model_used,
            "timestamp": session.timestamp,
        }
        with open(args.output, "w") as f:
            json.dump(proof, f, indent=2)
        print(f"  Proof exported to {args.output}")

    return session


def cmd_portfolio(args):
    """Quick portfolio analysis — crypto-native shortcut."""
    reasoner = get_reasoner(args.api_key or "")

    # Build portfolio string from positional args or prompt
    if args.holdings:
        portfolio = ", ".join(args.holdings)
    else:
        print("Enter portfolio (e.g. '40% ETH, 30% BTC, 30% USDC'):", file=sys.stderr)
        portfolio = input().strip()

    data = f"Portfolio holdings: {portfolio}. Analyze for optimal rebalancing."
    session = reasoner.reason_privately(data, "treasury_strategy")

    print(f"\n  Portfolio Analysis (private)")
    print(f"  {'=' * 42}")
    print(f"  Session: {session.session_id}")
    print(f"  Proof:   {session.input_hash[:24]}...")
    print()
    print(f"  Recommendations:")
    for i, a in enumerate(session.output_actions, 1):
        print(f"    {i}. {a}")
    print()


def cmd_verify(args):
    """Verify a previous session."""
    reasoner = get_reasoner()

    target = args.session_id
    for s in reasoner.sessions:
        if s.session_id == target:
            proof = reasoner.verify_session(s)
            print(f"\n  Session Verification")
            print(f"  {'=' * 42}")
            print(f"  Session ID:     {proof['session_id']}")
            print(f"  Verified:       {proof['verified']}")
            print(f"  Input hash:     {proof['input_hash'][:32]}...")
            print(f"  Reasoning hash: {proof['reasoning_hash'][:32]}...")
            print(f"  Privacy mode:   {proof['privacy_mode']}")
            print(f"  Timestamp:      {proof['timestamp']}")
            print(f"\n  {proof['proof']}")
            return

    print(f"  Session {target} not found in current session.", file=sys.stderr)
    sys.exit(1)


def cmd_report(args):
    """Print a full report of all sessions."""
    reasoner = get_reasoner()
    if not reasoner.sessions:
        print("  No sessions yet. Run 'analyze' first.")
        return
    print(reasoner.generate_report())


def cmd_describe(args):
    """Print agent capabilities (useful for MoonPay / Olas discovery)."""
    mp = get_moonpay()
    mp_status = "CONNECTED" if mp.connected else ("AVAILABLE (not connected)" if mp.is_available() else "NOT INSTALLED")

    print(f"""
  VaultGuard CLI Agent
  ====================
  Privacy-preserving AI reasoning for crypto portfolios and DAO operations.
  Powered by MoonPay CLI as the primary crypto action layer.

  MoonPay CLI Status: {mp_status}

  Private Reasoning Capabilities:
    treasury_strategy    Analyze portfolio composition, recommend rebalancing
    governance_analysis  Evaluate governance proposals, output vote
    deal_evaluation      Assess deal terms, recommend negotiation position

  MoonPay CLI Capabilities (via MCP):
    balances             Fetch live wallet balances across chains
    swap                 Swap tokens on the same chain
    bridge               Bridge tokens across chains
    search               Search and discover tokens
    trending             Find trending tokens and markets
    prediction-markets   Trade on Polymarket and Kalshi
    buy-crypto           Buy crypto with fiat

  Privacy Model:
    - Input data: SHA-256 hashed, never stored
    - Reasoning: in-memory only, never persisted
    - Output: public-safe summaries and actions only
    - Proof: cryptographic hashes prove computation
    - MoonPay: used only for public on-chain actions (no sensitive data sent)

  Supported Chains:
    ethereum, base, polygon, arbitrum, optimism, solana, bnb, avalanche

  Run 'vaultguard --help' for all commands.
""")


def cmd_moonpay_status(args):
    """Check MoonPay CLI availability and connection status."""
    print(f"\n  MoonPay CLI Integration Status")
    print(f"  {'=' * 42}\n")

    # Check if mp binary is installed
    mp_path = shutil.which("mp")
    if mp_path:
        print(f"  CLI binary:   FOUND at {mp_path}")
    else:
        print(f"  CLI binary:   NOT FOUND")
        print(f"  Install with: npm install -g @moonpay/cli")
        print(f"  Then run:     mp login --email <email>")
        return

    # Check version
    try:
        version_result = subprocess.run(
            ["mp", "--version"], capture_output=True, text=True, timeout=5
        )
        version = version_result.stdout.strip() or "unknown"
        print(f"  CLI version:  {version}")
    except Exception:
        print(f"  CLI version:  could not determine")

    # Check authentication
    try:
        user_result = subprocess.run(
            ["mp", "user", "retrieve"], capture_output=True, text=True, timeout=10
        )
        if user_result.returncode == 0:
            print(f"  Auth status:  AUTHENTICATED")
        else:
            print(f"  Auth status:  NOT AUTHENTICATED")
            print(f"  Run:          mp login --email <email>")
    except Exception:
        print(f"  Auth status:  could not determine")

    # Check wallets
    try:
        wallet_result = subprocess.run(
            ["mp", "wallet", "list"], capture_output=True, text=True, timeout=10
        )
        if wallet_result.returncode == 0 and wallet_result.stdout.strip():
            print(f"  Wallets:      found")
        else:
            print(f"  Wallets:      none")
            print(f"  Create with:  mp wallet create --name vaultguard")
    except Exception:
        print(f"  Wallets:      could not determine")

    # Try MCP connection
    print(f"\n  MCP Connection Test")
    print(f"  {'-' * 42}")
    mp = get_moonpay()
    if mp.connect():
        print(f"  MCP server:   CONNECTED (mp mcp)")

        # List available tools
        try:
            tools = mp.list_tools()
            if tools:
                print(f"  Tools:        {len(tools)} available")
                for tool in tools[:10]:
                    name = tool.get("name", "unknown") if isinstance(tool, dict) else str(tool)
                    print(f"                - {name}")
                if len(tools) > 10:
                    print(f"                ... and {len(tools) - 10} more")
            else:
                print(f"  Tools:        (could not enumerate)")
        except Exception:
            print(f"  Tools:        (could not enumerate)")

        mp.disconnect()
    else:
        print(f"  MCP server:   COULD NOT CONNECT")
        print(f"  The CLI is installed but `mp mcp` did not start.")
        print(f"  Make sure you are authenticated: mp login --email <email>")

    print()


def cmd_balances(args):
    """
    Fetch live wallet balances via MoonPay CLI.

    Requires MoonPay CLI authentication. The CLI communicates via MCP
    (JSON-RPC 2.0 over stdio) to call the token_balance_list tool.
    Balances are fetched as public on-chain data -- no private reasoning
    is involved in this step.
    """
    mp = get_moonpay()

    if not mp.is_available():
        print("  MoonPay CLI (`mp`) is not installed.", file=sys.stderr)
        print("  Install: npm install -g @moonpay/cli", file=sys.stderr)
        print("  Then:    mp login --email <your-email>", file=sys.stderr)
        print("\n  Tip: Run 'python3 src/cli_agent.py demo' to see the full pipeline without auth.", file=sys.stderr)
        sys.exit(1)

    if not mp.connect():
        print("  Could not connect to MoonPay MCP server (`mp mcp`).", file=sys.stderr)
        print("  The CLI is installed but authentication is required.", file=sys.stderr)
        print("  Authenticate: mp login --email <your-email>", file=sys.stderr)
        print("  Create wallet: mp wallet create --name vaultguard", file=sys.stderr)
        print("\n  Tip: Run 'python3 src/cli_agent.py demo' to see the full pipeline without auth.", file=sys.stderr)
        sys.exit(1)

    wallet = args.wallet
    chain = args.chain

    print(f"\n  Wallet Balances (via MoonPay CLI)")
    print(f"  {'=' * 42}")
    print(f"  Wallet: {wallet}")
    print(f"  Chain:  {chain}\n")

    try:
        result = mp.get_balances(wallet, chain)
        if isinstance(result, dict) and "error" in result:
            print(f"  Error: {result['error']}", file=sys.stderr)
        else:
            print(f"  {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
    finally:
        mp.disconnect()


def cmd_swap(args):
    """
    Execute a token swap via MoonPay CLI.

    Requires MoonPay CLI authentication with a wallet configured.
    The swap is a public on-chain action executed through MoonPay's
    token_swap MCP tool. No private reasoning data is sent to MoonPay.
    """
    mp = get_moonpay()

    if not mp.is_available():
        print("  MoonPay CLI (`mp`) is not installed.", file=sys.stderr)
        print("  Install: npm install -g @moonpay/cli", file=sys.stderr)
        print("  Then:    mp login --email <your-email>", file=sys.stderr)
        sys.exit(1)

    if not mp.connect():
        print("  Could not connect to MoonPay MCP server (`mp mcp`).", file=sys.stderr)
        print("  The CLI is installed but authentication is required.", file=sys.stderr)
        print("  Authenticate: mp login --email <your-email>", file=sys.stderr)
        print("  Create wallet: mp wallet create --name vaultguard", file=sys.stderr)
        sys.exit(1)

    # First resolve token symbols to addresses if needed
    from_token = args.from_token
    to_token = args.to_token

    print(f"\n  Token Swap (via MoonPay CLI)")
    print(f"  {'=' * 42}")
    print(f"  Wallet:  {args.wallet}")
    print(f"  Chain:   {args.chain}")
    print(f"  From:    {from_token}")
    print(f"  To:      {to_token}")
    print(f"  Amount:  {args.amount}\n")

    try:
        result = mp.swap_tokens(
            wallet=args.wallet,
            chain=args.chain,
            from_token=from_token,
            to_token=to_token,
            amount=args.amount,
        )
        print(f"  Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
    finally:
        mp.disconnect()


def cmd_portfolio_live(args):
    """
    Fetch live balances via MoonPay CLI, then run VaultGuard private analysis.

    This is the key integration point demonstrating the privacy pipeline:
      1. MoonPay CLI fetches live on-chain balances (public data retrieval)
      2. VaultGuard's PrivateReasoner hashes the balance data (SHA-256)
      3. Reasoning runs in-memory only (Venice API or local fallback)
      4. Only public-safe recommendations are output
      5. Raw balance data is discarded after hashing -- never persisted

    MoonPay is used solely as a public data source. No sensitive reasoning
    or private portfolio strategy ever flows to MoonPay.
    """
    reasoner = get_reasoner(args.api_key or "")
    mp = get_moonpay()

    chains = [c.strip() for c in args.chains.split(",")]
    wallet = args.wallet

    print(f"\n  VaultGuard Live Portfolio Analysis")
    print(f"  {'=' * 42}")
    print(f"  Wallet: {wallet}")
    print(f"  Chains: {', '.join(chains)}")
    print(f"  Privacy: full (balances hashed after fetch)\n")

    # Step 1: Fetch live balances via MoonPay CLI
    balances_data = {}
    if mp.is_available() and mp.connect():
        print(f"  [1/3] Fetching live balances via MoonPay CLI...")
        try:
            balances_data = mp.get_multi_chain_balances(wallet, chains)
            print(f"        Fetched from {len(chains)} chain(s)")
        except Exception as e:
            print(f"        Warning: could not fetch live data ({e})")
        finally:
            mp.disconnect()
    else:
        print(f"  [1/3] MoonPay CLI not available -- requires authentication")
        print(f"        Install: npm install -g @moonpay/cli")
        print(f"        Auth:    mp login --email <your-email>")
        print(f"        Using provided data only")

    # Step 2: Run private reasoning on the balance data
    print(f"  [2/3] Running private analysis...")
    sensitive_data = json.dumps({
        "wallet": wallet,
        "chains": chains,
        "balances": balances_data if balances_data else "no live data available",
        "request": "Analyze portfolio composition and recommend rebalancing strategy",
    })

    session = reasoner.reason_privately(sensitive_data, "treasury_strategy")

    # Step 3: Output public-safe results
    print(f"  [3/3] Analysis complete\n")
    print(f"  Session:   {session.session_id}")
    print(f"  Data hash: {session.input_hash[:32]}...")
    print(f"  Proof:     {session.reasoning_hash[:32]}...")
    print()
    print(f"  Recommendations:")
    for i, a in enumerate(session.output_actions, 1):
        print(f"    {i}. {a}")
    print()
    print(f"  (Raw balances hashed and discarded -- only recommendations are public)")
    print()


def cmd_demo(args):
    """
    Run a full demonstration of VaultGuard's MoonPay CLI integration.

    Shows the complete privacy pipeline without requiring MoonPay authentication:
      - Simulated live balance fetch (what MoonPay would return)
      - Private reasoning over the portfolio data
      - Public-safe output with cryptographic proof

    This is useful for judges, reviewers, and developers who want to see
    the end-to-end flow without needing MoonPay credentials.
    """
    reasoner = get_reasoner(args.api_key or "")

    print(f"\n  VaultGuard MoonPay Integration Demo")
    print(f"  {'=' * 50}")
    print(f"  Mode: demonstration (no MoonPay auth required)\n")

    # Step 1: Show what MoonPay CLI provides
    print(f"  [1/5] MoonPay CLI Capabilities (92 MCP tools):")
    print(f"        - token_balance_list: Fetch wallet balances across chains")
    print(f"        - token_swap: Swap tokens on the same chain")
    print(f"        - token_bridge: Bridge tokens across chains")
    print(f"        - token_search: Discover tokens by name/symbol")
    print(f"        - token_trending_list: Find trending tokens")
    print(f"        - prediction_market_*: Trade on Polymarket/Kalshi")
    print(f"        - wallet_*: Manage wallets and keys")
    print()

    # Step 2: Simulate balance data (what MoonPay would return)
    print(f"  [2/5] Simulated live balance data (from MoonPay CLI):")
    simulated_balances = {
        "ethereum": {
            "ETH": {"balance": "2.45", "usd_value": "8575.00"},
            "USDC": {"balance": "5000.00", "usd_value": "5000.00"},
            "stETH": {"balance": "1.20", "usd_value": "4200.00"},
        },
        "base": {
            "ETH": {"balance": "0.50", "usd_value": "1750.00"},
            "USDC": {"balance": "2000.00", "usd_value": "2000.00"},
        },
        "polygon": {
            "MATIC": {"balance": "1500.00", "usd_value": "975.00"},
            "USDC": {"balance": "1000.00", "usd_value": "1000.00"},
        },
    }
    for chain, tokens in simulated_balances.items():
        print(f"        {chain}:")
        for token, data in tokens.items():
            print(f"          {token}: {data['balance']} (${data['usd_value']})")
    print()

    # Step 3: Privacy pipeline
    print(f"  [3/5] Privacy pipeline:")
    sensitive_data = json.dumps({
        "wallet": "0xdemo...1234",
        "chains": list(simulated_balances.keys()),
        "balances": simulated_balances,
        "total_usd": "$23,500",
        "request": "Analyze portfolio composition and recommend rebalancing strategy",
    })
    print(f"        Input data: {len(sensitive_data)} bytes of sensitive portfolio data")

    session = reasoner.reason_privately(sensitive_data, "treasury_strategy")

    print(f"        Input hash:     {session.input_hash[:32]}... (data NOT stored)")
    print(f"        Reasoning hash: {session.reasoning_hash[:32]}... (proves computation)")
    print(f"        Model:          {session.model_used}")
    print(f"        Privacy mode:   {session.privacy_mode}")
    print()

    # Step 4: Public-safe output
    print(f"  [4/5] Public-safe output (only this leaves VaultGuard):")
    print(f"        Session: {session.session_id}")
    print(f"        Actions:")
    for i, action in enumerate(session.output_actions, 1):
        print(f"          {i}. {action}")
    print()

    # Step 5: Verification
    proof = reasoner.verify_session(session)
    print(f"  [5/5] Verification:")
    print(f"        Verified: {proof['verified']}")
    print(f"        Proof:    {proof['proof'][:80]}...")
    print()

    print(f"  Privacy Guarantees:")
    print(f"    - Raw balance data (from MoonPay): HASHED and discarded after analysis")
    print(f"    - Reasoning steps: IN-MEMORY ONLY, never persisted")
    print(f"    - Output: PUBLIC-SAFE summaries and actions only")
    print(f"    - MoonPay: used solely for public on-chain data retrieval")
    print(f"    - No sensitive data ever flows to MoonPay")
    print()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vaultguard",
        description="VaultGuard -- Private AI reasoning agent powered by MoonPay CLI",
    )
    parser.add_argument("--api-key", default="", help="Venice API key (or set VENICE_API_KEY)")
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Run a private reasoning session")
    p_analyze.add_argument("--task", default="treasury_strategy",
                           choices=["treasury_strategy", "governance_analysis", "deal_evaluation"],
                           help="Type of analysis")
    p_analyze.add_argument("--data", help="Sensitive data string (careful with shell history)")
    p_analyze.add_argument("--file", help="Read sensitive data from file")
    p_analyze.add_argument("--privacy-mode", default="full", choices=["full", "hash_only"])
    p_analyze.add_argument("--output", "-o", help="Export proof JSON to this file")
    p_analyze.set_defaults(func=cmd_analyze)

    # portfolio (shortcut -- manual entry)
    p_port = sub.add_parser("portfolio", help="Quick private portfolio analysis")
    p_port.add_argument("holdings", nargs="*", help="e.g. '40%% ETH' '30%% BTC' '30%% USDC'")
    p_port.set_defaults(func=cmd_portfolio)

    # verify
    p_verify = sub.add_parser("verify", help="Verify a session's proof")
    p_verify.add_argument("session_id", help="Session ID to verify (e.g. vg-0001-185954)")
    p_verify.set_defaults(func=cmd_verify)

    # report
    p_report = sub.add_parser("report", help="Print full reasoning report")
    p_report.set_defaults(func=cmd_report)

    # describe
    p_desc = sub.add_parser("describe", help="Show agent capabilities")
    p_desc.set_defaults(func=cmd_describe)

    # --- MoonPay CLI integration commands ---

    # moonpay-status
    p_mp_status = sub.add_parser("moonpay-status",
                                 help="Check MoonPay CLI installation and MCP connection")
    p_mp_status.set_defaults(func=cmd_moonpay_status)

    # balances (via MoonPay CLI)
    p_bal = sub.add_parser("balances", help="Fetch live wallet balances via MoonPay CLI")
    p_bal.add_argument("--wallet", required=True, help="Wallet name or address")
    p_bal.add_argument("--chain", required=True,
                       help="Chain name (ethereum, base, polygon, solana, ...)")
    p_bal.set_defaults(func=cmd_balances)

    # swap (via MoonPay CLI)
    p_swap = sub.add_parser("swap", help="Swap tokens via MoonPay CLI")
    p_swap.add_argument("--wallet", required=True, help="Wallet name")
    p_swap.add_argument("--chain", required=True, help="Chain name")
    p_swap.add_argument("--from-token", required=True, help="Source token address")
    p_swap.add_argument("--to-token", required=True, help="Target token address")
    p_swap.add_argument("--amount", required=True, help="Amount to swap")
    p_swap.set_defaults(func=cmd_swap)

    # portfolio-live (MoonPay CLI + private reasoning)
    p_live = sub.add_parser("portfolio-live",
                            help="Fetch live balances via MoonPay, then analyze privately")
    p_live.add_argument("--wallet", required=True, help="Wallet name or address")
    p_live.add_argument("--chains", default="ethereum,base,polygon",
                        help="Comma-separated chain names")
    p_live.set_defaults(func=cmd_portfolio_live)

    # demo (full pipeline demo without MoonPay auth)
    p_demo = sub.add_parser("demo",
                            help="Run a full demo of the MoonPay + private reasoning pipeline "
                                 "(no MoonPay auth required)")
    p_demo.set_defaults(func=cmd_demo)

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
