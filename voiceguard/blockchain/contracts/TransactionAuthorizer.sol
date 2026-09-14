// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import "./IdentityRegistry.sol";
import "./RevocationRegistry.sol";

contract TransactionAuthorizer {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    enum Status { PENDING, ALLOWED, BLOCKED }

    struct GuardedTx {
        bytes32 identityId;
        uint8 requiredApprovals;
        uint8 receivedApprovals;
        bool voiceCheckPassed;
        Status status;
        bool exists;
    }

    mapping(bytes32 => GuardedTx) public transactions;
    mapping(bytes32 => mapping(address => bool)) public hasApproved; // txHash => approver => approved?

    IdentityRegistry public identityRegistry;
    RevocationRegistry public revocationRegistry;
    address public voiceOracle; // backend service authorized to submit the AI voice-check result

    event TransactionProposed(bytes32 indexed txHash, bytes32 identityId, uint8 requiredApprovals);
    event VoiceCheckSubmitted(bytes32 indexed txHash, bool passed);
    event TransactionApproved(bytes32 indexed txHash, address approver);
    event TransactionStatusChanged(bytes32 indexed txHash, Status status);

    constructor(address _identityRegistry, address _revocationRegistry, address _voiceOracle) {
        identityRegistry = IdentityRegistry(_identityRegistry);
        revocationRegistry = RevocationRegistry(_revocationRegistry);
        voiceOracle = _voiceOracle;
    }

    function propose(bytes32 txHash, bytes32 identityId, uint8 requiredApprovals) external {
        require(!transactions[txHash].exists, "already proposed");
        transactions[txHash] = GuardedTx(identityId, requiredApprovals, 0, false, Status.PENDING, true);
        emit TransactionProposed(txHash, identityId, requiredApprovals);
    }

    function submitVoiceCheck(bytes32 txHash, bool passed) external {
        require(msg.sender == voiceOracle, "not authorized oracle");
        require(transactions[txHash].exists, "unknown tx");
        transactions[txHash].voiceCheckPassed = passed;
        emit VoiceCheckSubmitted(txHash, passed);
        _tryFinalize(txHash);
    }

    function approve(bytes32 txHash, bytes calldata signature) external {
        GuardedTx storage t = transactions[txHash];
        require(t.exists, "unknown tx");

        address expectedSigner = identityRegistry.getPubKey(t.identityId);
        bytes32 ethSignedHash = txHash.toEthSignedMessageHash();
        address recovered = ethSignedHash.recover(signature);
        require(recovered == expectedSigner, "signature does not match registered identity");
        require(!hasApproved[txHash][recovered], "already approved by this signer");

        hasApproved[txHash][recovered] = true;
        t.receivedApprovals += 1;
        emit TransactionApproved(txHash, recovered);
        _tryFinalize(txHash);
    }

    function _tryFinalize(bytes32 txHash) internal {
        GuardedTx storage t = transactions[txHash];
        if (t.status != Status.PENDING) return;

        bool identityOk = !revocationRegistry.isRevoked(t.identityId);
        if (t.voiceCheckPassed && t.receivedApprovals >= t.requiredApprovals && identityOk) {
            t.status = Status.ALLOWED;
            emit TransactionStatusChanged(txHash, Status.ALLOWED);
        }
        // status stays PENDING until conditions are met, or can be explicitly timed out/blocked
        // by an admin function in a production version — out of scope for the demo build.
    }

    function status(bytes32 txHash) external view returns (Status) {
        return transactions[txHash].status;
    }
}
