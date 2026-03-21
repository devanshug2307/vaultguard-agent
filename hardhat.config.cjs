require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.19",
  networks: {
    baseSepolia: {
      url: "https://sepolia.base.org",
      accounts: [
        "b5d82d77b0ba619e3bec08dfeb5bde6b55fe5b93e2b4b25dfb07c3e925b13d69",
      ],
      chainId: 84532,
    },
  },
};
