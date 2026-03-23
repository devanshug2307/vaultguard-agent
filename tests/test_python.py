"""
Python-side tests for VaultGuard: Private Reasoner, ENS Resolver, and
Commerce Privacy Engine.

All tests are pure-logic — no API keys, no network access, no blockchain calls.

Run:
    cd project3-vaultguard && python3 -m pytest tests/ -v
"""

import hashlib
import sys
import os

# Source files live in src/ and import each other without a package prefix,
# so we add src/ to sys.path.
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))

from private_reasoner import PrivateReasoner, PrivateReasoning  # noqa: E402
from ens_resolver import (                                       # noqa: E402
    namehash,
    _keccak256,
    _compute_verification_level,
    _encode_bytes32,
    _decode_address,
    _decode_string,
)
from commerce_privacy import (                                   # noqa: E402
    CommercePrivacyEngine,
    PricingRequest,
    DealAnalysis,
)


# ========================================================================
# 1.  Private Reasoner tests
# ========================================================================

class TestPrivateReasonerHashing:
    """SHA-256 hashing of inputs must be deterministic."""

    def test_hash_deterministic(self):
        r = PrivateReasoner()
        data = "secret treasury data"
        assert r._hash_data(data) == r._hash_data(data)

    def test_hash_matches_stdlib(self):
        r = PrivateReasoner()
        data = "portfolio: 40% ETH"
        expected = hashlib.sha256(data.encode()).hexdigest()
        assert r._hash_data(data) == expected

    def test_hash_differs_for_different_inputs(self):
        r = PrivateReasoner()
        assert r._hash_data("input A") != r._hash_data("input B")


class TestExtractPublicOutputs:
    """_extract_public_outputs with structured and unstructured text."""

    def test_structured_summary_and_actions(self):
        """Structured text with SUMMARY: and ACTIONS: markers."""
        r = PrivateReasoner()
        text = (
            "SUMMARY: Rebalance portfolio toward yield.\n"
            "ACTIONS:\n"
            "- Sell 10% volatile\n"
            "- Buy stETH\n"
            "RISK_LEVEL: MEDIUM"
        )
        summary, actions = r._extract_public_outputs(text, "treasury_strategy")
        assert "Rebalance" in summary
        assert len(actions) == 2
        assert "Sell 10% volatile" in actions[0]

    def test_structured_with_recommendation_fallback(self):
        """If SUMMARY is missing but RECOMMENDATION is present, use it."""
        r = PrivateReasoner()
        text = (
            "RECOMMENDATION: Vote yes on proposal 47.\n"
            "ACTIONS:\n"
            "1. Cast vote\n"
            "RISK_LEVEL: LOW"
        )
        summary, actions = r._extract_public_outputs(text, "governance_analysis")
        assert "Vote yes" in summary
        assert len(actions) >= 1

    def test_unstructured_fallback_treasury(self):
        """Local-simulation text (no markers) uses hardcoded actions."""
        r = PrivateReasoner()
        plain = "Some analysis without structured markers at all."
        summary, actions = r._extract_public_outputs(plain, "treasury_strategy")
        # Hardcoded fallback actions for treasury_strategy
        assert "Reduce volatile exposure by 15%" in actions
        assert len(actions) == 4

    def test_unstructured_fallback_unknown_task(self):
        """Unknown task falls back to generic actions."""
        r = PrivateReasoner()
        summary, actions = r._extract_public_outputs("no markers", "unknown_task")
        assert "Continue monitoring" in actions


class TestLocalReasoning:
    """_local_reasoning returns dynamic, task-dependent output."""

    def test_different_tasks_different_output(self):
        r = PrivateReasoner()
        out1 = r._local_reasoning("treasury_strategy", "data")
        out2 = r._local_reasoning("governance_analysis", "data")
        assert out1 != out2

    def test_different_data_different_hash_prefix(self):
        """The embedded data_hash prefix changes with input data."""
        r = PrivateReasoner()
        out1 = r._local_reasoning("treasury_strategy", "data A")
        out2 = r._local_reasoning("treasury_strategy", "data B")
        # Both contain [local-analysis ...] with different ref= values
        assert "ref=" in out1
        assert "ref=" in out2
        assert out1 != out2


class TestPrivacyGuarantee:
    """Public outputs must NOT contain the raw sensitive input."""

    def test_raw_input_not_in_summary(self):
        r = PrivateReasoner()
        secret = "Our runway is $42M and our burn rate is $1.2M/month"
        session = r.reason_privately(secret, "treasury_strategy")
        assert secret not in session.output_summary
        for action in session.output_actions:
            assert secret not in action

    def test_raw_input_not_in_reasoning_hash(self):
        r = PrivateReasoner()
        secret = "Acquisition target valued at $15M"
        session = r.reason_privately(secret, "deal_evaluation")
        # The reasoning hash is a hex digest, not the input itself
        assert secret not in session.reasoning_hash


