import { ethers, network } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log("==================================================");
  console.log("CodeProof — Deploying ProjectRegistry Contract");
  console.log("==================================================");

  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);

  console.log(`Network:          ${network.name} (Chain ID: ${network.config.chainId ?? "auto"})`);
  console.log(`Deployer address: ${deployer.address}`);
  console.log(`Deployer balance: ${ethers.formatEther(balance)} ETH`);

  // Deploy ProjectRegistry
  const ProjectRegistryFactory = await ethers.getContractFactory("ProjectRegistry");
  console.log("Deploying ProjectRegistry...");
  const projectRegistry = await ProjectRegistryFactory.deploy();

  await projectRegistry.waitForDeployment();
  const deployedAddress = await projectRegistry.getAddress();
  const deployTx = projectRegistry.deploymentTransaction();

  console.log("--------------------------------------------------");
  console.log(`✓ ProjectRegistry deployed successfully!`);
  console.log(`Contract Address: ${deployedAddress}`);
  if (deployTx) {
    console.log(`Transaction Hash: ${deployTx.hash}`);
    const receipt = await deployTx.wait();
    console.log(`Block Number:     ${receipt?.blockNumber}`);
    console.log(`Gas Used:         ${receipt?.gasUsed.toString()}`);
  }
  console.log("--------------------------------------------------");

  // Extract ABI from Hardhat artifact
  const artifactPath = path.join(
    __dirname,
    "../artifacts/contracts/ProjectRegistry.sol/ProjectRegistry.json"
  );
  let abi = [];
  if (fs.existsSync(artifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf-8"));
    abi = artifact.abi;
  }

  // Export clean ABI to blockchain/abi/ProjectRegistry.json
  const abiDir = path.join(__dirname, "../abi");
  if (!fs.existsSync(abiDir)) {
    fs.mkdirSync(abiDir, { recursive: true });
  }
  const abiFilePath = path.join(abiDir, "ProjectRegistry.json");
  fs.writeFileSync(abiFilePath, JSON.stringify(abi, null, 2), "utf-8");
  console.log(`✓ ABI exported to: ${path.relative(process.cwd(), abiFilePath)}`);

  // Save deployment metadata to blockchain/deployments/<network>.json
  const deploymentsDir = path.join(__dirname, "../deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  const deploymentData = {
    contractName: "ProjectRegistry",
    address: deployedAddress,
    network: network.name,
    chainId: network.config.chainId ?? 31337,
    deployer: deployer.address,
    transactionHash: deployTx?.hash ?? null,
    deployedAt: new Date().toISOString(),
    abi,
  };

  const deploymentFilePath = path.join(deploymentsDir, `${network.name}.json`);
  fs.writeFileSync(deploymentFilePath, JSON.stringify(deploymentData, null, 2), "utf-8");
  console.log(`✓ Deployment metadata saved to: ${path.relative(process.cwd(), deploymentFilePath)}`);

  console.log("==================================================");
  console.log("Deployment complete. To use this in backend/frontend:");
  console.log(`Contract Address: ${deployedAddress}`);
  console.log("==================================================");
}

main().catch((error) => {
  console.error("Deployment failed:", error);
  process.exitCode = 1;
});
