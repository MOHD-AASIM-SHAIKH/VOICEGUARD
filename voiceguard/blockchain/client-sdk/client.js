const { ethers } = require("ethers");
const IdentityRegistryABI = require("../artifacts/contracts/IdentityRegistry.sol/IdentityRegistry.json").abi;
const EvidenceLogABI = require("../artifacts/contracts/EvidenceLog.sol/EvidenceLog.json").abi;
const TransactionAuthorizerABI = require("../artifacts/contracts/TransactionAuthorizer.sol/TransactionAuthorizer.json").abi;
const RevocationRegistryABI = require("../artifacts/contracts/RevocationRegistry.sol/RevocationRegistry.json").abi;

class VoiceGuardChainClient {
  constructor(rpcUrl, privateKey, addresses) {
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
    this.wallet = new ethers.Wallet(privateKey, this.provider);
    this.identityRegistry = new ethers.Contract(addresses.identityRegistry, IdentityRegistryABI, this.wallet);
    this.evidenceLog = new ethers.Contract(addresses.evidenceLog, EvidenceLogABI, this.wallet);
    this.authorizer = new ethers.Contract(addresses.authorizer, TransactionAuthorizerABI, this.wallet);
    this.revocationRegistry = new ethers.Contract(addresses.revocationRegistry, RevocationRegistryABI, this.wallet);
  }

  async writeEvidence(hashHex) {
    const tx = await this.evidenceLog.submit(hashHex);
    return await tx.wait();
  }

  async registerIdentity(identityId, pubKey, kycRef) {
    const tx = await this.identityRegistry.register(identityId, pubKey, kycRef);
    return await tx.wait();
  }

  async submitTransactionIntent(txHash, identityId, requiredApprovals) {
    const tx = await this.authorizer.propose(txHash, identityId, requiredApprovals);
    return await tx.wait();
  }

  async submitVoiceCheck(txHash, passed) {
    const tx = await this.authorizer.submitVoiceCheck(txHash, passed);
    return await tx.wait();
  }

  async approveTransaction(txHash, signature) {
    const tx = await this.authorizer.approve(txHash, signature);
    return await tx.wait();
  }

  async checkAuthorization(txHash) {
    return await this.authorizer.status(txHash); // returns enum: 0=PENDING, 1=ALLOWED, 2=BLOCKED
  }

  async revokeIdentity(identityId, reason) {
    const tx = await this.revocationRegistry.revoke(identityId, reason);
    return await tx.wait();
  }
}

module.exports = VoiceGuardChainClient;
