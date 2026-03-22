# MoonPay CLI Integration Guide for VaultGuard

## Overview

The MoonPay CLI (`@moonpay/cli`) is a crypto infrastructure CLI designed for AI agents.
It runs as an MCP (Model Context Protocol) server via `mp mcp`, exposing all its tools
to any MCP-compatible client over stdio JSON-RPC.

VaultGuard integrates with the MoonPay CLI to gain real crypto execution capabilities:
swaps, bridges, portfolio balances, token discovery, prediction markets, and more --
all while preserving VaultGuard's privacy-first reasoning model.

Homepage: https://agents.moonpay.com
npm: https://www.npmjs.com/package/@moonpay/cli
Skills repo: https://github.com/moonpay/skills

---

## 1. Installation

### Install the CLI globally

```bash
npm install -g @moonpay/cli
```

This installs two binaries: `mp` and `moonpay`.

### Verify installation

```bash
mp --version
mp --help
```

### Authenticate

```bash
# Send an OTP to your email
mp login --email you@example.com

# Enter the OTP code from email
mp verify --email you@example.com --code 123456

# Confirm login
mp user retrieve
```

### Create a wallet

```bash
# Create a new HD wallet (supports Solana, Ethereum, Bitcoin, Tron)
mp wallet create --name "vaultguard"

# Or import an existing wallet
mp wallet import --name "vaultguard" --mnemonic "word1 word2 ..."

# List wallets
mp wallet list
```

Wallets are stored encrypted in `~/.config/moonpay/wallets.json` (AES-256-GCM,
key stored in OS keychain). Private keys never leave the machine.

---

## 2. Running as an MCP Server

The MoonPay CLI acts as an MCP server when invoked with `mp mcp`. This uses
stdio transport (JSON-RPC 2.0 over stdin/stdout with Content-Length headers).

### Add to Claude Code

```bash
claude mcp add moonpay -- mp mcp
```

### Add to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "moonpay": {
      "command": "mp",
      "args": ["mcp"]
    }
  }
}
```

### Programmatic connection (Python)

VaultGuard's `cli_agent.py` spawns `mp mcp` as a subprocess and communicates
via JSON-RPC over stdio. See the `MoonPayMCPBridge` class in `cli_agent.py`.

---

## 3. Available MCP Tools

When running as an MCP server, the MoonPay CLI exposes all its commands as tools:

### Wallet Management
| Tool | Description |
|------|-------------|
| `wallet_create` | Create a new HD wallet |
| `wallet_list` | List all local wallets |
| `wallet_retrieve` | Get wallet details |
| `wallet_delete` | Delete a wallet |
| `wallet_import` | Import from mnemonic or private key |

### Token Operations
| Tool | Description |
|------|-------------|
| `token_search` | Search tokens by name or symbol |
| `token_retrieve` | Get full token details and market data |
| `token_trending_list` | List trending tokens on a chain |
| `token_balance_list` | List all token balances for a wallet |
| `token_swap` | Swap tokens on the same chain |
| `token_bridge` | Bridge tokens across chains |
| `token_transfer` | Transfer tokens to another address |

### Prediction Markets (Polymarket / Kalshi)
| Tool | Description |
|------|-------------|
| `prediction_market_market_search` | Search prediction markets |
| `prediction_market_market_trending_list` | Trending markets by volume |
| `prediction_market_market_event_retrieve` | Full event details |
| `prediction_market_position_buy` | Buy outcome shares |
| `prediction_market_position_sell` | Sell outcome shares |
| `prediction_market_position_list` | View open/closed positions |
| `prediction_market_pnl_retrieve` | Get P&L summary |

### Fiat On/Off Ramp
| Tool | Description |
|------|-------------|
| `buy_crypto` | Buy crypto with card/bank via MoonPay checkout |
| `virtual_account_*` | Fiat on-ramp and off-ramp via virtual accounts |

### Transactions
| Tool | Description |
|------|-------------|
| `transaction_list` | List transactions |
| `transaction_retrieve` | Get transaction details |
| `transaction_send` | Sign and send a transaction |

### Supported Chains
solana, ethereum, base, polygon, arbitrum, optimism, bnb, avalanche, bitcoin, tron, ton

---

## 4. Connecting to VaultGuard's cli_agent.py

VaultGuard's `cli_agent.py` includes a `MoonPayMCPBridge` class that:

1. Spawns `mp mcp` as a child process
2. Sends JSON-RPC 2.0 messages over stdio
3. Exposes Python methods for each MoonPay tool category
4. Integrates with VaultGuard's private reasoning pipeline

### Architecture

```
User
  |
  v
