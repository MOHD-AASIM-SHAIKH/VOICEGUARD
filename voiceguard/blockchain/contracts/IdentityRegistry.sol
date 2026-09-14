// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

contract IdentityRegistry {
    struct Identity {
        address pubKey;
        bytes32 kycRef;
        bool active;
        uint256 registeredAt;
    }

    mapping(bytes32 => Identity) public identities;
    address public onboardingAuthority;

    event IdentityRegistered(bytes32 indexed identityId, address pubKey);

    constructor(address _onboardingAuthority) {
        onboardingAuthority = _onboardingAuthority;
    }

    modifier onlyOnboarder() {
        require(msg.sender == onboardingAuthority, "not authorized onboarder");
        _;
    }

    function register(bytes32 identityId, address pubKey, bytes32 kycRef) external onlyOnboarder {
        require(identities[identityId].registeredAt == 0, "already registered");
        identities[identityId] = Identity(pubKey, kycRef, true, block.timestamp);
        emit IdentityRegistered(identityId, pubKey);
    }

    function isActive(bytes32 identityId) external view returns (bool) {
        return identities[identityId].active;
    }

    function getPubKey(bytes32 identityId) external view returns (address) {
        return identities[identityId].pubKey;
    }
}
