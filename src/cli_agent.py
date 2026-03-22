#!/usr/bin/env python3
"""
VaultGuard CLI Agent
=====================
Command-line interface for running VaultGuard private reasoning sessions.

Supports:
  - Private portfolio / treasury analysis
  - Governance proposal deliberation
  - Deal evaluation
  - Session verification and proof export

Designed for the MoonPay CLI track — a crypto-native CLI agent that performs
private analysis of portfolios and outputs public-safe recommendations.

Usage:
    python cli_agent.py analyze --task treasury_strategy --data "Portfolio: ..."
    python cli_agent.py analyze --task governance_analysis --file proposal.txt
    python cli_agent.py verify  --session-id vg-0001-185954
    python cli_agent.py report
    python cli_agent.py describe
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from datetime import datetime
from typing import Optional

# Allow running from the src/ directory or project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from private_reasoner import PrivateReasoner, PrivateReasoning


# ---------------------------------------------------------------------------
# Shared reasoner instance (persists across commands in interactive mode)
# ---------------------------------------------------------------------------

_reasoner: Optional[PrivateReasoner] = None


def get_reasoner(api_key: str = "") -> PrivateReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = PrivateReasoner(api_key)
    return _reasoner


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
    print("""
  VaultGuard CLI Agent
  ====================
  Privacy-preserving AI reasoning for crypto portfolios and DAO operations.

  Capabilities:
    treasury_strategy    Analyze portfolio composition, recommend rebalancing
    governance_analysis  Evaluate governance proposals, output vote
    deal_evaluation      Assess deal terms, recommend negotiation position

  Privacy model:
    - Input data: SHA-256 hashed, never stored
    - Reasoning: in-memory only, never persisted
    - Output: public-safe summaries and actions only
    - Proof: cryptographic hashes prove computation

  Crypto operations:
    - Portfolio analysis with private reasoning
    - DAO treasury management
    - Confidential deal evaluation

  Run 'vaultguard analyze --help' for usage details.
""")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vaultguard",
        description="VaultGuard — Private AI reasoning agent for crypto operations",
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

    # portfolio (shortcut)
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
