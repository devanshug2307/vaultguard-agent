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

## Deployed Contract

| Contract | Network | Address |
|----------|---------|---------|
| PrivacyVault | Base Sepolia | [`0xE3321EFC6E1A8B27D2c9d261504b974E927Df4C2`](https://sepolia.basescan.org/address/0xE3321EFC6E1A8B27D2c9d261504b974E927Df4C2) |

## Onchain Proof

Every private reasoning session is committed onchain with hashes (never raw data):

| # | Action | TX Hash |
|---|--------|---------|
| 1 | Deploy PrivacyVault | [`0xe46c6f...`](https://sepolia.basescan.org/tx/0xe46c6f664111b27eaaf89cbf5cf426d18fded233f78316358a900e4d52cc596f) |
| 2 | Treasury Strategy (private reasoning) | [`0xd7dae8...`](https://sepolia.basescan.org/tx/0xd7dae894626d517cdac4283ccddba3e0d015cdd143d9389f7ad1829f5d90179c) |
| 3 | Governance Deliberation (private reasoning) | [`0xe42552...`](https://sepolia.basescan.org/tx/0xe4255220393431de69d1fb61a5d96d43b10d82692a115d3a46f501aa963d2225) |
| 4 | Deal Evaluation (private reasoning) | [`0xaa83b5...`](https://sepolia.basescan.org/tx/0xaa83b508c19a14bc8592390a4a4a7545e8bcc2e2738e16e438a2c5cf97ecff4b) |

## Tests

**13/13 passing** — run with:
```bash
npx hardhat --config hardhat.config.cjs test
```

## How to Run

```bash
git clone https://github.com/devanshug2307/vaultguard-agent.git
cd vaultguard-agent

pip install httpx

# Run the demo (3 private reasoning scenarios)
python3 src/private_reasoner.py
```

## Project Structure

```
vaultguard-agent/
├── contracts/
│   └── PrivacyVault.sol       # Onchain computation proof vault
├── scripts/
│   └── deploy.cjs             # Deploy + commit 3 sessions onchain
├── src/
│   └── private_reasoner.py    # Core privacy-preserving reasoning engine
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
