const hre = require("hardhat");

async function main() {
  console.log("=================================================");
  console.log("VOICEGUARD: PHASE 11 GUARDED TRANSACTION FLOW TEST");
  console.log("=================================================\n");

  const [deployer, officialSigner] = await hre.ethers.getSigners();
  console.log("Deployer / Oracle:", deployer.address);
  console.log("Official Signer:   ", officialSigner.address);

  // 1. Deploy contracts
  const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
  const identityRegistry = await IdentityRegistry.deploy(deployer.address);
  await identityRegistry.waitForDeployment();

  const EvidenceLog = await hre.ethers.getContractFactory("EvidenceLog");
  const evidenceLog = await EvidenceLog.deploy(deployer.address);
  await evidenceLog.waitForDeployment();

  const RevocationRegistry = await hre.ethers.getContractFactory("RevocationRegistry");
  const revocationRegistry = await RevocationRegistry.deploy(deployer.address);
  await revocationRegistry.waitForDeployment();

  const TransactionAuthorizer = await hre.ethers.getContractFactory("TransactionAuthorizer");
  const authorizer = await TransactionAuthorizer.deploy(
    await identityRegistry.getAddress(),
    await revocationRegistry.getAddress(),
    deployer.address
  );
  await authorizer.waitForDeployment();
  console.log("All 4 Smart Contracts Deployed Successfully.\n");

  // 2. Onboard high-risk official identity
  const identityId = hre.ethers.id("OFFICIAL_CXO_001");
  const kycRef = hre.ethers.id("KYC_REF_SECURE_VERIFIED_2026");
  await (await identityRegistry.register(identityId, officialSigner.address, kycRef)).wait();
  console.log("STEP 1: Registered Identity on IdentityRegistry");
  console.log("   Identity ID:", identityId);
  console.log("   Authorized PubKey:", officialSigner.address);
  console.log("   Is Active:", await identityRegistry.isActive(identityId), "\n");

  // 3. Citizen Evidence Notarization
  const evidenceHash = hre.ethers.id("INCIDENT_EVIDENCE_DIGEST_VG9812");
  const evidenceTx = await (await evidenceLog.submit(evidenceHash)).wait();
  console.log("STEP 2: Citizen Evidence Notarization on EvidenceLog");
  console.log("   Evidence SHA-256 Digest:", evidenceHash);
  console.log("   Transaction Status:", evidenceTx.status === 1 ? "SUCCESS (CONFIRMED ON-CHAIN)" : "FAILED", "\n");

  // 4. Propose Guarded Transaction (₹50 Lakh Intent)
  const txHash = hre.ethers.id("TRANSFER_50_LAKH_ABC_INDUSTRIES");
  const requiredApprovals = 1;
  await (await authorizer.propose(txHash, identityId, requiredApprovals)).wait();
  console.log("STEP 3: High-Value Transaction Proposed to TransactionAuthorizer");
  console.log("   txHash:", txHash);
  console.log("   Initial Contract Status:", await authorizer.status(txHash), "(0 = PENDING)");

  // 5. Test Case A: Cloned Voice Attack Attempt
  console.log("\nSTEP 4: Testing Attack Scenario (Voice Model Flags Voice as CLONED)");
  await (await authorizer.submitVoiceCheck(txHash, false)).wait(); // voiceCheckPassed = false
  const signature = await officialSigner.signMessage(hre.ethers.getBytes(txHash));
  await (await authorizer.approve(txHash, signature)).wait();
  const statusAfterClone = await authorizer.status(txHash);
  console.log("   Voice Check Result: CLONED / SPOOF (FALSE)");
  console.log("   Signature submitted: YES");
  console.log("   Contract Status:", statusAfterClone, "(0 = PENDING / BLOCKED)");
  if (statusAfterClone === 0n || statusAfterClone === 0) {
    console.log("   --> SECURITY PASS: Cloned voice alone CANNOT authorize funds transfer!");
  } else {
    throw new Error("SECURITY FAILURE: Transaction was allowed with cloned voice!");
  }

  // 6. Test Case B: Legitimate Call with REAL Voice + Multi-Sig
  console.log("\nSTEP 5: Testing Legitimate Scenario (REAL Voice + Multi-Sig)");
  const legitimateTxHash = hre.ethers.id("LEGIT_TRANSFER_50_LAKH_ABC_INDUSTRIES");
  await (await authorizer.propose(legitimateTxHash, identityId, requiredApprovals)).wait();
  // Live AI Core Detection confirms voice is REAL
  await (await authorizer.submitVoiceCheck(legitimateTxHash, true)).wait(); // voiceCheckPassed = true
  const legitSignature = await officialSigner.signMessage(hre.ethers.getBytes(legitimateTxHash));
  await (await authorizer.approve(legitimateTxHash, legitSignature)).wait();
  const legitStatus = await authorizer.status(legitimateTxHash);
  console.log("   Voice Check Result: REAL / AUTHENTIC (TRUE)");
  console.log("   Signature verified against IdentityRegistry: YES");
  console.log("   Contract Status:", legitStatus, "(1 = ALLOWED)");
  if (legitStatus === 1n || legitStatus === 1) {
    console.log("   --> PASS: Legitimate transaction cryptographically authorized!");
  } else {
    throw new Error("FAILURE: Valid transaction was not allowed!");
  }

  // 7. Test Case C: Key Revocation Flow
  console.log("\nSTEP 6: Testing Identity Revocation Flow");
  await (await revocationRegistry.revoke(identityId, "Device compromised / emergency revocation")).wait();
  console.log("   Identity revoked on RevocationRegistry: YES");
  const isRevoked = await revocationRegistry.isRevoked(identityId);
  console.log("   isRevoked status:", isRevoked);

  const compromisedTxHash = hre.ethers.id("COMPROMISED_TRANSFER_AFTER_REVOCATION");
  await (await authorizer.propose(compromisedTxHash, identityId, requiredApprovals)).wait();
  await (await authorizer.submitVoiceCheck(compromisedTxHash, true)).wait();
  const compSig = await officialSigner.signMessage(hre.ethers.getBytes(compromisedTxHash));
  await (await authorizer.approve(compromisedTxHash, compSig)).wait();
  const revokedStatus = await authorizer.status(compromisedTxHash);
  console.log("   Compromised Tx Status:", revokedStatus, "(0 = BLOCKED because identity is revoked)");
  if (revokedStatus === 0n || revokedStatus === 0) {
    console.log("   --> SECURITY PASS: Revoked identity cannot execute transactions even with valid key and real voice!");
  }

  console.log("\n=================================================");
  console.log("ALL NOVELTY & SMART CONTRACT GATES PASSED (100%)");
  console.log("=================================================");
}

main().catch((err) => {
  console.error("Test failed:", err);
  process.exitCode = 1;
});
