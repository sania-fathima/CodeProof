# CodeProof — Blockchain Module (`ProjectRegistry`)

The blockchain module provides an immutable, decentralized registry for recording and verifying cryptographic fingerprints of software projects on an EVM-compatible blockchain.

---

## Table of Contents

- [Overview](#overview)
- [Smart Contract Specification](#smart-contract-specification)
  - [Contract Identity](#contract-identity)
  - [Data Structures](#data-structures)
  - [Functions](#functions)
  - [Events](#events)
  - [Errors and Validation](#errors-and-validation)
- [Coordination Facts for `docs/API_CONTRACT.md`](#coordination-facts-for-docsapi_contractmd)
- [Project Setup and Commands](#project-setup-and-commands)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Compilation](#compilation)
  - [Testing](#testing)
  - [Local Deployment](#local-deployment)
- [Obtaining Contract Address and ABI](#obtaining-contract-address-and-abi)
- [Security and Authorship Notice](#security-and-authorship-notice)

---

## Overview

The `ProjectRegistry` contract is designed specifically for the CodeProof architecture:
1. **Cryptographic Fingerprint Registration:** Takes a 32-byte SHA-256 hash (`bytes32`) representing a project's contents.
2. **Provenance Metadata:** Anchors the caller's wallet address (`msg.sender`) and the block timestamp (`block.timestamp`).
3. **No Sensitive Data Stored:** Absolutely no raw source code, filenames, author names, or private personal data are stored on-chain.
4. **Duplicate & Zero Prevention:** Rejects zero-hash fingerprints (`bytes32(0)`) and any attempt to re-register an existing fingerprint.

---

## Smart Contract Specification

### Contract Identity

- **Name:** `ProjectRegistry`
- **Solidity Version:** `^0.8.24`
- **EVM Target:** `paris` / default EVM
- **Source File:** `contracts/ProjectRegistry.sol`
- **License:** MIT

### Data Structures

```solidity
struct ProjectRecord {
    address owner;      // Registering wallet address (msg.sender)
    uint256 timestamp;  // Blockchain timestamp of registration (block.timestamp)
}
```

- **Storage Mapping:** `mapping(bytes32 => ProjectRecord) private _records;`

### Functions

#### 1. `registerProject(bytes32 fingerprint)`
- **Visibility:** `external`
- **State Mutability:** Non-payable (writes state)
- **Parameters:**
  - `fingerprint` (`bytes32`): 32-byte SHA-256 fingerprint formatted as `0x` followed by 64 hexadecimal characters.
- **Behavior:**
  - Reverts if `fingerprint == bytes32(0)`.
  - Reverts if `_records[fingerprint].timestamp != 0` (duplicate check).
  - Sets `_records[fingerprint]` with `owner = msg.sender` and `timestamp = block.timestamp`.
  - Emits `ProjectRegistered(fingerprint, msg.sender, block.timestamp)`.
- **Return Value:** None (`void`).

#### 2. `verifyProject(bytes32 fingerprint)`
- **Visibility:** `external view`
- **State Mutability:** View (does not consume gas when called off-chain)
- **Parameters:**
  - `fingerprint` (`bytes32`): 32-byte SHA-256 fingerprint to look up.
- **Return Values:**
  - `isRegistered` (`bool`): `true` if registered, `false` otherwise.
  - `owner` (`address`): Wallet address of the registrant (`address(0)` if unregistered).
  - `timestamp` (`uint256`): Blockchain timestamp when registered (`0` if unregistered).

#### 3. `isProjectRegistered(bytes32 fingerprint)`
- **Visibility:** `external view`
- **State Mutability:** View
- **Parameters:**
  - `fingerprint` (`bytes32`): 32-byte SHA-256 fingerprint to check.
- **Return Values:**
  - `bool`: `true` if fingerprint is found in the registry, `false` otherwise.

### Events

#### `ProjectRegistered`
```solidity
event ProjectRegistered(
    bytes32 indexed fingerprint,
    address indexed owner,
    uint256 timestamp
);
```
- Emitted in transaction logs upon every successful registration.
- Indexed topics: `fingerprint` (topic 1) and `owner` (topic 2).

### Errors and Validation

The contract uses explicit require error messages:
- `"ProjectRegistry: fingerprint cannot be zero"` — when `fingerprint == bytes32(0)`
- `"ProjectRegistry: fingerprint already registered"` — when fingerprint has already been recorded

---

## Coordination Facts for `docs/API_CONTRACT.md`

> **Note to Repository Owner:**
> Use these exact specifications when authoring or updating `docs/API_CONTRACT.md`.

| Parameter / Field | Type | Format / Constraints |
|---|---|---|
| Fingerprint | `bytes32` (Solidity) / `string` (API/JSON) | Hex string starting with `0x` followed by exactly 64 hexadecimal characters (`^[0-9a-fA-F]{64}$`). E.g. `0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d` |
| Registrant Wallet | `address` (Solidity) / `string` (API/JSON) | Checksummed Ethereum address (`0x` + 40 hex characters) |
| Registration Timestamp | `uint256` (Solidity) / `number` or `string` | Unix epoch time in seconds (`block.timestamp`) |
| Registration Status | `bool` | `true` or `false` |

### Solidity ABI JSON
The canonical ABI is exported to:
- `blockchain/abi/ProjectRegistry.json`
- `blockchain/artifacts/contracts/ProjectRegistry.sol/ProjectRegistry.json`

---

## Project Setup and Commands

### Prerequisites
- Node.js >= 18 (Tested on Node.js v24.16.0)
- npm >= 9 (Tested on npm 11.13.0)

### Installation
From the `blockchain/` directory:
```bash
npm install
```

### Compilation
Compiles the Solidity contract and generates TypeScript typings:
```bash
npm run compile
```

### Testing
Executes the automated Hardhat test suite in `test/ProjectRegistry.test.ts`:
```bash
npm test
```

**Test Coverage Summary:**
- Contract deployment and valid address creation
- Successful project fingerprint registration
- Emitting `ProjectRegistered` event with exact indexed arguments
- Rejection of zero fingerprints (`bytes32(0)`)
- Rejection of duplicate registration by original owner
- Rejection of duplicate registration by a different user
- Verification of unknown fingerprints (returns `false`, `0x00...00`, `0`)
- Verification of known fingerprints (returns `true`, registrant address, timestamp)
- Independent multi-user, multi-project registrations with distinct timestamps
- Verification of 64-hex SHA-256 fingerprint format compliance

### Local Deployment

1. **Option A: Deploy to ephemeral in-memory Hardhat network**
   ```bash
   npx hardhat run scripts/deploy.ts
   ```

2. **Option B: Deploy to persistent local Hardhat node**
   In terminal 1, start the node:
   ```bash
   npm run node
   ```
   In terminal 2, run the deployment script:
   ```bash
   npm run deploy:local
   ```

---

## Obtaining Contract Address and ABI

When running `scripts/deploy.ts`, the deployment process automatically produces:
1. **Console Output:**
   ```text
   Contract Address: 0x5FbDB2315678afecb367f032d93F642f64180aa3
   Transaction Hash: 0x...
   Block Number:     1
   ```
2. **Exported ABI:**
   `blockchain/abi/ProjectRegistry.json` contains the array of ABI items ready for direct import in Python (`backend/`) via `json.load()` or React (`frontend/`) via `import`.
3. **Deployment Metadata File:**
   `blockchain/deployments/<network>.json` records the contract address, deployer, network, chainId, and timestamp.

---

## Security and Authorship Notice

> [!IMPORTANT]
> **Authorship vs. Timestamping Limitation**
> Blockchain registration cryptographically guarantees that a specific 32-byte fingerprint existed and was anchored by a specific wallet address at or before a given block timestamp (`block.timestamp`).
> It **does not** conclusively prove that the registering wallet originally authored the source code from which the fingerprint was generated (an actor could compute the fingerprint of another party's publicly available code and submit it first). CodeProof relies on combining on-chain timestamp priority with off-chain AI-assisted similarity analysis and platform verification logic to establish credibility and detect plagiarism.

> [!CAUTION]
> **Key Management and Production Guardrails**
> - Never commit `.env` files, mnemonic seeds, or private keys to version control.
> - Never deploy to public testnets or mainnets without authorization and security review.
> - No real cryptocurrency funds should be used during local development.
