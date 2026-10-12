import { expect } from "chai";
import { ethers } from "hardhat";
import { ProjectRegistry } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("ProjectRegistry", function () {
  let projectRegistry: ProjectRegistry;
  let owner: HardhatEthersSigner;
  let user1: HardhatEthersSigner;
  let user2: HardhatEthersSigner;

  // Sample 32-byte SHA-256 fingerprints (0x followed by 64 hexadecimal characters)
  const sampleFingerprint1 = ethers.sha256(
    ethers.toUtf8Bytes("CodeProof Project 1 - Initial Commit")
  );
  const sampleFingerprint2 = ethers.sha256(
    ethers.toUtf8Bytes("CodeProof Project 2 - Second Repository")
  );
  const unknownFingerprint = ethers.sha256(
    ethers.toUtf8Bytes("Unregistered Codebase")
  );
  const zeroFingerprint = ethers.ZeroHash; // 32 bytes of zeros

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();
    const ProjectRegistryFactory = await ethers.getContractFactory("ProjectRegistry");
    projectRegistry = await ProjectRegistryFactory.deploy();
    await projectRegistry.waitForDeployment();
  });

  describe("Deployment", function () {
    it("should deploy with a valid contract address", async function () {
      const address = await projectRegistry.getAddress();
      expect(address).to.be.properAddress;
      expect(address).to.not.equal(ethers.ZeroAddress);
    });
  });

  describe("Registration", function () {
    it("should successfully register a valid 32-byte fingerprint", async function () {
      const tx = await projectRegistry.connect(user1).registerProject(sampleFingerprint1);
      const receipt = await tx.wait();
      expect(receipt?.status).to.equal(1);

      const isReg = await projectRegistry.isProjectRegistered(sampleFingerprint1);
      expect(isReg).to.be.true;
    });

    it("should emit ProjectRegistered event with matching arguments", async function () {
      const tx = await projectRegistry.connect(user1).registerProject(sampleFingerprint1);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      await expect(tx)
        .to.emit(projectRegistry, "ProjectRegistered")
        .withArgs(sampleFingerprint1, user1.address, block!.timestamp);
    });

    it("should correctly record the caller as owner and current block timestamp", async function () {
      const tx = await projectRegistry.connect(user2).registerProject(sampleFingerprint1);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      const [isReg, regOwner, regTimestamp] = await projectRegistry.verifyProject(sampleFingerprint1);
      expect(isReg).to.be.true;
      expect(regOwner).to.equal(user2.address);
      expect(regTimestamp).to.equal(block!.timestamp);
    });

    it("should reject zero fingerprint (bytes32(0))", async function () {
      await expect(
        projectRegistry.connect(user1).registerProject(zeroFingerprint)
      ).to.be.revertedWith("ProjectRegistry: fingerprint cannot be zero");
    });

    it("should reject duplicate registration of the same fingerprint by the same user", async function () {
      await projectRegistry.connect(user1).registerProject(sampleFingerprint1);

      await expect(
        projectRegistry.connect(user1).registerProject(sampleFingerprint1)
      ).to.be.revertedWith("ProjectRegistry: fingerprint already registered");
    });

    it("should reject duplicate registration of the same fingerprint by a different user", async function () {
      await projectRegistry.connect(user1).registerProject(sampleFingerprint1);

      await expect(
        projectRegistry.connect(user2).registerProject(sampleFingerprint1)
      ).to.be.revertedWith("ProjectRegistry: fingerprint already registered");
    });
  });

  describe("Verification", function () {
    it("should return false, ZeroAddress, and 0 for unknown fingerprints", async function () {
      const [isReg, regOwner, regTimestamp] = await projectRegistry.verifyProject(unknownFingerprint);
      expect(isReg).to.be.false;
      expect(regOwner).to.equal(ethers.ZeroAddress);
      expect(regTimestamp).to.equal(0);

      const isRegHelper = await projectRegistry.isProjectRegistered(unknownFingerprint);
      expect(isRegHelper).to.be.false;
    });

    it("should return true, correct owner, and timestamp for registered fingerprints", async function () {
      const tx = await projectRegistry.connect(user1).registerProject(sampleFingerprint1);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt!.blockNumber);

      const [isReg, regOwner, regTimestamp] = await projectRegistry.verifyProject(sampleFingerprint1);
      expect(isReg).to.be.true;
      expect(regOwner).to.equal(user1.address);
      expect(regTimestamp).to.equal(block!.timestamp);
    });

    it("should maintain independent registrations for multiple distinct fingerprints", async function () {
      // User 1 registers fingerprint 1
      const tx1 = await projectRegistry.connect(user1).registerProject(sampleFingerprint1);
      const receipt1 = await tx1.wait();
      const block1 = await ethers.provider.getBlock(receipt1!.blockNumber);

      // Fast forward time slightly
      await time.increase(100);

      // User 2 registers fingerprint 2
      const tx2 = await projectRegistry.connect(user2).registerProject(sampleFingerprint2);
      const receipt2 = await tx2.wait();
      const block2 = await ethers.provider.getBlock(receipt2!.blockNumber);

      const [isReg1, owner1, time1] = await projectRegistry.verifyProject(sampleFingerprint1);
      const [isReg2, owner2, time2] = await projectRegistry.verifyProject(sampleFingerprint2);

      expect(isReg1).to.be.true;
      expect(owner1).to.equal(user1.address);
      expect(time1).to.equal(block1!.timestamp);

      expect(isReg2).to.be.true;
      expect(owner2).to.equal(user2.address);
      expect(time2).to.equal(block2!.timestamp);

      expect(time2).to.be.greaterThan(time1);
    });
  });

  describe("Fingerprint Format Compliance", function () {
    it("should accept valid 64-hex-character SHA-256 digests prefixed with 0x", async function () {
      const hex64 = "0x" + "a".repeat(64);
      await expect(projectRegistry.connect(user1).registerProject(hex64)).to.not.be.reverted;

      const [isReg, regOwner] = await projectRegistry.verifyProject(hex64);
      expect(isReg).to.be.true;
      expect(regOwner).to.equal(user1.address);
    });
  });
});
