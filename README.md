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
- **Privacy:** Venice stores nothing — no logs, no training data, no traces
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

## Deployed Contract (Base Sepolia)

| Contract | Network | Address |
|----------|---------|---------|
| PrivacyVault | Base Sepolia | [`0x3AeDD41999383E9a351B0Cb984D5Bb8eac3AAB28`](https://sepolia.basescan.org/address/0x3AeDD41999383E9a351B0Cb984D5Bb8eac3AAB28) |

## Onchain Proof

Every private reasoning session is committed onchain with hashes (never raw data):

| # | Action | TX Hash |
|---|--------|---------|
| 1 | Deploy PrivacyVault | [`0xee4682...`](https://sepolia.basescan.org/tx/0xee46829d529cb951926004d27db53976bee4185e211aca218f8e3cf53eb77d23) |
| 2 | Treasury Strategy (private reasoning) | [`0x7c4ece...`](https://sepolia.basescan.org/tx/0x7c4ece9c262798a03bace90a41a237ba7827d912515210e14d6db596aabc0896) |
| 3 | Governance Deliberation (private reasoning) | [`0x91b5d2...`](https://sepolia.basescan.org/tx/0x91b5d2b5bb6e0164b1c0c8fcba8f2c28bc39041d6511269447e990cf4ffa5c76) |
| 4 | Deal Evaluation (private reasoning) | [`0x8455a8...`](https://sepolia.basescan.org/tx/0x8455a8616f543d0ef0dd77ee751d24ae2fd32f44b53616ecdb006fa9f546f242) |

## Tests

**13/13 passing** — run with:
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

### Commerce Privacy (Future of Commerce / Slice)

Private reasoning applied to commerce: confidential pricing analysis, deal negotiation, and margin computation without exposing cost structures.

```bash
# Run the commerce privacy demo
python3 src/commerce_privacy.py
```

- Analyze supplier quotes privately, output only the final pricing recommendation
- Evaluate deal terms without revealing negotiation strategy
- Compute margins without exposing cost structure to counterparties

### CLI Agent (MoonPay CLI)

Full command-line interface for running VaultGuard from the terminal — crypto-native portfolio analysis with private reasoning.

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
```

## How to Run

```bash
git clone https://github.com/devanshug2307/vaultguard-agent.git
cd vaultguard-agent

pip install httpx

# Run the core demo (3 private reasoning scenarios)
python3 src/private_reasoner.py

# Run integrations
python3 src/olas_service.py          # Olas marketplace service
python3 src/commerce_privacy.py      # Commerce privacy engine
python3 src/cli_agent.py describe    # CLI agent capabilities
```

## Project Structure

```
vaultguard-agent/
├── contracts/
│   └── PrivacyVault.sol       # Onchain computation proof vault
├── scripts/
│   └── deploy.cjs             # Deploy + commit 3 sessions onchain
├── src/
│   ├── private_reasoner.py    # Core privacy-preserving reasoning engine
│   ├── olas_service.py        # Olas Pearl-compatible service component
│   ├── commerce_privacy.py    # Commerce privacy engine (Slice/Future of Commerce)
│   └── cli_agent.py           # CLI agent for crypto operations (MoonPay CLI)
├── test/
│   └── PrivacyVault.test.cjs  # 13 tests
├── docs/
│   └── index.html             # Live dashboard
├── privacy_proof.json         # Proof of private computation
├── hardhat.config.cjs
├── README.md
└── requirements.txt
```

## Links

- **Dashboard:** [devanshug2307.github.io/vaultguard-agent](https://devanshug2307.github.io/vaultguard-agent/)
- **GitHub:** [github.com/devanshug2307/vaultguard-agent](https://github.com/devanshug2307/vaultguard-agent)

## Built By

- **Human:** Devanshu Goyal ([@devanshugoyal23](https://x.com/devanshugoyal23))
- **Hackathon:** [The Synthesis](https://synthesis.md) — March 2026

## License

MIT
