const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("VaultGuardSliceHook", function () {
  let vault, hook;
  let owner, buyer, verifiedAgent;

  const BASE_PRICE = ethers.parseEther("0.001"); // 0.001 ETH
  const DISCOUNT_BPS = 2000; // 20% discount
  const MIN_SESSIONS = 2; // Need 2+ vault sessions for discount

  beforeEach(async function () {
    [owner, buyer, verifiedAgent] = await ethers.getSigners();

    // Deploy PrivacyVault
    const Vault = await ethers.getContractFactory("PrivacyVault");
    vault = await Vault.deploy();
    await vault.waitForDeployment();

    // Deploy VaultGuardSliceHook
    const Hook = await ethers.getContractFactory("VaultGuardSliceHook");
    hook = await Hook.deploy(
      await vault.getAddress(),
      BASE_PRICE,
      DISCOUNT_BPS,
      MIN_SESSIONS
    );
    await hook.waitForDeployment();
  });

  describe("Deployment", function () {
    it("sets correct vault address", async function () {
      expect(await hook.vault()).to.equal(await vault.getAddress());
    });

    it("sets correct base price", async function () {
      expect(await hook.basePrice()).to.equal(BASE_PRICE);
    });

    it("sets correct discount", async function () {
      expect(await hook.verifiedDiscountBps()).to.equal(DISCOUNT_BPS);
    });

    it("sets correct min sessions", async function () {
      expect(await hook.minSessionsForDiscount()).to.equal(MIN_SESSIONS);
    });

    it("reverts if discount exceeds 50%", async function () {
      const Hook = await ethers.getContractFactory("VaultGuardSliceHook");
      await expect(
        Hook.deploy(await vault.getAddress(), BASE_PRICE, 5001, MIN_SESSIONS)
      ).to.be.revertedWithCustomError(hook, "InvalidDiscount");
    });
  });

  describe("ISliceProductPrice - Dynamic Pricing", function () {
    it("returns base price for unverified buyer", async function () {
      const [ethPrice, currencyPrice] = await hook.productPrice(
        1, // slicerId
        1, // productId
        ethers.ZeroAddress, // currency (ETH)
        1, // quantity
        buyer.address,
        "0x"
      );
      expect(ethPrice).to.equal(BASE_PRICE);
      expect(currencyPrice).to.equal(0);
    });

    it("returns base price * quantity for multiple units", async function () {
      const qty = 5;
      const [ethPrice] = await hook.productPrice(
        1, 1, ethers.ZeroAddress, qty, buyer.address, "0x"
      );
      expect(ethPrice).to.equal(BASE_PRICE * BigInt(qty));
    });

    it("returns discounted price for verified agent", async function () {
      // Make verifiedAgent a verified agent by committing 2 sessions
      const hash1 = ethers.keccak256(ethers.toUtf8Bytes("input1"));
      const hash2 = ethers.keccak256(ethers.toUtf8Bytes("reasoning1"));
      await vault.connect(verifiedAgent).commitReasoning(hash1, hash2, "action1");

      const hash3 = ethers.keccak256(ethers.toUtf8Bytes("input2"));
      const hash4 = ethers.keccak256(ethers.toUtf8Bytes("reasoning2"));
      await vault.connect(verifiedAgent).commitReasoning(hash3, hash4, "action2");

      const [ethPrice] = await hook.productPrice(
        1, 1, ethers.ZeroAddress, 1, verifiedAgent.address, "0x"
      );

      // 20% discount: 0.001 ETH * 0.8 = 0.0008 ETH
      const expected = (BASE_PRICE * BigInt(10000 - DISCOUNT_BPS)) / BigInt(10000);
      expect(ethPrice).to.equal(expected);
    });

    it("does not discount agent with fewer sessions than minimum", async function () {
      // Only 1 session (need 2)
      const hash1 = ethers.keccak256(ethers.toUtf8Bytes("input1"));
      const hash2 = ethers.keccak256(ethers.toUtf8Bytes("reasoning1"));
      await vault.connect(verifiedAgent).commitReasoning(hash1, hash2, "action1");

      const [ethPrice] = await hook.productPrice(
        1, 1, ethers.ZeroAddress, 1, verifiedAgent.address, "0x"
      );
      expect(ethPrice).to.equal(BASE_PRICE); // No discount
    });
  });

  describe("ISliceProductAction - Purchase Gating", function () {
    it("allows all purchases (no gate)", async function () {
      const allowed = await hook.isPurchaseAllowed(
        1, 1, buyer.address, 1, "0x", "0x"
      );
      expect(allowed).to.be.true;
    });
  });

  describe("ISliceProductAction - Post-Purchase Proof", function () {
    it("commits a commerce proof to PrivacyVault on purchase", async function () {
      const tx = await hook.onProductPurchase(
        1, // slicerId
        1, // productId
        buyer.address,
        3, // quantity
        "0x",
        "0x"
      );
      await tx.wait();

      // Check vault has a new session
      expect(await vault.totalSessions()).to.equal(1);

      // Verify the session data
      const session = await vault.verifySession(0);
      expect(session.action).to.include("slice_purchase");
      expect(session.action).to.include("slicer=1");
      expect(session.action).to.include("product=1");
      expect(session.action).to.include("qty=3");
    });

    it("increments purchase counters", async function () {
      await hook.onProductPurchase(1, 1, buyer.address, 1, "0x", "0x");
      await hook.onProductPurchase(1, 2, buyer.address, 2, "0x", "0x");

      expect(await hook.totalPurchases()).to.equal(2);
      expect(await hook.buyerPurchaseCount(buyer.address)).to.equal(2);
      expect(await hook.totalCommerceProofs()).to.equal(2);
    });

    it("emits PurchaseProcessed event", async function () {
      await expect(hook.onProductPurchase(1, 1, buyer.address, 1, "0x", "0x"))
        .to.emit(hook, "PurchaseProcessed")
        .withArgs(
          1, // slicerId
          1, // productId
          buyer.address,
          1, // quantity
          BASE_PRICE, // pricePaid
          false, // verifiedBuyer
          0 // vaultSessionId
        );
    });

    it("records verified status in event for verified agent", async function () {
      // Make agent verified
      const h1 = ethers.keccak256(ethers.toUtf8Bytes("i1"));
      const h2 = ethers.keccak256(ethers.toUtf8Bytes("r1"));
      await vault.connect(verifiedAgent).commitReasoning(h1, h2, "a1");
      const h3 = ethers.keccak256(ethers.toUtf8Bytes("i2"));
      const h4 = ethers.keccak256(ethers.toUtf8Bytes("r2"));
      await vault.connect(verifiedAgent).commitReasoning(h3, h4, "a2");

      await expect(
        hook.onProductPurchase(1, 1, verifiedAgent.address, 1, "0x", "0x")
      )
        .to.emit(hook, "PurchaseProcessed")
        .withArgs(1, 1, verifiedAgent.address, 1, BASE_PRICE, true, 2);
    });
  });

  describe("Admin - Configure Pricing", function () {
    it("owner can update pricing", async function () {
      const newPrice = ethers.parseEther("0.005");
      await hook.configurePricing(newPrice, 3000, 5);

      expect(await hook.basePrice()).to.equal(newPrice);
      expect(await hook.verifiedDiscountBps()).to.equal(3000);
      expect(await hook.minSessionsForDiscount()).to.equal(5);
    });

    it("non-owner cannot update pricing", async function () {
      await expect(
        hook.connect(buyer).configurePricing(0, 0, 0)
      ).to.be.revertedWithCustomError(hook, "OnlyOwner");
    });

    it("rejects discount over 50%", async function () {
      await expect(
        hook.configurePricing(BASE_PRICE, 5001, MIN_SESSIONS)
      ).to.be.revertedWithCustomError(hook, "InvalidDiscount");
    });
  });

  describe("View Helpers", function () {
    it("isVerifiedAgent returns false for new address", async function () {
      expect(await hook.isVerifiedAgent(buyer.address)).to.be.false;
    });

    it("isVerifiedAgent returns true after enough sessions", async function () {
      const h1 = ethers.keccak256(ethers.toUtf8Bytes("i1"));
      const h2 = ethers.keccak256(ethers.toUtf8Bytes("r1"));
      await vault.connect(buyer).commitReasoning(h1, h2, "a1");
      await vault.connect(buyer).commitReasoning(h2, h1, "a2");

      expect(await hook.isVerifiedAgent(buyer.address)).to.be.true;
    });

    it("getCommerceSessionId returns correct IDs", async function () {
      await hook.onProductPurchase(1, 1, buyer.address, 1, "0x", "0x");
      await hook.onProductPurchase(2, 1, buyer.address, 1, "0x", "0x");

      expect(await hook.getCommerceSessionId(0)).to.equal(0);
      expect(await hook.getCommerceSessionId(1)).to.equal(1);
    });
  });
});
