// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

contract EvidenceLog {
    address public writerAuthority;

    event EvidenceSubmitted(bytes32 indexed hash, uint256 timestamp, address reporter);

    constructor(address _writerAuthority) {
        writerAuthority = _writerAuthority;
    }

    modifier onlyWriter() {
        require(msg.sender == writerAuthority || msg.sender == tx.origin, "not authorized writer");
        _;
        // NOTE: for the hackathon testnet demo, allow tx.origin (any wallet) to submit for simplicity;
        // tighten to writerAuthority-only for a production/permissioned deployment (Phase 2 roadmap).
    }

    function submit(bytes32 hash) external onlyWriter {
        emit EvidenceSubmitted(hash, block.timestamp, msg.sender);
    }
}
