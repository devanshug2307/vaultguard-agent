const { ethers } = require("hardhat");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying PrivacyVault with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  // Deploy the contract
  const PrivacyVault = await ethers.getContractFactory("PrivacyVault");
  const vault = await PrivacyVault.deploy();
  await vault.waitForDeployment();
  const contractAddress = await vault.getAddress();
  console.log("\nPrivacyVault deployed to:", contractAddress);
  console.log("Deploy TX hash:", vault.deploymentTransaction().hash);

  // Wait for nonce to sync after deploy
  await sleep(5000);

  // --- Commit 3 reasoning sessions onchain ---

  // Session 1: Treasury Strategy
  const inputHash1 = ethers.keccak256(
    ethers.toUtf8Bytes("Portfolio: $3.5M across ETH, stETH, USDC. Runway 18 months.")
  );
  const reasoningHash1 = ethers.keccak256(
    ethers.toUtf8Bytes("Risk analysis: volatile exposure too high at 60%. Recommend rebalancing to 45% volatile, 55% stable yield.")
  );
  const action1 = "Reduce volatile exposure 15%, increase yield positions";

  console.log("\n--- Session 1: Treasury Strategy ---");
  const tx1 = await vault.commitReasoning(inputHash1, reasoningHash1, action1);
  const receipt1 = await tx1.wait();
  console.log("TX Hash:", tx1.hash);
  console.log("Block:", receipt1.blockNumber);

  await sleep(3000);

  // Session 2: Governance Deliberation
  const inputHash2 = ethers.keccak256(
    ethers.toUtf8Bytes("Proposal #47: Increase staking rewards from 5% to 8%. 340 votes for, 120 against.")
  );
  const reasoningHash2 = ethers.keccak256(
    ethers.toUtf8Bytes("Impact analysis: reward increase sustainable for 12 months given treasury. Security risk: minimal. Community sentiment: positive.")
  );
  const action2 = "SUPPORT with amendment: cap increase at 7% with 6-month review";

  console.log("\n--- Session 2: Governance Deliberation ---");
  const tx2 = await vault.commitReasoning(inputHash2, reasoningHash2, action2);
  const receipt2 = await tx2.wait();
  console.log("TX Hash:", tx2.hash);
  console.log("Block:", receipt2.blockNumber);

  await sleep(3000);

  // Session 3: Deal Evaluation
  const inputHash3 = ethers.keccak256(
    ethers.toUtf8Bytes("Term sheet: Series B, $25M valuation, 2x liquidation preference, 4-year vesting.")
  );
  const reasoningHash3 = ethers.keccak256(
    ethers.toUtf8Bytes("Benchmark analysis: valuation 15% above market. Liquidation pref standard. Vesting acceptable. Counter at $22M with 1.5x pref.")
  );
  const action3 = "Accept with 10% haircut and milestone-based vesting";

  console.log("\n--- Session 3: Deal Evaluation ---");
  const tx3 = await vault.commitReasoning(inputHash3, reasoningHash3, action3);
  const receipt3 = await tx3.wait();
  console.log("TX Hash:", tx3.hash);
  console.log("Block:", receipt3.blockNumber);

  // Verify all sessions
  console.log("\n=== Verification ===");
  const total = await vault.totalSessions();
  console.log("Total sessions committed:", total.toString());

  for (let i = 0; i < Number(total); i++) {
    const session = await vault.verifySession(i);
    console.log(`\nSession ${i}:`);
    console.log("  Agent:", session.agent);
    console.log("  Input Hash:", session.inputHash);
    console.log("  Reasoning Hash:", session.reasoningHash);
    console.log("  Action:", session.action);
    console.log("  Timestamp:", new Date(Number(session.timestamp) * 1000).toISOString());
  }

  // Print summary for README
  console.log("\n========================================");
  console.log("DEPLOYMENT SUMMARY (for README)");
  console.log("========================================");
  console.log(`Contract Address: ${contractAddress}`);
  console.log(`Deploy TX:  ${vault.deploymentTransaction().hash}`);
  console.log(`Session 1 TX: ${tx1.hash}`);
  console.log(`Session 2 TX: ${tx2.hash}`);
  console.log(`Session 3 TX: ${tx3.hash}`);
  console.log("========================================");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
