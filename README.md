# VaultGuard: Private AI Reasoning with Public Verifiable Actions

> Think privately. Act publicly. Prove everything.

**Built for [The Synthesis Hackathon 2026](https://synthesis.md)**

**Live Dashboard:** [devanshug2307.github.io/vaultguard-agent](https://devanshug2307.github.io/vaultguard-agent/)

---

## Problem

AI agents handling treasury strategies, governance analysis, or deal negotiations need to think about sensitive information. But current agents expose everything — their reasoning, their data, their strategies. How can an agent analyze confidential data and act on it publicly, without leaking the private reasoning?

## Solution

VaultGuard separates **private reasoning** from **public action** with cryptographic proof:

1. **Input is hashed** — SHA-256 proves what was analyzed without revealing it
2. **Reasoning is in-memory only** — never persisted, never stored
3. **Output is public-safe** — only summaries and actions are exposed
4. **Hash-based verification** — proves computation happened honestly
5. **Compatible with Venice API** — zero-storage inference for true privacy

## Architecture

```
┌────────────────────────────────────────────────────┐
│                  VAULTGUARD AGENT                    │
├────────────────────────────────────────────────────┤
│                                                      │
│  PRIVATE ZONE (never stored)     PUBLIC ZONE         │
│  ┌──────────────────────┐       ┌────────────────┐  │
│  │ Sensitive Input       │──────>│ Summary        │  │
│  │ (hashed, not stored)  │       │ (public-safe)  │  │
│  │                       │       │                │  │
│  │ Private Reasoning     │──────>│ Actions        │  │
│  │ (in-memory only)      │       │ (executable)   │  │
│  │                       │       │                │  │
│  │ Reasoning Hash        │──────>│ Verification   │  │
│  │ (proof of computation)│       │ (hash-based)   │  │
│  └──────────────────────┘       └────────────────┘  │
│                                                      │
│  Privacy Guarantee:                                  │
│  • Input: HASHED (SHA-256)                           │
│  • Reasoning: IN-MEMORY ONLY                         │
│  • Output: PUBLIC-SAFE ONLY                          │
│  • Proof: Cryptographic hashes                       │
└────────────────────────────────────────────────────┘
```

## Use Cases

### 1. Private Treasury Strategy
```
Input:  Portfolio data, balances, runway ($3.5M, 18 months)
        → HASHED, never stored
Private: Analyze risk, model scenarios, calculate rebalancing
        → IN-MEMORY ONLY, never persisted
Public:  "Reduce volatile exposure 15%, increase yield positions"
        → Safe to share, no sensitive data exposed
Proof:   SHA-256 of input + reasoning proves computation happened
```

### 2. Private Governance Deliberation
```
Input:  Proposal details, voting data, stakeholder positions
Private: Evaluate impact, model outcomes, assess risks
Public:  "SUPPORT with amendments to address security concerns"
Proof:   Hash chain proves deliberation was thorough
```

### 3. Private Deal Evaluation
```
Input:  Term sheet, valuation, counterparty data
Private: Analyze terms, compare benchmarks, assess risks
Public:  "Accept with 10% haircut and milestone vesting"
Proof:   Computation proof without revealing terms
```

## How It Works

```python
from src.private_reasoner import PrivateReasoner

reasoner = PrivateReasoner()

# Reason over sensitive data privately
session = reasoner.reason_privately(
    sensitive_input="Portfolio: $3.5M across ETH, stETH, USDC...",
    task="treasury_strategy"
)

# Only public outputs are accessible
print(session.output_actions)   # ["Reduce volatile exposure 15%", ...]
print(session.input_hash)       # "a1b2c3..." (proves data was analyzed)
print(session.reasoning_hash)   # "d4e5f6..." (proves reasoning happened)

# Verify computation integrity
proof = reasoner.verify_session(session)
print(proof["verified"])        # True
```

## Venice API Integration

VaultGuard is designed for Venice's zero-storage inference:
- **Endpoint:** `https://api.venice.ai/api/v1/chat/completions`
- **API Key:** Configured (set `VENICE_API_KEY` in `.env`)
- **Privacy:** Venice stores nothing — no logs, no training data, no traces (zero-storage inference)
- **Models:** Llama 3.3 70B and others via Venice
- **Fallback:** Local reasoning when Venice is unavailable

The privacy guarantee: even the LLM provider (Venice) doesn't retain the data.

## Privacy Proof

Every session generates verifiable proof:

```json
{
  "session_id": "vg-0001-185954",
  "input_hash": "a1b2c3d4...",
  "reasoning_hash": "e5f6g7h8...",
  "output_actions": ["Reduce volatile exposure 15%", "Increase yield positions"],
  "verified": true,
  "timestamp": "2026-03-22T..."
}
```

**What this proves:**
- Input was analyzed (hash matches)
- Reasoning was performed (hash exists)
- Specific actions were generated
- All without revealing the private data

## Deployed Contracts

| Contract | Network | Address |
|----------|---------|---------|
| PrivacyVault | Base Sepolia | [`0x3AeDD41999383E9a351B0Cb984D5Bb8eac3AAB28`](https://sepolia.basescan.org/address/0x3AeDD41999383E9a351B0Cb984D5Bb8eac3AAB28) |
| VaultGuardSliceHook | Base Sepolia | [`0x8BC511BC3A63DB615Ab2d906Ba9C2A6EF79687b9`](https://sepolia.basescan.org/address/0x8BC511BC3A63DB615Ab2d906Ba9C2A6EF79687b9) |
| PrivacyVault (Slice Hook) | Base Sepolia | [`0x090FdF20D68fEA1923f9Af132086837c876a0102`](https://sepolia.basescan.org/address/0x090FdF20D68fEA1923f9Af132086837c876a0102) |
| VaultGuard Token | Status Network Sepolia | [`0x51C96F24A3D6aDc6B5bE391b778a847CCFc78Ba3`](https://sepoliascan.status.network/address/0x51C96F24A3D6aDc6B5bE391b778a847CCFc78Ba3) |

## Onchain Proof

Every private reasoning session is committed onchain with hashes (never raw data). **3 onchain reasoning sessions** plus **Slice Hook commerce proof** demonstrate the full privacy-preserving lifecycle:

| # | Action | TX Hash |
|---|--------|---------|
| 1 | Deploy PrivacyVault | [`0xee4682...`](https://sepolia.basescan.org/tx/0xee46829d529cb951926004d27db53976bee4185e211aca218f8e3cf53eb77d23) |
| 2 | Treasury Strategy (private reasoning session 1) | [`0x7c4ece...`](https://sepolia.basescan.org/tx/0x7c4ece9c262798a03bace90a41a237ba7827d912515210e14d6db596aabc0896) |
| 3 | Governance Deliberation (private reasoning session 2) | [`0x91b5d2...`](https://sepolia.basescan.org/tx/0x91b5d2b5bb6e0164b1c0c8fcba8f2c28bc39041d6511269447e990cf4ffa5c76) |
| 4 | Deal Evaluation (private reasoning session 3) | [`0x8455a8...`](https://sepolia.basescan.org/tx/0x8455a8616f543d0ef0dd77ee751d24ae2fd32f44b53616ecdb006fa9f546f242) |
| 5 | Deploy VaultGuardSliceHook | [`0x0fa323...`](https://sepolia.basescan.org/tx/0x0fa32309ed333c3bd192b2a331fc03f39a5c3b3f2517675e46cdbba4f1f42cc6) |
| 6 | Slice Commerce Proof (purchase demo) | [`0xd9c3d2...`](https://sepolia.basescan.org/tx/0xd9c3d29a44a54dc3e74e91c7eefe131027d0100df288f3ee9b4434757ace3a84) |

## Tests

**33/33 passing** (13 PrivacyVault + 20 VaultGuardSliceHook) — run with:
```bash
npx hardhat --config hardhat.config.cjs test
```

## Integrations

### Olas Autonomous Service (Hire on Olas)

VaultGuard is registered as an Olas-compatible autonomous service component. Other agents can discover, hire, and invoke it through the Olas marketplace.

```bash
# Run the Olas service demo
python3 src/olas_service.py
```

- Service descriptor with capabilities, pricing (0.001 ETH/session), and privacy guarantees
- Standard request/response handler for marketplace integration
- Health check endpoint for Olas Pearl compatibility

### Olas Mech Marketplace — Hire an Agent (14 Requests Completed)

VaultGuard hires external AI mechs on the **Olas Mech Marketplace** for DeFi analysis. Using `mech-client` (mechx), VaultGuard sends analysis prompts to Base mechs and feeds the results through its privacy-preserving reasoning pipeline.

**Configuration:**
- **Mech:** `0xe535d7acdeed905dddcb5443f41980436833ca2b` (Mech #112, Base)
- **Tool:** `short_maker`
- **Chain:** Base (off-chain delivery via Olas Propel)
- **Wallet:** `0x54eeFbb7b3F701eEFb7fa99473A60A6bf5fE16D7`

**14 requests completed** across diverse DeFi topics:

| # | Topic | Request ID |
|---|-------|------------|
| 1 | DeFi risk analysis | `084090e9...3595d4f8` |
| 2 | ETH staking yield outlook | `d0529063...f9063a9d` |
| 3 | Stablecoin market analysis | `8bc695f5...4c307daa` |
| 4 | Portfolio optimization | `4c931aa1...bc37ffca` |
| 5 | Lido vs Aave yield comparison | `080b3430...0f0b7f44` |
| 6 | Treasury management strategies | `9bc555e8...00f09581` |
| 7 | Agent economy predictions | `64cd0dca...5a578899` |
| 8 | Bitcoin/ETH price analysis | `fe939d3e...1adbaa05` |
| 9 | Smart contract security assessment | `be7a49f4...8e5e6898` |
| 10 | Onchain governance analysis | `71f618d5...b58982fb` |
| 11 | Layer 2 fee optimization | `7475333f...4447c0fb` |
| 12 | Cross-chain bridge risk assessment | `7dceebd3...c5337e` |
| 13 | EIP-4844 impact analysis | `3429cd05...1ad610e` |
| 14 | Liquid restaking protocol comparison | `a265499f...4f4cd749` |

All prompts are stored on IPFS via the Autonolas gateway. Full proof in [`olas_mech_proof.json`](olas_mech_proof.json).

**How VaultGuard uses mech-client:**

1. VaultGuard's private reasoner identifies a DeFi analysis task
2. `OlasMechClient.hire_agent()` sends the prompt to an Olas mech on Base
3. The mech processes the request using its AI tool (`short_maker`)
4. The response is fed back into VaultGuard's privacy pipeline (hashed, never stored raw)
5. Only public-safe outputs are produced — the mech's raw response is discarded after hashing

```bash
# View mech request proof
python3 src/olas_mech_client.py

# Use programmatically
python3 -c "
from src.olas_mech_client import OlasMechClient, get_proof_summary
proof = get_proof_summary()
print(f'Total requests: {proof[\"total_requests\"]}')
print(f'Request IDs: {[r[\"request_id\"][:16] for r in proof[\"requests\"]]}')
"
```

### Commerce Privacy & Slice Hooks (Future of Commerce / Slice)

Private reasoning applied to commerce: confidential pricing analysis, deal negotiation, and margin computation without exposing cost structures.

**VaultGuardSliceHook** is a Slice commerce hook deployed on Base Sepolia that integrates privacy-preserving reasoning proofs with Slice product purchases:

- **Dynamic Pricing (ISliceProductPrice):** Verified agents (with 2+ committed reasoning sessions in PrivacyVault) get a 20% discount. Unverified buyers pay the base price (0.001 ETH/unit).
- **Commerce Proofs (ISliceProductAction):** Every purchase automatically commits a commerce proof to PrivacyVault, linking Slice product purchases to verifiable onchain reasoning sessions.
- **Purchase Gating:** Open by default; subclass to add allowlist/NFT-gated behavior.
- **20 tests passing** covering deployment, dynamic pricing, purchase gating, post-purchase proof commits, admin configuration, and view helpers.

```bash
# Run the commerce privacy demo
python3 src/commerce_privacy.py

# Deploy Slice Hook to Base Sepolia
npx hardhat --config hardhat.config.cjs run scripts/deploy-slice-hook.cjs --network baseSepolia
```

- Analyze supplier quotes privately, output only the final pricing recommendation
- Evaluate deal terms without revealing negotiation strategy
- Compute margins without exposing cost structure to counterparties

### Dark Knowledge Skills -- Lit Protocol (Chipotle TEE)

VaultGuard's "think privately, act publicly" model is implemented as a **real, deployable Lit Action** that runs inside Lit Protocol's Chipotle TEE (Trusted Execution Environment). This is not a concept -- the Lit Action code is written, the IPFS CID is computed, and the Lit SDK integration is wired up.

**Lit Action:** [`vaultguard-private-reasoning.js`](lit-actions/vaultguard-private-reasoning.js)
**IPFS CID:** `QmeZQgyVw74RQXaULgZ4XN4M7eWSmsTq6jMtzq1BZ8uoLJ`
**Lit Network:** datil-dev (Chipotle TEE)
**SDK:** `@lit-protocol/lit-node-client` v7.4.0

**How it works:**

1. Vault data (balances, yield rates, risk scores) is passed as `jsParams` to `litNodeClient.executeJs()`
2. The Lit Action runs inside a Chipotle TEE node -- private data never leaves the enclave
3. Inside the TEE: the action parses vault state, runs decision logic (health check / rebalance / risk assessment), and computes a SHA-256 commitment hash of the full reasoning
4. Only the **public-safe output** exits the TEE: the decision, confidence score, and reasoning hash
5. The raw vault balances and reasoning steps are discarded when the TEE session ends

**Three action types supported:**

| Action Type | Decision Logic | Example Output |
|------------|---------------|----------------|
| `health_check` | Balance > 0, yield > 0, risk < 0.9 | `HEALTHY` (confidence: 85) |
| `rebalance` | Deviation from target allocation exceeds threshold | `REBALANCE` (confidence: 54) |
| `risk_check` | Risk score exceeds configurable threshold | `SAFE` (confidence: 80) |

**Execution patterns:**

```javascript
// Pattern A: Inline code (no IPFS needed)
const result = await litNodeClient.executeJs({
  code: litActionCode,
  jsParams: {
    vaultData: { balance: "10000", yieldRate: "4.5", riskScore: "0.3" },
    threshold: 0.05,
    actionType: "health_check"
  }
});

// Pattern B: IPFS CID (content-addressed, immutable)
const result = await litNodeClient.executeJs({
  ipfsId: "QmeZQgyVw74RQXaULgZ4XN4M7eWSmsTq6jMtzq1BZ8uoLJ",
  jsParams: { ... }
});
```

**Why Lit Protocol maps to VaultGuard's privacy model:**

- VaultGuard's PrivateReasoner hashes inputs and keeps reasoning in-memory only -- Lit's Chipotle TEE enforces this at the hardware level
- VaultGuard's public outputs are summaries + hashes -- the Lit Action's `LitActions.setResponse()` returns only the decision, confidence, and reasoning hash
- VaultGuard's SHA-256 commitment proofs translate directly to the TEE's `crypto.subtle.digest()` inside the enclave
- The IPFS CID makes the Lit Action content-addressed and immutable -- anyone can verify the exact code that ran

```bash
# Run the local simulation (all 3 action types)
node lit-actions/deploy-to-ipfs.cjs

# Run the Lit SDK integration demo (shows executeJs patterns)
node lit-actions/execute-lit-action.cjs

# Verify the IPFS CID independently
node -e "require('ipfs-only-hash').of(require('fs').readFileSync('lit-actions/vaultguard-private-reasoning.js')).then(console.log)"
```

**Proof:** See [`lit_action_proof.json`](lit_action_proof.json) for full execution results across all 3 action types, CID verification, and privacy guarantees.

### CLI Agent (MoonPay CLI MCP Integration)

Full command-line interface for running VaultGuard from the terminal — crypto-native portfolio analysis with private reasoning. The CLI uses `MoonPayMCPBridge` to communicate with the MoonPay CLI (`mp mcp`) over stdio JSON-RPC 2.0, combining live on-chain data with private reasoning.

**MoonPay CLI verified working:**
- **Version:** 1.12.4 (`npm install -g @moonpay/cli`)
- **Binaries:** `mp` and `moonpay` at `/usr/local/bin/`
- **MCP Server:** Responds to JSON-RPC 2.0 `initialize` over stdio
- **Tools:** 92 tools across wallets, tokens, swaps, bridges, commerce, prediction markets, virtual accounts
- **Live API:** Token search, trending, and safety checks return real market data (no auth required)
- **Skills:** 20 AI skills for Claude Code (`mp skill list`)
- **Proof:** See [`moonpay_cli_proof.json`](moonpay_cli_proof.json) for full installation and test results

**Privacy model:** VaultGuard never sends raw sensitive data to MoonPay. MoonPay is used only for public on-chain actions (balances, swaps). Private reasoning stays in the `PrivateReasoner` (hashed, in-memory only).

**Commands:**

| Command | Description |
|---------|-------------|
| `analyze` | Run a private reasoning session (treasury, governance, or deal) |
| `portfolio` | Quick private portfolio analysis from holdings |
| `verify` | Verify a session's cryptographic proof |
| `report` | Print full report of all reasoning sessions |
| `describe` | Show agent capabilities and supported chains |
| `moonpay-status` | Check MoonPay CLI installation and MCP connection |
| `balances` | Fetch live wallet balances via MoonPay CLI |
| `swap` | Execute token swap via MoonPay CLI |
| `portfolio-live` | Fetch live balances via MoonPay, then analyze privately |

```bash
# Quick portfolio analysis
python3 src/cli_agent.py portfolio "40% ETH" "30% BTC" "30% USDC"

# Private treasury analysis
python3 src/cli_agent.py analyze --task treasury_strategy --data "Portfolio: $5M..."

# Governance deliberation from file
python3 src/cli_agent.py analyze --task governance_analysis --file proposal.txt

# Export proof to JSON
python3 src/cli_agent.py analyze --task deal_evaluation --data "Terms..." -o proof.json

# Show capabilities
python3 src/cli_agent.py describe

# Check MoonPay CLI status and MCP connection
python3 src/cli_agent.py moonpay-status

# Fetch live balances via MoonPay CLI
python3 src/cli_agent.py balances --wallet 0x... --chain ethereum

# Live portfolio analysis (MoonPay + private reasoning)
python3 src/cli_agent.py portfolio-live --wallet 0x... --chains ethereum,base,polygon
```

### Status Network — Gasless L2 Deployment

VaultGuard is deployed on Status Network Sepolia with zero gas fees, enabling free private reasoning session commits.

- **Contract:** [`0x51C96F24A3D6aDc6B5bE391b778a847CCFc78Ba3`](https://sepoliascan.status.network/address/0x51C96F24A3D6aDc6B5bE391b778a847CCFc78Ba3)
- **Zero gas fees** make it ideal for high-frequency privacy proof commits
- **Explorer:** [sepoliascan.status.network](https://sepoliascan.status.network)

### OpenWallet Standard (OWS) — Agent Wallet Infrastructure

VaultGuard uses [`@open-wallet-standard/core`](https://www.npmjs.com/package/@open-wallet-standard/core) **v0.3.9** by **MoonPay Engineering** as its wallet infrastructure layer. OWS provides local-first, chain-agnostic wallet management through 14 native NAPI-RS functions -- the agent's private keys are encrypted at rest inside the OWS vault and never exposed to LLM context.

**What OWS provides:**

| Capability | OWS Function | VaultGuard Usage |
|-----------|-------------|-----------------|
| Mnemonic generation | `generateMnemonic` | BIP-39 seed for agent wallet |
| Universal wallet | `createWallet` | 7-chain address derivation from single seed |
| Multi-chain addresses | `deriveAddress` | EVM, Solana, Bitcoin, Cosmos, Tron, TON, Filecoin + 6 EVM L2s |
| Reasoning proof signing | `signMessage` | Sign SHA-256 proof hashes on EVM, Solana, and Cosmos |
| Governance attestation | `signTypedData` | EIP-712 structured data for onchain attestations |
| Wallet lifecycle | `listWallets`, `getWallet`, `renameWallet` | Vault management |
| Key portability | `exportWallet`, `importWalletMnemonic` | Backup and restore with address continuity verified |
| Cleanup | `deleteWallet` | Secure vault cleanup |

**Chain coverage (13 networks):**

| Chain Family | Chain ID (CAIP-2) | Derivation Path |
|-------------|-------------------|-----------------|
| Ethereum / EVM | `eip155:1` | `m/44'/60'/0'/0/0` |
| Solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | `m/44'/501'/0'/0'` |
| Bitcoin | `bip122:000000000019d6689c085ae165831e93` | `m/84'/0'/0'/0/0` |
| Cosmos Hub | `cosmos:cosmoshub-4` | `m/44'/118'/0'/0/0` |
| Tron | `tron:mainnet` | `m/44'/195'/0'/0/0` |
| TON | `ton:mainnet` | `m/44'/607'/0'` |
| Filecoin | `fil:mainnet` | `m/44'/461'/0'/0/0` |
| Base, Arbitrum, Optimism, Polygon, Avalanche, BSC | Same EVM key | `m/44'/60'/0'/0/0` |

**Security model:**
- Agent keys encrypted at rest in OWS vault (AES-256)
- Key material stays inside NAPI-RS native boundary -- never serialized to JS heap
- Mnemonic never passed to LLM context or logged
- Signing happens through OWS `signMessage` / `signTypedData` -- agent code never touches raw private keys

**How VaultGuard uses OWS for reasoning proofs:**
1. Private reasoning produces `input_hash` and `output_hash` (SHA-256)
2. Proof payload: `vaultguard:reasoning:<input_hash>:<output_hash>`
3. OWS `signMessage` signs the proof hash on EVM, Solana, and Cosmos
4. OWS `signTypedData` creates EIP-712 `VaultGuardAttestation` for onchain verification
5. Signatures prove the agent endorsed the reasoning output without exposing the input

```bash
# Run the OWS wallet integration demo
node src/ows_wallet.cjs --test
```

**Proof:** See [`ows_proof.json`](ows_proof.json) for the full execution trace with real wallet creation, multi-chain derivation, 5 cryptographic signatures, and key continuity verification.

### ENS Communication

VaultGuard integrates real Ethereum Name Service (ENS) resolution for human-readable agent-to-agent communication. Instead of passing raw hex addresses through private reasoning sessions, VaultGuard resolves ENS names on Ethereum mainnet using direct JSON-RPC calls to the ENS Registry contract -- no web3.py dependency required.

**What it does:**

1. **Resolves ENS names to addresses before processing transactions** -- When input contains `vitalik.eth`, VaultGuard resolves it to `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` via live mainnet RPC before feeding data into the private reasoning engine
2. **Uses ENS names in agent-to-agent communication** -- `ENSAgentRegistry` provides full identity resolution with forward + reverse verification, so agents can authenticate each other by ENS name
3. **Displays ENS names instead of raw hex addresses in outputs** -- `enrich_with_ens()` replaces hex addresses in output text with human-readable names like `vitalik.eth (0xd8dA...6045)`

**How it works (on-chain):**

- ENS Registry at `0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e` -- queries resolver address for a namehash
- Public Resolver (varies per name) -- queries the `addr()` record for forward resolution
- Reverse Registrar -- queries `name()` on the reverse node for address-to-name lookup
- All calls are raw `eth_call` JSON-RPC to free Ethereum mainnet RPC endpoints (no API keys needed)
- Pure-Python Keccak-256 + EIP-137 namehash implementation -- zero external crypto dependencies

```bash
# Run the ENS resolver demo (live mainnet resolution)
python3 src/ens_resolver.py

# Run private reasoning with ENS integration
python3 src/private_reasoner.py
```

**Proof of real ENS resolution (from `ens_proof.json`):**

| Resolution | Input | Result | Status |
|-----------|-------|--------|--------|
| Forward | `vitalik.eth` | `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` | Resolved |
| Forward | `nick.eth` | `0xb8c2C29ee19D8307cb7255e1Cd9CbDE883A267d5` | Resolved |
| Reverse | `0xd8dA6BF2...96045` | `vitalik.eth` | Resolved |
| Batch | `nonexistent12345.eth` | `null` | Not found |

All resolutions are live Ethereum mainnet RPC calls, not hardcoded values. See [`ens_proof.json`](ens_proof.json) for the full proof with timestamps.

## Agent Identity Files

- **`agent.json`** — Machine-readable agent descriptor with name, version, privacy model, supported tools, tech stack, smart contract addresses, and links. Enables programmatic agent discovery.
- **`agent_log.json`** — Complete activity log recording all private reasoning sessions, onchain commits, and verification results.

## How to Run

```bash
git clone https://github.com/devanshug2307/vaultguard-agent.git
cd vaultguard-agent

pip install httpx

# Run the core demo (4 private reasoning scenarios, including ENS)
python3 src/private_reasoner.py

# Run ENS resolver demo (live mainnet resolution)
python3 src/ens_resolver.py

# Run integrations
python3 src/olas_service.py          # Olas marketplace service
python3 src/commerce_privacy.py      # Commerce privacy engine
node src/ows_wallet.cjs --test       # OWS wallet integration (generates ows_proof.json)
python3 src/cli_agent.py describe    # CLI agent capabilities
```

## Project Structure

```
vaultguard-agent/
├── contracts/
│   ├── PrivacyVault.sol              # Onchain computation proof vault
│   ├── ISliceProductPrice.sol        # Slice pricing hook interface
│   ├── ISliceProductAction.sol       # Slice action hook interface
│   └── VaultGuardSliceHook.sol       # Slice commerce hook (dynamic pricing + commerce proofs)
├── scripts/
│   ├── deploy.cjs                    # Deploy + commit 3 sessions onchain
│   └── deploy-slice-hook.cjs         # Deploy Slice Hook to Base Sepolia
├── src/
│   ├── private_reasoner.py           # Core privacy-preserving reasoning engine (+ ENS integration)
│   ├── ens_resolver.py               # Real ENS name resolution (mainnet RPC, no web3.py)
│   ├── olas_service.py               # Olas Pearl-compatible service component
│   ├── olas_service_descriptor.json  # Olas service descriptor (capabilities, pricing)
│   ├── commerce_privacy.py           # Commerce privacy engine (Slice/Future of Commerce)
│   ├── cli_agent.py                  # CLI agent with MoonPayMCPBridge (MoonPay CLI MCP)
│   ├── olas_mech_client.py           # Olas Mech Marketplace client (hire AI mechs for DeFi analysis)
│   └── ows_wallet.cjs               # OpenWallet Standard integration (7-chain wallet, signing)
├── test/
│   ├── PrivacyVault.test.cjs         # 13 tests
│   └── VaultGuardSliceHook.test.cjs  # 20 tests (pricing, gating, proofs, admin)
├── lit-actions/
│   ├── vaultguard-private-reasoning.js  # Lit Action: private vault reasoning in Chipotle TEE
│   ├── deploy-to-ipfs.cjs              # IPFS CID computation + local simulation
│   ├── execute-lit-action.cjs           # Lit SDK executeJs() integration demo
│   └── deployment-record.json           # Deployment metadata (CID, network, SDK version)
├── docs/
│   ├── index.html                    # Live dashboard
│   └── MOONPAY_CLI_SETUP.md          # MoonPay CLI setup guide
├── agent.json                        # Agent identity + capabilities descriptor
├── agent_log.json                    # Full agent activity log
├── privacy_proof.json                # Proof of private computation
├── ens_proof.json                    # Proof of real ENS resolution (mainnet RPC)
├── moonpay_cli_proof.json            # Proof of MoonPay CLI v1.12.4 install + 92 tools verified
├── ows_proof.json                    # Proof of OWS wallet ops (7 chains, 5 signatures, key continuity)
├── slice_hook_deploy_proof.json      # Proof of Slice Hook deployment on Base Sepolia
├── olas_mech_proof.json              # Proof of 14 Olas mech requests (Hire an Agent track)
├── lit_action_proof.json             # Proof of Lit Action execution (3 action types, CID verified)
├── hardhat.config.cjs
├── README.md
└── requirements.txt
```

### Markee GitHub Integration

VaultGuard is integrated with [Markee](https://markee.xyz) — open source digital real estate that funds the open internet. Markee enables sustainable funding for open source projects by embedding sponsored messages directly in repository markdown files.

**How it works:**
1. A Markee "sign" is deployed onchain, linked to this GitHub repo via OAuth
2. The delimiter tags below define where the Markee message appears
3. Supporters and sponsors can purchase message space, with funds split between the project (62%) and the Markee Cooperative (38%)
4. Judging is fully objective: based on views and monetization metrics

**Setup (manual steps required):**
1. Go to [markee.xyz](https://markee.xyz) and connect your GitHub account
2. Grant OAuth permissions to the `vaultguard-agent` repository
3. Create a Markee sign and select your pricing strategy
4. Copy the generated delimiter tags (with your unique Ethereum address) and replace the placeholder below
5. Verify the repo appears as "Live" on [markee.xyz/ecosystem/platforms/github](https://markee.xyz/ecosystem/platforms/github)

<!-- MARKEE:START -->
> **Sponsored by [Markee](https://markee.xyz)** — Fund open source projects by purchasing this message space. VaultGuard: Private AI reasoning with public verifiable actions.
>
> [Purchase this message on the Markee App](https://markee.xyz)
<!-- MARKEE:END -->

## Links

- **Dashboard:** [devanshug2307.github.io/vaultguard-agent](https://devanshug2307.github.io/vaultguard-agent/)
- **GitHub:** [github.com/devanshug2307/vaultguard-agent](https://github.com/devanshug2307/vaultguard-agent)
- **Markee:** [markee.xyz/ecosystem/platforms/github](https://markee.xyz/ecosystem/platforms/github)

## Built By

- **Human:** Devanshu Goyal ([@devanshugoyal23](https://x.com/devanshugoyal23))
- **Hackathon:** [The Synthesis](https://synthesis.md) — March 2026

## License

MIT
