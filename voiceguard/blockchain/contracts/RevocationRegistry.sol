// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

contract RevocationRegistry {
    mapping(bytes32 => bool) public revoked;
    address public admin;

    event IdentityRevoked(bytes32 indexed identityId, uint256 timestamp, string reason);

    constructor(address _admin) {
        admin = _admin;
    }

    function revoke(bytes32 identityId, string calldata reason) external {
        require(msg.sender == admin, "not authorized");
        revoked[identityId] = true;
        emit IdentityRevoked(identityId, block.timestamp, reason);
    }

    function isRevoked(bytes32 identityId) external view returns (bool) {
        return revoked[identityId];
    }
}
