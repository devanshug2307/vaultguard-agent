const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PrivacyVault", function () {
  let vault;
  let owner, agent1, agent2;

  // Sample hashes for testing
  const inputHash1 = ethers.keccak256(ethers.toUtf8Bytes("portfolio data"));
  const reasoningHash1 = ethers.keccak256(ethers.toUtf8Bytes("risk analysis reasoning"));
  const action1 = "Reduce volatile exposure 15%";

  const inputHash2 = ethers.keccak256(ethers.toUtf8Bytes("governance proposal"));
  const reasoningHash2 = ethers.keccak256(ethers.toUtf8Bytes("governance deliberation"));
  const action2 = "SUPPORT with amendments";

  const inputHash3 = ethers.keccak256(ethers.toUtf8Bytes("deal term sheet"));
  const reasoningHash3 = ethers.keccak256(ethers.toUtf8Bytes("deal evaluation"));
  const action3 = "Accept with 10% haircut";

  beforeEach(async function () {
    [owner, agent1, agent2] = await ethers.getSigners();
    const PrivacyVault = await ethers.getContractFactory("PrivacyVault");
    vault = await PrivacyVault.deploy();
    await vault.waitForDeployment();
  });

  // --- Test 1: Commit a reasoning proof and get sessionId 0 ---
  it("should commit reasoning and return sessionId 0", async function () {
    const tx = await vault.commitReasoning(inputHash1, reasoningHash1, action1);
    const receipt = await tx.wait();

    // Check that a ReasoningCommitted event was emitted
    const event = receipt.logs.find((log) => {
      try {
        return vault.interface.parseLog(log).name === "ReasoningCommitted";
      } catch {
        return false;
      }
    });
    expect(event).to.not.be.undefined;

    const parsed = vault.interface.parseLog(event);
    expect(parsed.args.sessionId).to.equal(0n);
    expect(parsed.args.agent).to.equal(owner.address);
    expect(parsed.args.inputHash).to.equal(inputHash1);
    expect(parsed.args.reasoningHash).to.equal(reasoningHash1);
    expect(parsed.args.action).to.equal(action1);
  });

  // --- Test 2: Verify a committed session ---
  it("should verify a committed session with correct data", async function () {
    await vault.commitReasoning(inputHash1, reasoningHash1, action1);

    const result = await vault.verifySession(0);
    expect(result.agent).to.equal(owner.address);
    expect(result.inputHash).to.equal(inputHash1);
    expect(result.reasoningHash).to.equal(reasoningHash1);
    expect(result.action).to.equal(action1);
    expect(result.timestamp).to.be.greaterThan(0n);
  });

  // --- Test 3: Multiple sessions increment sessionId ---
  it("should assign incrementing session IDs", async function () {
    await vault.commitReasoning(inputHash1, reasoningHash1, action1);
    await vault.commitReasoning(inputHash2, reasoningHash2, action2);
    await vault.commitReasoning(inputHash3, reasoningHash3, action3);

    const session0 = await vault.verifySession(0);
    const session1 = await vault.verifySession(1);
    const session2 = await vault.verifySession(2);

    expect(session0.action).to.equal(action1);
    expect(session1.action).to.equal(action2);
    expect(session2.action).to.equal(action3);
  });

  // --- Test 4: totalSessions tracks count ---
  it("should track total sessions correctly", async function () {
    expect(await vault.totalSessions()).to.equal(0n);

    await vault.commitReasoning(inputHash1, reasoningHash1, action1);
    expect(await vault.totalSessions()).to.equal(1n);

    await vault.commitReasoning(inputHash2, reasoningHash2, action2);
    expect(await vault.totalSessions()).to.equal(2n);

    await vault.commitReasoning(inputHash3, reasoningHash3, action3);
    expect(await vault.totalSessions()).to.equal(3n);
  });

  // --- Test 5: Agent session tracking ---
  it("should track sessions per agent", async function () {
    await vault.commitReasoning(inputHash1, reasoningHash1, action1);
    await vault.commitReasoning(inputHash2, reasoningHash2, action2);

    const ownerSessions = await vault.getAgentSessions(owner.address);
    expect(ownerSessions.length).to.equal(2);
    expect(ownerSessions[0]).to.equal(0n);
    expect(ownerSessions[1]).to.equal(1n);
  });

  // --- Test 6: Multiple agents have separate session lists ---
  it("should separate sessions by agent", async function () {
    await vault.connect(agent1).commitReasoning(inputHash1, reasoningHash1, action1);
    await vault.connect(agent2).commitReasoning(inputHash2, reasoningHash2, action2);
    await vault.connect(agent1).commitReasoning(inputHash3, reasoningHash3, action3);

    const agent1Sessions = await vault.getAgentSessions(agent1.address);
    const agent2Sessions = await vault.getAgentSessions(agent2.address);

    expect(agent1Sessions.length).to.equal(2);
    expect(agent2Sessions.length).to.equal(1);
    expect(agent1Sessions[0]).to.equal(0n);
    expect(agent1Sessions[1]).to.equal(2n);
    expect(agent2Sessions[0]).to.equal(1n);
  });

  // --- Test 7: Revert on zero inputHash ---
  it("should revert when inputHash is zero", async function () {
    await expect(
      vault.commitReasoning(ethers.ZeroHash, reasoningHash1, action1)
    ).to.be.revertedWith("Input hash cannot be zero");
  });

  // --- Test 8: Revert on zero reasoningHash ---
  it("should revert when reasoningHash is zero", async function () {
    await expect(
      vault.commitReasoning(inputHash1, ethers.ZeroHash, action1)
    ).to.be.revertedWith("Reasoning hash cannot be zero");
  });

  // --- Test 9: Revert on empty action ---
  it("should revert when action is empty", async function () {
    await expect(
      vault.commitReasoning(inputHash1, reasoningHash1, "")
    ).to.be.revertedWith("Action cannot be empty");
  });

  // --- Test 10: Revert on verifying non-existent session ---
  it("should revert when verifying a non-existent session", async function () {
    await expect(vault.verifySession(0)).to.be.revertedWith(
      "Session does not exist"
    );

    await vault.commitReasoning(inputHash1, reasoningHash1, action1);
    await expect(vault.verifySession(999)).to.be.revertedWith(
      "Session does not exist"
    );
  });

  // --- Test 11: Event emitted with correct indexed fields ---
  it("should emit ReasoningCommitted event with correct fields", async function () {
    await expect(vault.commitReasoning(inputHash1, reasoningHash1, action1))
      .to.emit(vault, "ReasoningCommitted")
      .withArgs(0n, owner.address, inputHash1, reasoningHash1, action1, (v) => v > 0n);
  });

  // --- Test 12: Agent with no sessions returns empty array ---
  it("should return empty array for agent with no sessions", async function () {
    const sessions = await vault.getAgentSessions(agent1.address);
    expect(sessions.length).to.equal(0);
  });

  // --- Test 13: Duplicate hashes are allowed (separate sessions) ---
  it("should allow duplicate hashes as separate sessions", async function () {
    await vault.commitReasoning(inputHash1, reasoningHash1, action1);
    await vault.commitReasoning(inputHash1, reasoningHash1, action1);

    expect(await vault.totalSessions()).to.equal(2n);

    const s0 = await vault.verifySession(0);
    const s1 = await vault.verifySession(1);
    expect(s0.inputHash).to.equal(s1.inputHash);
    expect(s0.reasoningHash).to.equal(s1.reasoningHash);
  });
});
