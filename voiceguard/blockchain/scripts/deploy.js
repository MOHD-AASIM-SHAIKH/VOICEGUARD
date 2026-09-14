const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
  const identityRegistry = await IdentityRegistry.deploy(deployer.address);
  await identityRegistry.waitForDeployment();
  console.log("IdentityRegistry:", await identityRegistry.getAddress());

  const EvidenceLog = await hre.ethers.getContractFactory("EvidenceLog");
  const evidenceLog = await EvidenceLog.deploy(deployer.address);
  await evidenceLog.waitForDeployment();
  console.log("EvidenceLog:", await evidenceLog.getAddress());

  const RevocationRegistry = await hre.ethers.getContractFactory("RevocationRegistry");
  const revocationRegistry = await RevocationRegistry.deploy(deployer.address);
  await revocationRegistry.waitForDeployment();
  console.log("RevocationRegistry:", await revocationRegistry.getAddress());

  const TransactionAuthorizer = await hre.ethers.getContractFactory("TransactionAuthorizer");
  const authorizer = await TransactionAuthorizer.deploy(
    await identityRegistry.getAddress(),
    await revocationRegistry.getAddress(),
    deployer.address // deployer also acts as the voice-oracle backend for the demo
  );
  await authorizer.waitForDeployment();
  console.log("TransactionAuthorizer:", await authorizer.getAddress());

  console.log("\n--- COPY THESE ADDRESSES INTO client-sdk/addresses.json ---");
  console.log(JSON.stringify({
    identityRegistry: await identityRegistry.getAddress(),
    evidenceLog: await evidenceLog.getAddress(),
    revocationRegistry: await revocationRegistry.getAddress(),
    authorizer: await authorizer.getAddress()
  }, null, 2));
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
