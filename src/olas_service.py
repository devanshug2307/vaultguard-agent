"""
VaultGuard — Olas Autonomous Service Component
================================================
Defines VaultGuard as an Olas-compatible autonomous service that can be
discovered, hired, and invoked through the Olas marketplace.

Service type: Private AI Reasoning Agent
Capabilities: treasury analysis, governance deliberation, deal evaluation
Pricing: per-session, paid in ETH on Base

Olas Pearl compatibility:
  - Implements the standard request/response handler
  - Publishes a service descriptor with capabilities and pricing
  - Supports health checks and capability queries
"""

import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict

from private_reasoner import PrivateReasoner, PrivateReasoning


# ---------------------------------------------------------------------------
# Service descriptor (Olas marketplace metadata)
# ---------------------------------------------------------------------------

SERVICE_DESCRIPTOR = {
    "name": "VaultGuard",
    "description": (
        "Privacy-preserving AI reasoning agent. Analyzes sensitive treasury, "
        "governance, and deal data privately and produces public-safe outputs "
        "with cryptographic proof of computation."
    ),
    "version": "1.0.0",
    "author": "devanshu",
    "homepage": "https://github.com/devanshug2307/vaultguard-agent",
    "service_type": "ai_reasoning",
    "capabilities": [
        {
            "id": "treasury_strategy",
            "name": "Private Treasury Analysis",
            "description": "Analyze portfolio composition and recommend rebalancing — privately.",
            "input_schema": {"type": "object", "properties": {"portfolio_data": {"type": "string"}}},
            "output": "Public-safe actions + SHA-256 proof",
        },
        {
            "id": "governance_analysis",
            "name": "Private Governance Deliberation",
            "description": "Evaluate governance proposals privately, output only the vote.",
            "input_schema": {"type": "object", "properties": {"proposal_data": {"type": "string"}}},
            "output": "Vote recommendation + proof",
        },
        {
            "id": "deal_evaluation",
            "name": "Private Deal Evaluation",
            "description": "Evaluate term sheets privately, recommend public terms.",
            "input_schema": {"type": "object", "properties": {"deal_data": {"type": "string"}}},
            "output": "Term recommendation + proof",
        },
    ],
    "pricing": {
        "model": "per_session",
        "base_price_wei": 1000000000000000,   # 0.001 ETH
        "currency": "ETH",
        "chain": "base",
    },
    "privacy_guarantees": [
        "Input data is SHA-256 hashed — never stored in plaintext",
        "Reasoning is in-memory only — never persisted",
        "Venice API zero-storage inference when available",
        "Hash-based cryptographic proof of computation",
    ],
}


# ---------------------------------------------------------------------------
# Olas service component
# ---------------------------------------------------------------------------

@dataclass
class ServiceRequest:
    """Incoming request from the Olas marketplace."""
    request_id: str
    sender: str             # Olas agent address
    capability: str         # one of the capability IDs
    payload: str            # sensitive data (handled privately)
    max_price_wei: int = 1000000000000000


@dataclass
class ServiceResponse:
    """Response returned to the Olas marketplace."""
    request_id: str
    session_id: str
    status: str             # "completed" | "rejected" | "error"
    public_summary: str
    public_actions: list
    input_hash: str
    reasoning_hash: str
    price_charged_wei: int
    timestamp: str