cli_agent.py (VaultGuard CLI)
  |
  +-- PrivateReasoner (private analysis, hashed proofs)
  |
  +-- MoonPayMCPBridge (MCP client over stdio)
        |
        v
      mp mcp (MoonPay CLI as MCP server)
        |
        +-- Wallet management
        +-- Token swaps & bridges
        +-- Portfolio balances
        +-- Prediction markets
        +-- Fiat on/off ramp
```

### Flow: Private Portfolio Analysis with Live Data

1. `MoonPayMCPBridge.get_balances()` fetches real wallet balances
2. Balances are passed to `PrivateReasoner.reason_privately()` as sensitive input
3. Private reasoning produces public-safe rebalancing actions
4. Actions can be executed via `MoonPayMCPBridge.swap_tokens()` or `.bridge_tokens()`
5. All reasoning hashes are logged; raw data is never persisted

---

## 5. What the User Needs to Do

### Required

1. **Install Node.js** (v18+) and npm
2. **Install MoonPay CLI**: `npm install -g @moonpay/cli`
3. **Authenticate**: `mp login --email <email>` then `mp verify --email <email> --code <code>`
4. **Create a wallet**: `mp wallet create --name "vaultguard"`

### Optional

- **VENICE_API_KEY**: Set in environment for Venice private inference (VaultGuard's AI backend)
- **Fund your wallet**: Transfer crypto to your wallet address for live swaps/bridges
- **Register for prediction markets**: `mp prediction-market user create --provider polymarket --wallet <address>`

### Environment Variables

```bash
# Required for VaultGuard private reasoning
export VENICE_API_KEY="your-venice-api-key"

# Optional: override default MoonPay MCP tool names
export MOONPAY_BALANCES_TOOL="token_balance_list"
export MOONPAY_SWAP_TOOL="token_swap"
export MOONPAY_BRIDGE_TOOL="token_bridge"
export MOONPAY_MARKET_TOOL="token_search"
```

---

## 6. Config File Locations

| File | Location |
|------|----------|
| Wallets | `~/.config/moonpay/wallets.json` (encrypted AES-256-GCM) |
| Credentials | `~/.config/moonpay/credentials.json` (encrypted AES-256-GCM) |
| Config | `~/.config/moonpay/config.json` |
| Encryption key | OS keychain (`moonpay-cli` / `encryption-key`) |

---

## 7. Key CLI Commands Reference

```bash
# Auth
mp login --email user@example.com
mp verify --email user@example.com --code 123456
mp user retrieve

# Wallets
mp wallet create --name "main"
mp wallet list
mp wallet retrieve --wallet "main"

# Check balances
mp token balance list --wallet <address> --chain ethereum
mp token balance list --wallet <address> --chain solana

# Search tokens
mp token search --query "ETH" --chain ethereum
mp token trending list --chain solana

# Swap (same chain)
mp token swap --wallet main --chain ethereum \
  --from-token 0x0000000000000000000000000000000000000000 \
  --from-amount 0.1 \
  --to-token <usdc-address>

# Bridge (cross chain)
mp token bridge --from-wallet main --from-chain ethereum \
  --from-token 0x0000000000000000000000000000000000000000 \
  --from-amount 0.01 \
  --to-chain polygon --to-token <usdc-polygon-address>

# Prediction markets
mp prediction-market market search --provider polymarket --query "bitcoin"
mp prediction-market market trending list --provider polymarket --limit 10

# MCP server mode
mp mcp
```
