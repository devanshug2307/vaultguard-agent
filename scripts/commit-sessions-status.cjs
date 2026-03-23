const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const [signer] = await ethers.getSigners();
  console.log("=== VaultGuard: Commit Reasoning Sessions to Status Network ===\n");
  console.log("Signer:", signer.address);

  const balance = await ethers.provider.getBalance(signer.address);
  console.log("Balance:", ethers.formatEther(balance), "ETH");
  console.log("Note: Status Network is gasless (gas = 0 at protocol level)\n");

  // Connect to deployed PrivacyVault
  const VAULT_ADDRESS = "0xDcb6aEdb34b7c91F3b83a0Bf61c7d84DB2f9F2bF";
  const vaultAbi = [
    "function commitReasoning(bytes32 inputHash, bytes32 reasoningHash, string calldata action) external returns (uint256 sessionId)",
    "function verifySession(uint256 sessionId) external view returns (address agent, bytes32 inputHash, bytes32 reasoningHash, string action, uint256 timestamp)",
    "function totalSessions() external view returns (uint256)",
    "event ReasoningCommitted(uint256 indexed sessionId, address indexed agent, bytes32 inputHash, bytes32 reasoningHash, string action, uint256 timestamp)"
  ];

  const vault = new ethers.Contract(VAULT_ADDRESS, vaultAbi, signer);

  // Check current state
  const totalBefore = await vault.totalSessions();
  console.log("Sessions before:", totalBefore.toString());

  // Define 3 reasoning sessions to commit
  const sessions = [
    {
      label: "session-1",
      inputSeed: "vaultguard-private-treasury-analysis-session-1",
      reasoningSeed: "vaultguard-reasoning-output-rebalance-session-1",
      action: "REBALANCE: Reduce volatile exposure 15%, increase stablecoin yield positions"
    },
    {
      label: "session-2",
      inputSeed: "vaultguard-private-governance-deliberation-session-2",
      reasoningSeed: "vaultguard-reasoning-output-governance-session-2",
      action: "VOTE: Support proposal #42 with amendment for security audit requirement"
    },
    {
      label: "session-3",
      inputSeed: "vaultguard-private-deal-evaluation-session-3",
      reasoningSeed: "vaultguard-reasoning-output-deal-session-3",
      action: "EVALUATE: Counter-offer at 12% discount with 6-month vesting schedule"
    }
  ];

  const results = [];

  for (let i = 0; i < sessions.length; i++) {
    const s = sessions[i];
    console.log(`\n--- Committing ${s.label} ---`);

    // Generate deterministic hashes using keccak256
    const inputHash = ethers.keccak256(ethers.toUtf8Bytes(s.inputSeed));
    const reasoningHash = ethers.keccak256(ethers.toUtf8Bytes(s.reasoningSeed));

    console.log("  Input hash:     ", inputHash);
    console.log("  Reasoning hash: ", reasoningHash);
    console.log("  Action:         ", s.action);

    // Commit the reasoning session onchain
    const tx = await vault.commitReasoning(inputHash, reasoningHash, s.action);
    console.log("  TX hash:        ", tx.hash);

    const receipt = await tx.wait();
    console.log("  Block:          ", receipt.blockNumber);
    console.log("  Gas used:       ", receipt.gasUsed.toString(), "(gasless = free)");

    // Parse the event to get sessionId
    let sessionId = null;
    for (const log of receipt.logs) {
      try {
        const parsed = vault.interface.parseLog({ topics: log.topics, data: log.data });
        if (parsed && parsed.name === "ReasoningCommitted") {
          sessionId = parsed.args.sessionId.toString();
        }
      } catch (e) {
        // skip non-matching logs
      }
    }
    console.log("  Session ID:     ", sessionId);

    results.push({
      label: s.label,
      sessionId: sessionId,
      inputHash: inputHash,
      reasoningHash: reasoningHash,
      action: s.action,
      txHash: tx.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed.toString(),
      explorerUrl: `https://sepoliascan.status.network/tx/${tx.hash}`
    });

    // Small delay between transactions
    if (i < sessions.length - 1) {
      await sleep(2000);
    }
  }

  // Verify all sessions
  console.log("\n\n=== Verification ===\n");
  const totalAfter = await vault.totalSessions();
  console.log("Total sessions after:", totalAfter.toString());

  for (const r of results) {
    if (r.sessionId !== null) {
      const [agent, inputHash, reasoningHash, action, timestamp] = await vault.verifySession(r.sessionId);
      console.log(`\nSession ${r.sessionId} verified:`);
      console.log("  Agent:          ", agent);
      console.log("  Input hash:     ", inputHash);
      console.log("  Reasoning hash: ", reasoningHash);
      console.log("  Action:         ", action);
      console.log("  Timestamp:      ", new Date(Number(timestamp) * 1000).toISOString());
    }
  }

  // Save proof
  const proof = {
    description: "VaultGuard reasoning sessions committed to PrivacyVault on Status Network Sepolia",
    network: {
      name: "Status Network Sepolia",
      chainId: 1660990954,
      rpcUrl: "https://public.sepolia.rpc.status.network",
      explorer: "https://sepoliascan.status.network",
      gasPrice: 0,
      gasless: true
    },
    contract: {
      name: "PrivacyVault",
      address: VAULT_ADDRESS,
      explorerUrl: `https://sepoliascan.status.network/address/${VAULT_ADDRESS}`
    },
    signer: signer.address,
    sessionsCommitted: results.length,
    totalSessionsOnContract: totalAfter.toString(),
    sessions: results,
    timestamp: new Date().toISOString()
  };

  const proofPath = path.join(__dirname, "..", "status_sessions_proof.json");
  fs.writeFileSync(proofPath, JSON.stringify(proof, null, 2));
  console.log("\n\nProof saved to:", proofPath);

  // Print summary
  console.log("\n========================================");
  console.log("STATUS NETWORK SESSION COMMIT SUMMARY");
  console.log("========================================");
  console.log(`Contract:    ${VAULT_ADDRESS}`);
  console.log(`Sessions:    ${results.length} committed`);
  console.log(`Gas Cost:    0 (gasless at protocol level)`);
  console.log(`Chain ID:    1660990954`);
  for (const r of results) {
    console.log(`\n  ${r.label}:`);
    console.log(`    TX:    ${r.txHash}`);
    console.log(`    Link:  ${r.explorerUrl}`);
  }
  console.log("\n========================================");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