# ========================================================================
# 2.  ENS Resolver tests (pure-logic, no network)
# ========================================================================

class TestNamehash:
    """EIP-137 namehash computation using known test vectors."""

    def test_empty_name(self):
        """namehash('') = 32 zero bytes."""
        assert namehash("") == b"\x00" * 32

    def test_eth_tld(self):
        """namehash('eth') must match the well-known EIP-137 value."""
        result = namehash("eth")
        expected_hex = (
            "93cdeb708b7545dc668eb9280176169d1c33cfd8ed6f04690a0bcc88a93fc4ae"
        )
        assert result.hex() == expected_hex

    def test_vitalik_eth(self):
        """namehash('vitalik.eth') — verifiable on-chain."""
        result = namehash("vitalik.eth")
        # Known namehash from ENS docs / ethers.js utils.namehash
        expected_hex = (
            "ee6c4522aab0003e8d14cd40a6af439055fd2577951148c14b6cea9a53475835"
        )
        assert result.hex() == expected_hex

    def test_deterministic(self):
        """Same name always produces same hash."""
        assert namehash("test.eth") == namehash("test.eth")

    def test_different_names(self):
        assert namehash("alice.eth") != namehash("bob.eth")


class TestKeccak256:
    """_keccak256 must produce correct Keccak-256 hashes."""

    def test_empty_bytes(self):
        """keccak256('') is a well-known constant."""
        result = _keccak256(b"")
        expected = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        assert result.hex() == expected

    def test_hello(self):
        """keccak256('hello') — matches ethers.js / web3.py output."""
        result = _keccak256(b"hello")
        expected = "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"
        assert result.hex() == expected


class TestComputeVerificationLevel:
    """_compute_verification_level produces the correct tier string."""

    def test_full_verification(self):
        identity = {"resolved_address": "0x1234", "reverse_verified": True}
        assert _compute_verification_level(identity, True) == "full"

    def test_forward_only(self):
        identity = {"resolved_address": "0x1234", "reverse_verified": False}
        assert _compute_verification_level(identity, True) == "forward"

    def test_partial(self):
        identity = {"resolved_address": "0x1234", "reverse_verified": False}
        assert _compute_verification_level(identity, False) == "partial"

    def test_none(self):
        identity = {"resolved_address": None, "reverse_verified": False}
        assert _compute_verification_level(identity, False) == "none"


# ========================================================================
# 3.  Commerce Privacy Engine tests
# ========================================================================

class TestDeriveRecommendation:
    """_derive_recommendation: margin >= 30% -> 'counter', else 'accept'."""

    def test_high_margin_returns_counter(self):
        engine = CommercePrivacyEngine()
        req = PricingRequest(
            product_id="X",
            supplier_quotes=[],
            target_margin_pct=35.0,
            market_context="",
        )
        assert engine._derive_recommendation(req) == "counter"

    def test_low_margin_returns_accept(self):
        engine = CommercePrivacyEngine()
        req = PricingRequest(
            product_id="X",
            supplier_quotes=[],
            target_margin_pct=20.0,
            market_context="",
        )
        assert engine._derive_recommendation(req) == "accept"

    def test_boundary_30_returns_counter(self):
        engine = CommercePrivacyEngine()
        req = PricingRequest(
            product_id="X",
            supplier_quotes=[],
            target_margin_pct=30.0,
            market_context="",
        )
        assert engine._derive_recommendation(req) == "counter"


class TestCommerceAnalyzePricing:
    """analyze_pricing returns a well-formed DealAnalysis without network."""

    def test_returns_deal_analysis(self):
        engine = CommercePrivacyEngine()
        result = engine.analyze_pricing(PricingRequest(
            product_id="WIDGET-7",
            supplier_quotes=[
                {"supplier": "A", "unit_price": 10, "volume": 100, "terms": "net-30"},
            ],
            target_margin_pct=25.0,
            market_context="stable",
        ))
        assert isinstance(result, DealAnalysis)
        assert result.recommendation == "accept"   # 25 < 30
        assert len(result.input_hash) == 64         # SHA-256 hex
        assert len(result.reasoning_hash) == 64
        assert len(result.suggested_actions) >= 1
        assert result.risk_level in ("LOW", "MEDIUM", "HIGH")

    def test_sensitive_data_not_in_output(self):
        """Supplier quotes must not leak into public rationale or actions."""
        engine = CommercePrivacyEngine()
        secret_supplier = "SuperSecretSupplierCorp"
        result = engine.analyze_pricing(PricingRequest(
            product_id="WIDGET-SEC",
            supplier_quotes=[
                {"supplier": secret_supplier, "unit_price": 99.99,
                 "volume": 500, "terms": "net-15"},
            ],
            target_margin_pct=20.0,
            market_context="niche market",
        ))
        assert secret_supplier not in result.public_rationale
        for action in result.suggested_actions:
            assert secret_supplier not in action