class OlasVaultGuardService:
    """
    Olas-compatible autonomous service wrapper around PrivateReasoner.

    Lifecycle:
      1. Marketplace queries ``get_descriptor()`` to display the service.
      2. Requester sends a ``ServiceRequest``.
      3. ``handle_request()`` runs private reasoning and returns a
         ``ServiceResponse`` with public-safe outputs and proof.
    """

    def __init__(self, venice_api_key: str = ""):
        self.reasoner = PrivateReasoner(venice_api_key)
        self.completed_requests: list[ServiceResponse] = []
        self.revenue_wei: int = 0

    # -- Discovery ----------------------------------------------------------

    @staticmethod
    def get_descriptor() -> dict:
        """Return the service descriptor for the Olas marketplace."""
        return SERVICE_DESCRIPTOR

    def health_check(self) -> dict:
        """Standard Olas health-check endpoint."""
        return {
            "service": "VaultGuard",
            "status": "healthy",
            "uptime_sessions": self.reasoner.total_sessions,
            "total_revenue_wei": self.revenue_wei,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # -- Request handling ---------------------------------------------------

    def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        Process an incoming Olas marketplace request.

        1. Validate capability and pricing.
        2. Run private reasoning.
        3. Return public-safe response with proof.
        """
        # Validate capability
        valid_caps = {c["id"] for c in SERVICE_DESCRIPTOR["capabilities"]}
        if request.capability not in valid_caps:
            return ServiceResponse(
                request_id=request.request_id,
                session_id="",
                status="rejected",
                public_summary=f"Unknown capability: {request.capability}",
                public_actions=[],
                input_hash="",
                reasoning_hash="",
                price_charged_wei=0,
                timestamp=datetime.utcnow().isoformat(),
            )

        # Check pricing
        base = SERVICE_DESCRIPTOR["pricing"]["base_price_wei"]
        if request.max_price_wei < base:
            return ServiceResponse(
                request_id=request.request_id,
                session_id="",
                status="rejected",
                public_summary=f"Price too low (min {base} wei)",
                public_actions=[],
                input_hash="",
                reasoning_hash="",
                price_charged_wei=0,
                timestamp=datetime.utcnow().isoformat(),
            )

        # Run private reasoning
        session = self.reasoner.reason_privately(
            sensitive_input=request.payload,
            task=request.capability,
        )

        self.revenue_wei += base

        response = ServiceResponse(
            request_id=request.request_id,
            session_id=session.session_id,
            status="completed",
            public_summary=session.output_summary,
            public_actions=session.output_actions,
            input_hash=session.input_hash,
            reasoning_hash=session.reasoning_hash,
            price_charged_wei=base,
            timestamp=session.timestamp,
        )
        self.completed_requests.append(response)
        return response


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

def demo():
    print("=== VaultGuard Olas Service Demo ===\n")

    service = OlasVaultGuardService()

    # Show marketplace descriptor
    desc = service.get_descriptor()
    print(f"Service: {desc['name']} v{desc['version']}")
    print(f"Capabilities: {[c['id'] for c in desc['capabilities']]}")
    print(f"Price: {desc['pricing']['base_price_wei']} wei per session")
    print(f"Privacy: {desc['privacy_guarantees'][0]}")
    print()

    # Simulate a hire request
    req = ServiceRequest(
        request_id="olas-req-001",
        sender="0xAgentAlice",
        capability="treasury_strategy",
        payload="Portfolio: 50% ETH, 30% stETH, 20% USDC. Total $2M.",
    )
    print(f"Incoming request from {req.sender}: {req.capability}")
    resp = service.handle_request(req)
    print(f"  Status: {resp.status}")
    print(f"  Session: {resp.session_id}")
    print(f"  Actions: {resp.public_actions}")
    print(f"  Input hash: {resp.input_hash[:32]}...")
    print(f"  Price charged: {resp.price_charged_wei} wei")
    print()

    # Simulate a second request
    req2 = ServiceRequest(
        request_id="olas-req-002",
        sender="0xAgentBob",
        capability="governance_analysis",
        payload="Proposal #12: Increase emissions 5%. Quorum 60%. Impact $500K/yr.",
    )
    print(f"Incoming request from {req2.sender}: {req2.capability}")
    resp2 = service.handle_request(req2)
    print(f"  Status: {resp2.status}")
    print(f"  Actions: {resp2.public_actions}")
    print()

    # Health check
    health = service.health_check()
    print(f"Health: {health['status']}, sessions={health['uptime_sessions']}, "
          f"revenue={health['total_revenue_wei']} wei")

    # Dump descriptor to JSON (useful for Olas registration)
    with open("olas_service_descriptor.json", "w") as f:
        json.dump(desc, f, indent=2)
    print("\nService descriptor saved to olas_service_descriptor.json")


if __name__ == "__main__":
    demo()
