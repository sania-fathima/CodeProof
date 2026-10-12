// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ProjectRegistry
 * @dev On-chain registry for CodeProof project fingerprint verification.
 * Stores only cryptographic SHA-256 project fingerprints (bytes32), registrant wallet address,
 * and blockchain timestamp. Never stores raw source code, filenames, or private user details.
 *
 * NOTE: Blockchain registration proves a fingerprint was recorded at a given time by a
 * specific wallet address, not conclusively who originally authored the source code.
 */
contract ProjectRegistry {
    /// @dev Structure representing project registration metadata on-chain.
    struct ProjectRecord {
        address owner;
        uint256 timestamp;
    }

    /// @dev Mapping from SHA-256 fingerprint (bytes32) to ProjectRecord.
    mapping(bytes32 => ProjectRecord) private _records;

    /**
     * @dev Emitted when a new project fingerprint is registered.
     * @param fingerprint The 32-byte SHA-256 digest of the project.
     * @param owner The wallet address registering the project.
     * @param timestamp The blockchain timestamp (block.timestamp) when registered.
     */
    event ProjectRegistered(
        bytes32 indexed fingerprint,
        address indexed owner,
        uint256 timestamp
    );

    /**
     * @notice Registers a new 32-byte SHA-256 project fingerprint.
     * @dev Rejects zero fingerprints and duplicate registrations.
     * Stores msg.sender as owner and block.timestamp as registration timestamp.
     * @param fingerprint 32-byte SHA-256 hash (0x followed by 64 hexadecimal characters).
     */
    function registerProject(bytes32 fingerprint) external {
        require(fingerprint != bytes32(0), "ProjectRegistry: fingerprint cannot be zero");
        require(_records[fingerprint].timestamp == 0, "ProjectRegistry: fingerprint already registered");

        _records[fingerprint] = ProjectRecord({
            owner: msg.sender,
            timestamp: block.timestamp
        });

        emit ProjectRegistered(fingerprint, msg.sender, block.timestamp);
    }

    /**
     * @notice Verifies registration status, owner address, and timestamp for a fingerprint.
     * @param fingerprint The 32-byte SHA-256 hash to verify.
     * @return isRegistered Boolean indicating if fingerprint exists in the registry.
     * @return owner Address of the wallet that registered the fingerprint (address(0) if unknown).
     * @return timestamp Blockchain block.timestamp when registered (0 if unknown).
     */
    function verifyProject(bytes32 fingerprint)
        external
        view
        returns (
            bool isRegistered,
            address owner,
            uint256 timestamp
        )
    {
        ProjectRecord memory record = _records[fingerprint];
        if (record.timestamp != 0) {
            return (true, record.owner, record.timestamp);
        }
        return (false, address(0), 0);
    }

    /**
     * @notice Checks if a fingerprint is registered.
     * @param fingerprint The 32-byte SHA-256 hash to check.
     * @return Boolean true if registered, false otherwise.
     */
    function isProjectRegistered(bytes32 fingerprint) external view returns (bool) {
        return _records[fingerprint].timestamp != 0;
    }
}
