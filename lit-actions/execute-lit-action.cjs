/**
 * Execute VaultGuard Private Reasoning via Lit Protocol TEE
 *
 * This script demonstrates calling the Lit Action either:
 *   (a) inline (code string), or
 *   (b) via IPFS CID (after pinning)
 *
 * Requires: LIT_PRIVATE_KEY env var or an auth session.
 * Network: datil-dev (Lit testnet with Chipotle TEE)
 */
const { LitNodeClient } = require("@lit-protocol/lit-node-client");
const fs = require("fs");
const path = require("path");

const IPFS_CID = "QmeZQgyVw74RQXaULgZ4XN4M7eWSmsTq6jMtzq1BZ8uoLJ";

async function main() {
  console.log("=== VaultGuard x Lit Protocol TEE Execution ===\n");

  // 1. Connect to Lit Network
  console.log("1. Connecting to Lit datil-dev network...");
  const litNodeClient = new LitNodeClient({
    litNetwork: "datil-dev",
    debug: false,
  });

  try {
    await litNodeClient.connect();
    console.log("   Connected to Lit Network!\n");
  } catch (e) {
    console.log(`   Connection note: ${e.message}\n`);
    console.log("   To execute inside the Chipotle TEE, you need:");
    console.log("     1. A Lit auth session (PKP NFT mint or wallet auth signature)");
    console.log("     2. The @lit-protocol/lit-node-client SDK installed");
    console.log("     3. Access to the datil-dev network\n");
    console.log("   See: https://developer.litprotocol.com/sdk/authentication\n");
    console.log("   Demonstrating the integration pattern with expected outputs:\n");
  }

  // 2. Load the Lit Action code
  const actionCode = fs.readFileSync(
    path.join(__dirname, "vaultguard-private-reasoning.js"),
    "utf8"
  );

  // 3. Show the two execution patterns
  console.log("2. Execution patterns for VaultGuard private reasoning:\n");

  console.log("   Pattern A - Inline code:");
  console.log("   ```");
  console.log("   const result = await litNodeClient.executeJs({");
  console.log(`     code: litActionCode,  // ${actionCode.length} bytes`);
  console.log("     authContext: authContext,");
  console.log("     jsParams: {");
  console.log('       vaultData: { balance: "10000", yieldRate: "4.5", riskScore: "0.3" },');
  console.log("       threshold: 0.05,");
  console.log('       actionType: "health_check"');
  console.log("     }");
  console.log("   });");
  console.log("   ```\n");

  console.log("   Pattern B - IPFS CID (after pinning):");
  console.log("   ```");
  console.log("   const result = await litNodeClient.executeJs({");
  console.log(`     ipfsId: "${IPFS_CID}",`);
  console.log("     authContext: authContext,");
  console.log("     jsParams: { ... }");
  console.log("   });");
  console.log("   ```\n");

  // 4. Show what the output looks like
  console.log("3. Expected TEE output (private data stays inside enclave):\n");

  const exampleOutput = {
    action: "HEALTHY",
    confidence: 85,
    reasoningHash: "d63ae4e21915eb727bdad36322ff47cba33933f3a2841d9ec6daccfc9cce87c1",
    timestamp: Date.now(),
    teeVerified: true,
    actionType: "health_check",
  };
  console.log(JSON.stringify(exampleOutput, null, 2));

  console.log("\n   Note: balance=10000, yieldRate=4.5, riskScore=0.3");
  console.log("   are NEVER exposed outside the TEE.\n");

  // 5. Summary
  console.log("=== Integration Summary ===");
  console.log(`IPFS CID:      ${IPFS_CID}`);
  console.log("Lit Network:   datil-dev (Chipotle TEE)");
  console.log("SDK Version:   @lit-protocol/lit-node-client@7.4.0");
  console.log("Action Types:  health_check, rebalance, risk_check");
  console.log("Privacy:       Vault balances + reasoning stay in TEE");
  console.log("Public Output: Decision + confidence + reasoning hash");

  // Cleanup
  if (litNodeClient.ready) {
    await litNodeClient.disconnect();
  }
}

main().catch(console.error);
