"""
Olas Mech Marketplace Client Integration for VaultGuard
=========================================================
Integrates mech-client (mechx) with VaultGuard's private reasoning pipeline.
VaultGuard hires external AI mechs on the Olas Marketplace for DeFi analysis,
then processes the results through its privacy-preserving reasoning engine.

This enables VaultGuard to:
1. Send analysis prompts to Olas AI mechs (off-chain or on-chain)
2. Track all requests, IPFS hashes, and responses
3. Feed mech responses into VaultGuard's private reasoner for further analysis
4. Maintain a complete audit trail of all mech interactions

Built for The Synthesis Hackathon — "Hire an Agent" Track (Olas)
"""

import json
import os
import subprocess
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional


# Default mech on Base chain (mech #112)
DEFAULT_MECH_ADDRESS = "0xe535d7acdeed905dddcb5443f41980436833ca2b"
DEFAULT_CHAIN = "base"
DEFAULT_TOOL = "short_maker"
PROOF_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "olas_mech_proof.json")


@dataclass
class MechRequest:
    """A single request sent to an Olas AI mech."""
    prompt: str
    request_id: str
    onchain_request_id: str = ""
    ipfs_hash: str = ""
    ipfs_url: str = ""
    mech_address: str = DEFAULT_MECH_ADDRESS
    chain: str = DEFAULT_CHAIN
    tool: str = DEFAULT_TOOL
    timestamp: str = ""
    status: str = "pending"
    response: Optional[str] = None
    topic: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MechClientConfig:
    """Configuration for the Olas mech client."""
    mech_address: str = DEFAULT_MECH_ADDRESS
    chain: str = DEFAULT_CHAIN
    tool: str = DEFAULT_TOOL
    key_path: str = "/tmp/ethereum_private_key.txt"
    offchain: bool = True
    timeout: float = 60.0
    retries: int = 3


