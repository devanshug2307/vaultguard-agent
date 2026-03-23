const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying PrivacyVault to Status Network Sepolia");
  console.log("Deployer:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");
  console.log("Note: Status Network is gasless (gas = 0 at protocol level)\n");

  // Deploy the contract
  const PrivacyVault = await ethers.getContractFactory("PrivacyVault");
  const vault = await PrivacyVault.deploy();
  await vault.waitForDeployment();
  const contractAddress = await vault.getAddress();
  const deployTx = vault.deploymentTransaction();

  console.log("PrivacyVault deployed to:", contractAddress);
  console.log("Deploy TX hash:", deployTx.hash);
  console.log("Gasless deployment: gas price = 0 (Status Network protocol level)\n");

  // Wait for confirmation
  await sleep(5000);

  // Verify deployment
  const total = await vault.totalSessions();
  console.log("Contract verified: totalSessions =", total.toString());

  // Save deployment proof
  const proof = {
    deployment: "PrivacyVault on Status Network Sepolia",
    network: {
      name: "Status Network Sepolia",
      chainId: 1660990954,
      rpcUrl: "https://public.sepolia.rpc.status.network",
      explorer: "https://sepoliascan.status.network",
      gasPrice: 0,
      gasless: true,
    },
    contract: {
      name: "PrivacyVault",
      address: contractAddress,
      deployTxHash: deployTx.hash,
      explorerUrl: `https://sepoliascan.status.network/address/${contractAddress}`,
    },
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
  };

  const proofPath = path.join(__dirname, "..", "status_deploy_proof.json");
  fs.writeFileSync(proofPath, JSON.stringify(proof, null, 2));
  console.log("\nDeployment proof saved:", proofPath);

  // Print summary
  console.log("\n========================================");
  console.log("STATUS NETWORK DEPLOYMENT SUMMARY");
  console.log("========================================");
  console.log(`Contract:  ${contractAddress}`);
  console.log(`TX Hash:   ${deployTx.hash}`);
  console.log(`Explorer:  https://sepoliascan.status.network/address/${contractAddress}`);
  console.log(`Gas Cost:  0 (gasless at protocol level)`);
  console.log(`Chain ID:  1660990954`);
  console.log("========================================");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
