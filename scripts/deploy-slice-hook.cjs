const { ethers } = require("hardhat");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying VaultGuardSliceHook with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  // ─── Configuration ────────────────────────────────────────────────
  // Set this to your already-deployed PrivacyVault address on Base Sepolia.
  // If empty, we deploy a fresh PrivacyVault first.
  const EXISTING_VAULT = process.env.PRIVACY_VAULT_ADDRESS || "";

  const BASE_PRICE = ethers.parseEther("0.001"); // 0.001 ETH per unit
  const DISCOUNT_BPS = 2000; // 20% discount for verified agents
  const MIN_SESSIONS = 2; // Need 2+ vault sessions for discount

  // ─── Deploy or reuse PrivacyVault ─────────────────────────────────
  let vaultAddress;
  if (EXISTING_VAULT) {
    vaultAddress = EXISTING_VAULT;
    console.log("\nUsing existing PrivacyVault at:", vaultAddress);
  } else {
    const Vault = await ethers.getContractFactory("PrivacyVault");
    const vault = await Vault.deploy();
    await vault.waitForDeployment();
    vaultAddress = await vault.getAddress();
    console.log("\nDeployed new PrivacyVault at:", vaultAddress);
    console.log("  TX:", vault.deploymentTransaction().hash);
    await sleep(5000);
  }

  // ─── Deploy VaultGuardSliceHook ───────────────────────────────────
  const Hook = await ethers.getContractFactory("VaultGuardSliceHook");
  const hook = await Hook.deploy(vaultAddress, BASE_PRICE, DISCOUNT_BPS, MIN_SESSIONS);
  await hook.waitForDeployment();
  const hookAddress = await hook.getAddress();
  console.log("\nVaultGuardSliceHook deployed to:", hookAddress);
  console.log("  TX:", hook.deploymentTransaction().hash);

  await sleep(5000);

  // ─── Demo: simulate a Slice product purchase ─────────────────────
  console.log("\n--- Simulating Slice product purchase (onProductPurchase) ---");

  const tx = await hook.onProductPurchase(
    1,   // slicerId
    1,   // productId
    deployer.address,  // buyer
    2,   // quantity
    "0x",
    "0x"
  );
  const receipt = await tx.wait();
  console.log("Purchase TX:", tx.hash);
  console.log("Block:", receipt.blockNumber);

  // ─── Verify the commerce proof was committed ─────────────────────
  const vault = await ethers.getContractAt("PrivacyVault", vaultAddress);
  const totalSessions = await vault.totalSessions();
  console.log("\nTotal PrivacyVault sessions:", totalSessions.toString());

  const lastSessionId = Number(totalSessions) - 1;
  const session = await vault.verifySession(lastSessionId);
  console.log("Commerce proof session:", lastSessionId);
  console.log("  Agent:", session.agent);
  console.log("  Action:", session.action);
  console.log("  Timestamp:", new Date(Number(session.timestamp) * 1000).toISOString());

  // ─── Check pricing for unverified vs verified buyer ───────────────
  console.log("\n--- Pricing check ---");
  const [unverifiedPrice] = await hook.productPrice(
    1, 1, ethers.ZeroAddress, 1, deployer.address, "0x"
  );
  console.log("Unverified buyer price (1 unit):", ethers.formatEther(unverifiedPrice), "ETH");

  const isVerified = await hook.isVerifiedAgent(deployer.address);
  console.log("Deployer is verified agent:", isVerified);

  // ─── Summary ──────────────────────────────────────────────────────
  console.log("\n========================================");
  console.log("SLICE HOOK DEPLOYMENT SUMMARY");
  console.log("========================================");
  console.log(`PrivacyVault:         ${vaultAddress}`);
  console.log(`VaultGuardSliceHook:  ${hookAddress}`);
  console.log(`Hook Deploy TX:       ${hook.deploymentTransaction().hash}`);
  console.log(`Purchase Demo TX:     ${tx.hash}`);
  console.log(`Base Price:           ${ethers.formatEther(BASE_PRICE)} ETH`);
  console.log(`Verified Discount:    ${DISCOUNT_BPS / 100}%`);
  console.log(`Min Sessions:         ${MIN_SESSIONS}`);
  console.log("========================================");
  console.log("\nSlice Hooks Track Integration:");
  console.log("- ISliceProductPrice: dynamic pricing based on vault verification");
  console.log("- ISliceProductAction: commits commerce proofs to PrivacyVault");
  console.log("- Ready to register with a Slice store on Base");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