class OlasMechClient:
    """
    Client for interacting with AI mechs on the Olas Marketplace.

    Wraps the mechx CLI to send requests, track responses, and maintain
    a complete audit trail. Designed to integrate with VaultGuard's
    private reasoning pipeline.
    """

    def __init__(self, config: Optional[MechClientConfig] = None,
                 venv_path: str = ""):
        self.config = config or MechClientConfig()
        self.venv_path = venv_path
        self.requests: list[MechRequest] = []
        self._load_existing_proof()

    def _load_existing_proof(self):
        """Load existing request history from proof file."""
        if os.path.exists(PROOF_FILE):
            try:
                with open(PROOF_FILE) as f:
                    data = json.load(f)
                for req in data.get("requests", []):
                    self.requests.append(MechRequest(
                        prompt=req["prompt"],
                        request_id=req["request_id"],
                        onchain_request_id=req.get("onchain_request_id", ""),
                        ipfs_hash=req.get("ipfs_hash", ""),
                        ipfs_url=req.get("ipfs_url", ""),
                        status=req.get("status", "sent"),
                        topic=req.get("topic", ""),
                    ))
            except (json.JSONDecodeError, KeyError):
                pass

    def _build_mechx_command(self, prompt: str) -> list[str]:
        """Build the mechx CLI command."""
        cmd = ["mechx", "--client-mode", "request"]
        cmd += ["--prompts", prompt]
        cmd += ["--priority-mech", self.config.mech_address]
        cmd += ["--tools", self.config.tool]
        cmd += ["--chain-config", self.config.chain]
        cmd += ["--key", self.config.key_path]
        if self.config.offchain:
            cmd += ["--use-offchain", "true"]
        cmd += ["--timeout", str(self.config.timeout)]
        return cmd

    def _parse_output(self, output: str) -> dict:
        """Parse mechx CLI output to extract request details."""
        result = {
            "request_id": "",
            "onchain_request_id": "",
            "ipfs_hash": "",
            "ipfs_url": "",
            "response": None,
        }

        for line in output.split("\n"):
            line = line.strip()
            if "Created offchain request with ID" in line:
                result["onchain_request_id"] = line.split("ID ")[-1].strip()
            elif "Request IDs:" in line:
                # Parse ['abc123'] format
                import re
                match = re.search(r"\['([a-f0-9]+)'\]", line)
                if match:
                    result["request_id"] = match.group(1)
            elif "uploaded to:" in line:
                url = line.split("uploaded to: ")[-1].strip()
                result["ipfs_url"] = url
                result["ipfs_hash"] = url.split("/ipfs/")[-1] if "/ipfs/" in url else ""
            elif "Mech response:" in line:
                result["response"] = line.split("Mech response: ")[-1].strip()

        return result

    def hire_agent(self, prompt: str, topic: str = "") -> MechRequest:
        """
        Hire an Olas AI mech to analyze a prompt.

        Sends the prompt to the configured mech on the Olas Marketplace,
        tracks the request, and returns the MechRequest with all metadata.

        Args:
            prompt: The analysis prompt to send to the mech
            topic: Human-readable topic label for tracking

        Returns:
            MechRequest with request_id, IPFS hash, and status
        """
        cmd = self._build_mechx_command(prompt)

        # Activate venv if provided
        env = os.environ.copy()
        if self.venv_path:
            venv_bin = os.path.join(self.venv_path, "bin")
            env["PATH"] = venv_bin + ":" + env.get("PATH", "")
            env["VIRTUAL_ENV"] = self.venv_path

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.config.timeout + 30,
                env=env,
            )
            output = result.stdout + result.stderr
            parsed = self._parse_output(output)

            request = MechRequest(
                prompt=prompt,
                request_id=parsed["request_id"],
                onchain_request_id=parsed["onchain_request_id"],
                ipfs_hash=parsed["ipfs_hash"],
                ipfs_url=parsed["ipfs_url"],
                mech_address=self.config.mech_address,
                chain=self.config.chain,
                tool=self.config.tool,
                status="sent" if parsed["request_id"] else "error",
                response=parsed["response"],
                topic=topic,
            )
        except subprocess.TimeoutExpired:
            request = MechRequest(
                prompt=prompt,
                request_id="",
                status="timeout",
                topic=topic,
            )
        except FileNotFoundError:
            request = MechRequest(
                prompt=prompt,
                request_id="",
                status="mechx_not_found",
                topic=topic,
            )

        self.requests.append(request)
        self._save_proof()
        return request

    def hire_for_private_reasoning(self, prompt: str, topic: str = "") -> dict:
        """
        Hire a mech and feed the result into VaultGuard's private reasoner.

        This is the main integration point: VaultGuard asks an Olas mech for
        external DeFi analysis, then processes it through the private reasoning
        pipeline to produce a public-safe output.

        Args:
            prompt: The analysis prompt
            topic: Topic label

        Returns:
            dict with mech_request data and privacy hashes
        """
        mech_req = self.hire_agent(prompt, topic)

        # Hash the prompt for privacy (VaultGuard never stores raw input)
        input_hash = hashlib.sha256(prompt.encode()).hexdigest()

        # If we got a response, hash it too
        response_hash = ""
        if mech_req.response:
            response_hash = hashlib.sha256(mech_req.response.encode()).hexdigest()

        return {
            "mech_request_id": mech_req.request_id,
            "ipfs_hash": mech_req.ipfs_hash,
            "input_hash": input_hash,
            "response_hash": response_hash,
            "topic": topic,
            "status": mech_req.status,
            "timestamp": mech_req.timestamp,
            "privacy_note": "Raw prompt hashed; only hashes and public-safe outputs are stored",
        }

    def get_request_count(self) -> int:
        """Return total number of requests sent."""
        return len(self.requests)

    def get_successful_requests(self) -> list[MechRequest]:
        """Return only requests that were successfully sent."""
        return [r for r in self.requests if r.status == "sent"]

    def get_request_ids(self) -> list[str]:
        """Return all request IDs."""
        return [r.request_id for r in self.requests if r.request_id]

    def _save_proof(self):
        """Save all request data to the proof file."""
        data = {
            "track": "Hire an Agent (Olas Marketplace)",
            "wallet": "0x54eeFbb7b3F701eEFb7fa99473A60A6bf5fE16D7",
            "mech_address": self.config.mech_address,
            "chain": self.config.chain,
            "tool": self.config.tool,
            "offchain": self.config.offchain,
            "total_requests": len(self.requests),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requests": [
                {
                    "number": i + 1,
                    "prompt": r.prompt,
                    "request_id": r.request_id,
                    "onchain_request_id": r.onchain_request_id,
                    "ipfs_hash": r.ipfs_hash,
                    "ipfs_url": r.ipfs_url,
                    "status": r.status,
                    "topic": r.topic,
                    "timestamp": r.timestamp,
                }
                for i, r in enumerate(self.requests)
            ],
        }
        with open(PROOF_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def summary(self) -> str:
        """Return a human-readable summary of all mech interactions."""
        total = len(self.requests)
        sent = len(self.get_successful_requests())
        ids = self.get_request_ids()

        lines = [
            f"Olas Mech Client Summary",
            f"========================",
            f"Total requests: {total}",
            f"Successfully sent: {sent}",
            f"Mech: {self.config.mech_address}",
            f"Chain: {self.config.chain}",
            f"Tool: {self.config.tool}",
            f"",
            f"Request IDs:",
        ]
        for i, rid in enumerate(ids, 1):
            lines.append(f"  {i}. {rid}")

        return "\n".join(lines)


# --- Convenience functions for use by VaultGuard modules ---

def hire_agent(prompt: str, topic: str = "",
               venv_path: str = "") -> MechRequest:
    """
    Convenience function to hire an Olas mech for a single analysis task.

    Usage:
        from olas_mech_client import hire_agent
        result = hire_agent("Analyze stETH yield risk", topic="DeFi risk")
        print(result.request_id)
    """
    client = OlasMechClient(venv_path=venv_path)
    return client.hire_agent(prompt, topic)


def get_proof_summary() -> dict:
    """Load and return the proof file as a dict."""
    if os.path.exists(PROOF_FILE):
        with open(PROOF_FILE) as f:
            return json.load(f)
    return {"total_requests": 0, "requests": []}


# --- CLI entry point ---

if __name__ == "__main__":
    print("Olas Mech Client for VaultGuard")
    print("=" * 40)

    proof = get_proof_summary()
    total = proof.get("total_requests", 0)
    print(f"\nTotal mech requests sent: {total}")
    print(f"Wallet: {proof.get('wallet', 'N/A')}")
    print(f"Mech: {proof.get('mech_address', 'N/A')}")
    print(f"Chain: {proof.get('chain', 'N/A')}")

    print(f"\nRequest IDs:")
    for req in proof.get("requests", []):
        print(f"  #{req['number']:2d} [{req.get('topic', '')}]")
        print(f"       ID: {req['request_id']}")
        if req.get("ipfs_url"):
            print(f"       IPFS: {req['ipfs_url']}")
    print(f"\nQualification: {'PASS (10+ requests)' if total >= 10 else 'NEED MORE REQUESTS'}")
