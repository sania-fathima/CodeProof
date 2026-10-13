# CodeProof — Shared API Contract Specification

> **Version:** `1.1.0-draft`
> **Status:** Architecture Reference & Specification (Under Active Development)
> **Modules Covered:** FastAPI Backend, React Frontend, AI Similarity Detector, Blockchain (`ProjectRegistry`)
> **Governance Note:** Items derived directly from active repository code ([`blockchain/contracts/ProjectRegistry.sol`](file:///c:/presidency/CodeProof/blockchain/contracts/ProjectRegistry.sol), [`blockchain/README.md`](file:///c:/presidency/CodeProof/blockchain/README.md), [`README.md`](file:///c:/presidency/CodeProof/README.md)) represent **Verified Implementation Details**. All architectural workflows, database schemas, and endpoints not yet committed in implementation code are explicitly designated as **`[PROPOSAL - NOT YET IMPLEMENTED - REQUIRES TEAM AGREEMENT]`**.

---

## 1. Scope and Core Architecture Principles

CodeProof provides a decentralized project ownership verification and AI-assisted code similarity detection platform:
1. **Cryptographic Fingerprinting:** Projects are converted off-chain into a deterministic 32-byte SHA-256 digest (`bytes32`), formatted in hex as `0x` followed by 64 hexadecimal characters.
2. **On-Chain Immutability:** The smart contract stores only the 32-byte fingerprint, the registering wallet address, and the blockchain timestamp.
3. **Strict Data Minimization:** **No raw source code, repository files, author names, or private credentials are ever stored on-chain.**
4. **Authorship vs. Timestamping Limitation:** On-chain registration cryptographically proves that a fingerprint existed and was anchored by a specific wallet at a given block timestamp (`block.timestamp`). It **does not prove original authorship** of the underlying source code (an unauthorized actor could compute the fingerprint of external or public code).
5. **AI Detection Role:** The AI detector computes structural and syntactic similarity scores between codebases. Similarity is an **algorithmic indicator of overlap, not conclusive proof of plagiarism**.
6. **Implementation Status:** The `ProjectRegistry.sol` smart contract is implemented and tested with Hardhat. The AI detector's Phase 1 Python/Java similarity baseline is implemented and tested, with a standard-library-only runtime and `pytest` development dependency. The detector currently exposes a Python function (`analyze_submissions`), not a standalone HTTP service. The FastAPI backend, React frontend, PostgreSQL integration, and detector-to-backend orchestration must be verified against their respective module implementations before being described as implemented. The REST endpoints and asynchronous analysis workflows in this document remain proposals until implemented and agreed upon by the team.

```mermaid
flowchart LR
    Frontend["React Frontend\n(Client Web3 Wallet)"] <-->|REST JSON / HTTP| Backend["FastAPI Backend\n[PROPOSAL]"]
    Frontend <-->|Direct RPC Signing\n(EIP-1193)| Blockchain["ProjectRegistry (EVM)\n[VERIFIED]"]
    Backend <-->|Web3 RPC / View Calls| Blockchain
    Backend <-->|Python function call (Phase 1)| AIDetector["AI Detector (Python/Java baseline)\n[IMPLEMENTED: LIBRARY]\n[HTTP INTEGRATION: PROPOSAL]"]
    Backend <-->|SQL| Database[("PostgreSQL DB\n[PROPOSAL]")]
```

---

## 2. Global Standards and Conventions

### 2.1 Base Path and Content Type
- **Base URL:** `/api/v1`
- **Request Content-Type:** `application/json` (or `multipart/form-data` for validated ZIP archive uploads)
- **Response Content-Type:** `application/json`

### 2.2 Canonical Field Formats & Standardized Names

| Standardized Name | Type | Format / Constraints | Description | Implementation Status |
|---|---|---|---|---|
| `project_id` | `string` | UUIDv4 (`^[0-9a-fA-F-]{36}$`) | Platform-unique identifier for a database project record | `[PROPOSAL]` |
| `project_fingerprint` | `string` | `^0x[0-9a-fA-F]{64}$` | 32-byte SHA-256 digest prefixed with `0x` (case-insensitive input, normalized to lowercase) | **Verified** in Solidity (`bytes32`) |
| `owner_wallet_address`| `string` | `^0x[0-9a-fA-F]{40}$` | 20-byte checksummed Ethereum address (`msg.sender` on-chain) | **Verified** in Solidity (`address`) |
| `transaction_hash` | `string` \| `null` | `^0x[0-9a-fA-F]{64}$` | Blockchain transaction hash (32-byte hex string) | `[PROPOSAL]` (tracked off-chain) |
| `block_number` | `integer` \| `null` | `>= 0` | EVM block height containing confirmed transaction | `[PROPOSAL]` (cached off-chain) |
| `block_timestamp` | `integer` \| `null` | Unix epoch seconds | Timestamp recorded by the EVM miner (`block.timestamp`) | **Verified** in Solidity (`uint256`) |
| `created_at` | `string` | ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) | Database record creation timestamp | `[PROPOSAL]` |
| `confirmed_at` | `string` \| `null` | ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) | Timestamp when transaction was confirmed on-chain | `[PROPOSAL]` |
| `registration_status` | `string` | Enum: `PENDING`, `CONFIRMED`, `FAILED`, `UNREGISTERED` | Lifecycle status of project registration | `[PROPOSAL]` |
| `failure_reason` | `string` \| `null` | Max 500 characters | Human-readable explanation when `registration_status == FAILED` | `[PROPOSAL]` |
| `analysis_id` | `string` | UUIDv4 (`^[0-9a-fA-F-]{36}$`) | Platform-unique identifier for a similarity analysis job | `[PROPOSAL]` |
| `analysis_status` | `string` | Enum: `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED` | Lifecycle status of AI similarity analysis | `[PROPOSAL]` |
| `sensitivity_threshold`| `number` | Float `0.0` to `1.0` (inclusive), default `0.30` | Minimum similarity threshold reported by AI detector | `[PROPOSAL]` |
| `similarity_percentage`| `number` \| `null` | Float `0.0` to `100.0` (inclusive) | Overall similarity score computed by AI detector | `[PROPOSAL]` |
| `exact_matches` | `array` | List of `string` | Identifiers or fingerprints exhibiting 100% hash identity | `[PROPOSAL]` |
| `match_results` | `array` | List of `MatchResultEntry` | Granular similarity breakdown against database corpus | `[PROPOSAL]` |

### 2.2.1 Fingerprint Normalization and Validation Specification `[PROPOSAL - NOT YET IMPLEMENTED]`

To ensure deterministic duplicate prevention and uniform data handling across the React frontend, FastAPI backend, PostgreSQL database, and EVM blockchain:

1. **Input Format & Acceptance:**
   - The API accepts `project_fingerprint` formatted strictly as `0x` followed by exactly 64 hexadecimal characters matching the regular expression `^0x[0-9a-fA-F]{64}$`.
   - Both uppercase (`A-F`) and lowercase (`a-f`) hexadecimal characters are accepted in client requests.

2. **API Boundary Normalization:**
   - At the API boundary (e.g., Pydantic schema validation in FastAPI), the future backend **must** normalize the fingerprint to lowercase while strictly preserving the `0x` prefix:
     ```python
     # Proposed Pydantic validator logic:
     normalized_fingerprint = "0x" + raw_fingerprint[2:].lower()
     ```
   - This normalization must occur **prior to** database persistence, database queries, or blockchain RPC interactions.

3. **Consistent Endpoint Handling:**
   - The normalized lowercase value must be used consistently across all registration and verification workflows:
     - `POST /api/v1/projects/register` (stored in database and verified against mempool/chain)
     - `GET /api/v1/projects/{project_id}` (retrieved and returned in normalized form)
     - `POST /api/v1/projects/verify` (used for read-only view calls and response payload)
     - `POST /api/v1/analysis` & `GET /api/v1/analysis/{analysis_id}` (used for exact hash matching)

4. **Acceptance & Normalization Examples:**
   The table below illustrates how different input casings normalize to the exact same canonical fingerprint:

   | Raw Client Input | Normalized Value | Normalization Effect |
   |---|---|---|
   | `0xABCD1234EF56...` | `0xabcd1234ef56...` | Uppercase hex normalized to canonical lowercase |
   | `0xabcd1234ef56...` | `0xabcd1234ef56...` | Lowercase hex preserved identically |
   | `0xAbCd1234Ef56...` | `0xabcd1234ef56...` | Mixed-case hex normalized to canonical lowercase |

   > **Note:** The values in the table above are illustrative shortened examples for readability. Valid production fingerprints must always contain exactly 64 hexadecimal characters after the `0x` prefix (66 characters total).

---

### 2.3 Registration Lifecycle & State Synchronization Distinction

A critical architectural distinction exists between **backend-tracked state** and **actual on-chain state**:

```
                  Client Signs & Broadcasts
                           │
                           ▼
[UNREGISTERED] ──────► [PENDING] ──────► [CONFIRMED] (receipt.status == 1)
                           │
                           └───────────► [FAILED]    (receipt.status == 0 / dropped)
```

#### 2.3.1 Core Lifecycle Terminology Definition
To avoid ambiguity across the API contract, background worker, and blockchain module, the following lifecycle terms are precisely distinguished:
- **`MINED`:** The transaction has an observable receipt in an EVM block (`receipt != null`, with status 1 or 0). A mined transaction is not yet guaranteed to be reorganization-safe or final.
- **`CONFIRMED`:** The transaction has passed all mutual consistency checks (receipt status 1, canonical block hash match, target registry, sender, calldata, event topics, registration block timestamp, and committed contract state) and has satisfied the configured network-specific confirmation policy (`CONFIRMATION_DEPTH` or `finalized` block tag).
- **`FINALIZED`:** The transaction's canonical block is irreversible according to the network's supported finality mechanism (e.g. PoS checkpoint finality via the `finalized` block tag, L1 settlement for rollups, or local development instant finality).

#### 2.3.2 API Lifecycle States (`registration_status` Enum Meaning)
The API preserves the existing four-state lifecycle enum (`UNREGISTERED`, `PENDING`, `CONFIRMED`, `FAILED`):
1. **`UNREGISTERED`:** The fingerprint has never been submitted or mined on-chain.
2. **`PENDING` (Submitted / Unconfirmed Transaction):**
   - The client wallet has signed and broadcast the transaction to the EVM mempool.
   - The transaction has an assigned `transaction_hash`.
   - `block_number` and `block_timestamp` are `null`.
   - Direct on-chain query `verifyProject(bytes32)` returns `is_registered: false` / `registration_status: "UNREGISTERED"` until the transaction is mined into a block.
3. **`CONFIRMED` (Policy-Confirmed / Finalized Registration):**
   - The transaction is `MINED` with `receipt.status == 1`.
   - **Contract & API Meaning:** In the four-state API enum, `registration_status: "CONFIRMED"` signifies that the registration is **policy-confirmed**:
     - On networks configured for PoS finality (e.g. Ethereum Mainnet/Sepolia), `CONFIRMED` requires **protocol-finalization** (both `receipt.blockNumber <= finalized_block.number` and canonical block hash match).
     - On probabilistic chains without protocol finality tags, `CONFIRMED` represents **policy-confirmation** at the configured block depth (`CONFIRMATION_DEPTH`).
     - In read verification (`POST /api/v1/projects/verify`), `CONFIRMED` denotes that the fingerprint is confirmed in mined contract storage (`verifyProject` returns `isRegistered == true`).
   - All 8 mutual consistency checks pass on the same mined transaction and canonical block.
   - `block_number` and `block_timestamp` are populated from the mined canonical registration block header.
   - `failure_reason` is `null`.
   - *Reorganization Protection:* On networks without protocol finality, if a block is reorganized out before finality, the status reverts to `PENDING` for re-verification.
4. **`FAILED` (Terminal Failure or Nonterminal Operational Timeout):**
   - The API distinguishes between two fundamentally different causes of `FAILED`:
     - **Objectively Terminal Failure:** The transaction definitively cannot succeed:
       - The transaction was mined into a canonical block but reverted on-chain (`receipt.status == 0`).
       - The transaction's nonce was irreversibly consumed by a different mined canonical transaction (`sender_nonce > tx.nonce` and verified not to be a registration of this fingerprint).
       *Permanence:* These terminal states are irreversible on-chain.
     - **Nonterminal Operational Timeout:** The transaction remained unmined and absent from observed mempools past `MAX_PENDING_TIMEOUT` (`sender_nonce <= tx.nonce`).
       *Nonterminal Nature & Reconciliation:* An operational timeout does not prove the transaction can never be mined. It is an operational expiry state, NOT an irreversible protocol failure. The record may be reconciled back to `PENDING` (if resubmitted by the client or re-observed in mempools) or directly to `CONFIRMED` (if late mining evidence confirms canonical inclusion).
   - `failure_reason` indicates the specific cause (revert message vs. operational timeout). Frontend interfaces and API documentation must **not** imply that every `FAILED` status represents a permanently impossible registration.

### 2.3.3 Data Trust Classification (On-Chain Truth vs. Off-Chain Metadata) `[PROPOSAL - NOT YET IMPLEMENTED]`

To ensure security, auditability, and clear separation of concerns, the API distinguishes between consensus-verified blockchain data and untrusted user-supplied metadata:

| Field Name | Source / Trust Level | Verification Mechanism | Storage Location |
|---|---|---|---|
| `project_fingerprint` | **Cryptographically Trusted** | Validated against EVM transaction calldata (`tx.input`), verified event log topic1, and contract view query `verifyProject`. | Smart Contract & PostgreSQL |
| `owner_wallet_address` | **Cryptographically Trusted** | Derived strictly from transaction signer (`tx.from` / `msg.sender`) and verified event log topic2. Never trusted from unverified client JSON. | Smart Contract & PostgreSQL |
| `block_number` | **Consensus Trusted** | Extracted from mined EVM block header via receipt (`receipt.blockNumber`). | PostgreSQL (cached) |
| `block_timestamp` | **Consensus Trusted** | Extracted from mined EVM registration block header (`receipt.blockNumber`) and verified against contract state and event log. | Smart Contract & PostgreSQL |
| `registration_status` | **Verified Lifecycle State** | Computed from confirmed transaction receipt status, event emission, and contract verification query. | PostgreSQL |
| `project_name` | **Untrusted User Metadata** | Client-supplied string. Not stored or verified on blockchain. | PostgreSQL Only |
| `description` | **Untrusted User Metadata** | Client-supplied string. Not stored or verified on blockchain. | PostgreSQL Only |
| `created_at` | **Backend Server Metadata** | Timestamp recorded by the FastAPI backend when registration request is received. | PostgreSQL Only |

---

### 2.4 Standard Error Response Schema
All endpoints return errors adhering to this uniform schema:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid project fingerprint supplied.",
    "details": [
      {
        "field": "project_fingerprint",
        "issue": "Must be 0x followed by exactly 64 hexadecimal characters."
      }
    ],
    "timestamp": "2026-10-12T12:00:00Z"
  }
}
```

#### Standard Error Codes:
- `VALIDATION_ERROR` (HTTP 400 / 422) — Malformed request body, invalid field format, or constraint failure.
- `DUPLICATE_FINGERPRINT` (HTTP 409) — Fingerprint already exists in CodeProof database.
- `TRANSACTION_NOT_FOUND` (HTTP 400) — Transaction hash not found in mempool or RPC provider.
- `WALLET_MISMATCH` (HTTP 400) — Transaction signer (`from`) does not match supplied `owner_wallet_address`.
- `INVALID_TARGET_CONTRACT` (HTTP 400) — Transaction destination (`to`) does not match configured `PROJECT_REGISTRY_ADDRESS`.
- `INVALID_FUNCTION_CALL` (HTTP 400) — Transaction calldata does not invoke `registerProject(bytes32)` (`0x21897cdd`).
- `FINGERPRINT_MISMATCH` (HTTP 400) — Transaction calldata parameter does not match supplied `project_fingerprint`.
- `CHAIN_ID_MISMATCH` (HTTP 400) — Transaction was broadcast on an unexpected chain ID.
- `BLOCKCHAIN_RPC_UNAVAILABLE` (HTTP 503) — Connection failure, timeout, or rate-limiting to the EVM RPC node.
- `RESOURCE_NOT_FOUND` (HTTP 404) — Requested project or analysis ID not found.
- `PAYLOAD_TOO_LARGE` (HTTP 413) — Uploaded archive exceeds size limits (10 MB compressed / 50 MB extracted).
- `RATE_LIMIT_EXCEEDED` (HTTP 429) — Too many requests within rate limit window.
- `INTERNAL_SERVER_ERROR` (HTTP 500) — Unexpected backend server failure.

---

## 3. Endpoints Specification

### 3.1 `GET /api/v1/health`
Checks operational readiness and connectivity to dependent infrastructure (PostgreSQL database, Blockchain RPC node, AI detector worker).

- **Method:** `GET`
- **Authentication:** None
- **Request Parameters / Body:** None

#### Response: `200 OK`
```json
{
  "status": "HEALTHY",
  "version": "1.0.0",
  "timestamp": "2026-10-12T12:00:00Z",
  "dependencies": {
    "database": {
      "status": "UP",
      "latency_ms": 4
    },
    "blockchain_rpc": {
      "status": "UP",
      "network": "localhost",
      "chain_id": 31337,
      "contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
      "latency_ms": 12
    },
    "ai_detector": {
      "status": "UP",
      "latency_ms": 8
    }
  }
}
```

#### Response: `503 Service Unavailable`
```json
{
  "status": "DEGRADED",
  "version": "1.0.0",
  "timestamp": "2026-10-12T12:00:00Z",
  "dependencies": {
    "database": { "status": "UP", "latency_ms": 5 },
    "blockchain_rpc": { "status": "DOWN", "error": "Connection refused at http://127.0.0.1:8545" },
    "ai_detector": { "status": "UP", "latency_ms": 10 }
  }
}
```

---

### 3.2 `POST /api/v1/projects/register`
Records a project registration submission and indexes it for off-chain monitoring.

> **Client Signing and Verification Model `[PROPOSAL - INITIAL VERSION]`:**
> The smart contract `ProjectRegistry.sol` strictly records `msg.sender` as the on-chain owner:
> `_records[fingerprint] = ProjectRecord({ owner: msg.sender, timestamp: block.timestamp });`
>
> **1. Client-Side Workflow (MetaMask / EIP-1193):**
> - The React frontend connects to the client's Web3 wallet provider (`window.ethereum`).
> - The frontend verifies that the connected chain ID matches the configured target network (e.g., `31337` for local Hardhat node). If mismatched, it prompts a network switch via `wallet_switchEthereumChain`.
> - The frontend verifies that the destination contract address matches the configured `PROJECT_REGISTRY_ADDRESS`.
> - The user signs and broadcasts the `registerProject(fingerprint)` transaction directly from their wallet.
> - The wallet provider returns the `transaction_hash` immediately upon mempool broadcast (`eth_sendTransaction`).
> - **The frontend submits the `transaction_hash` immediately to `POST /api/v1/projects/register` without waiting for block mining (`await tx.wait()`).**
>
> **2. Independent Backend Validation (Synchronous Intake Checks):**
> Before accepting the submission and returning `202 Accepted`, the future FastAPI backend must independently validate:
> - **Hash Format:** Validates `transaction_hash` matches regex `^0x[0-9a-fA-F]{64}$`.
> - **Fingerprint Normalization:** Normalizes `project_fingerprint` to canonical lowercase `0x` + 64 hex characters.
> - **RPC Query:** Retrieves the pending transaction object via `eth_getTransactionByHash(transaction_hash)`.
> - **RPC Availability:** If the RPC node times out or fails, returns `503 Service Unavailable` (`BLOCKCHAIN_RPC_UNAVAILABLE`).
> - **Mempool Presence:** Verifies transaction presence in mempool. If not immediately found, allows a short intake retry window (2-3 seconds) to tolerate cross-node propagation between client wallet and backend RPC before returning `400 Bad Request` (`TRANSACTION_NOT_FOUND`).
> - **Chain ID Validation:** Verifies the transaction was broadcast on the configured EVM chain ID (`CHAIN_ID_MISMATCH`).
> - **Sender / Owner Match:** Validates `tx.from.lower() == owner_wallet_address.lower()`. Never trusts client-supplied owner address without matching `tx.from` (`WALLET_MISMATCH`).
> - **Destination Contract Match:** Validates `tx.to.lower() == CONFIG.PROJECT_REGISTRY_ADDRESS.lower()` (`INVALID_TARGET_CONTRACT`).
> - **Function Selector Match:** Validates that `tx.input` starts with `0x21897cdd` (`registerProject(bytes32)` selector) (`INVALID_FUNCTION_CALL`).
> - **Calldata Fingerprint Match:** Validates that `tx.input[10:].lower() == normalized_fingerprint[2:].lower()` (`FINGERPRINT_MISMATCH`).
> - **Database Uniqueness Check:** Checks local database for existing normalized fingerprint (`DUPLICATE_FINGERPRINT`).

- **Method:** `POST`
- **Request Headers:** `Content-Type: application/json`

#### Request Body
| Field | Type | Required | Constraints / Validation | Description |
|---|---|---|---|---|
| `project_name` | `string` | Yes | 1 - 100 characters, trimmed | Human-readable project title (untrusted metadata) |
| `project_fingerprint` | `string` | Yes | `^0x[0-9a-fA-F]{64}$` | 32-byte SHA-256 hash. Case-insensitive input. |
| `transaction_hash` | `string` | Yes | `^0x[0-9a-fA-F]{64}$` | Broadcast transaction hash produced by client wallet |
| `owner_wallet_address` | `string` | Yes | `^0x[0-9a-fA-F]{40}$` | Client wallet address that signed the transaction (`tx.from`) |
| `description` | `string` | No | Max 1000 characters | Optional project summary (untrusted metadata) |

```json
{
  "project_name": "CodeProof Core Engine",
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
  "transaction_hash": "0x8a927c385ad3f0e8f7a6358db8ce37fbcf24e05b5505c2a11b7d5fb0ec19672e",
  "owner_wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "description": "Code similarity engine and project registry"
}
```

#### Response: `202 Accepted` (Transaction Submitted & Tracked)
```json
{
  "project_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "project_name": "CodeProof Core Engine",
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
  "owner_wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "registration_status": "PENDING",
  "transaction_hash": "0x8a927c385ad3f0e8f7a6358db8ce37fbcf24e05b5505c2a11b7d5fb0ec19672e",
  "block_number": null,
  "block_timestamp": null,
  "failure_reason": null,
  "created_at": "2026-10-12T12:05:00Z",
  "confirmed_at": null
}
```

#### Error Responses
- **`400 Bad Request` (`TRANSACTION_NOT_FOUND`):** Transaction hash not found in mempool or RPC node.
- **`400 Bad Request` (`WALLET_MISMATCH`):** Transaction signer (`tx.from`) does not match supplied `owner_wallet_address`.
- **`400 Bad Request` (`INVALID_TARGET_CONTRACT`):** Transaction recipient (`tx.to`) does not target configured `PROJECT_REGISTRY_ADDRESS`.
- **`400 Bad Request` (`INVALID_FUNCTION_CALL`):** Transaction calldata does not invoke `registerProject(bytes32)` (`0x21897cdd`).
- **`400 Bad Request` (`FINGERPRINT_MISMATCH`):** Transaction calldata parameter does not match supplied `project_fingerprint`.
- **`400 Bad Request` (`CHAIN_ID_MISMATCH`):** Transaction chain ID does not match configured backend network.
- **`409 Conflict` (`DUPLICATE_FINGERPRINT`):** Fingerprint already exists in CodeProof database.
- **`422 Unprocessable Entity` (`VALIDATION_ERROR`):** Malformed hash or fingerprint format syntax.
- **`429 Too Many Requests` (`RATE_LIMIT_EXCEEDED`):** Rate limit or daily quota exceeded.
- **`503 Service Unavailable` (`BLOCKCHAIN_RPC_UNAVAILABLE`):** Temporary failure or timeout connecting to blockchain RPC node.

---

### 3.3 `GET /api/v1/projects/{project_id}`
Retrieves project details, off-chain metadata, synchronized blockchain confirmation status (policy-confirmed or protocol-finalized according to configured network policy), and failure reason if applicable.

- **Method:** `GET`
- **Path Parameters:**
  - `project_id` (`string`, required): UUIDv4 string

#### Response: `200 OK` (Confirmed Project)
```json
{
  "project_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "project_name": "CodeProof Core Engine",
  "description": "Code similarity engine and project registry",
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
  "owner_wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "registration_status": "CONFIRMED",
  "transaction_hash": "0x8a927c385ad3f0e8f7a6358db8ce37fbcf24e05b5505c2a11b7d5fb0ec19672e",
  "block_number": 42,
  "block_timestamp": 1791806710,
  "failure_reason": null,
  "created_at": "2026-10-12T12:05:00Z",
  "confirmed_at": "2026-10-12T12:05:10Z"
}
```

#### Response: `200 OK` (Failed Project)
```json
{
  "project_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "project_name": "CodeProof Core Engine",
  "description": "Code similarity engine and project registry",
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
  "owner_wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "registration_status": "FAILED",
  "transaction_hash": "0x8a927c385ad3f0e8f7a6358db8ce37fbcf24e05b5505c2a11b7d5fb0ec19672e",
  "block_number": 45,
  "block_timestamp": null,
  "failure_reason": "Execution reverted: ProjectRegistry: fingerprint already registered",
  "created_at": "2026-10-12T12:05:00Z",
  "confirmed_at": null
}
```

#### Error Responses
- **`400 Bad Request`:** Invalid UUID format for `project_id`.
- **`404 Not Found`:** Project ID does not exist in the database.

---

### 3.4 `POST /api/v1/projects/verify`
Directly verifies a 32-byte fingerprint against the live blockchain contract state (`ProjectRegistry.verifyProject`). Can be called without a prior database entry.

> **Execution Nature & Separation of On-Chain Existence from Lifecycle Confirmation:**
> This endpoint uses HTTP `POST` to receive the JSON request body, but it is an **idempotent, read-only, gas-free view operation** executed via EVM `eth_call`. It does not create or submit any transaction to the blockchain.
>
> **Crucial Distinction: On-Chain Existence (`is_registered`) vs. Lifecycle Confirmation (`registration_status`):**
> - `is_registered` reflects the **cryptographic on-chain existence boolean** returned directly by the smart contract view call `ProjectRegistry.verifyProject(fingerprint)`.
> - `registration_status` reflects the **backend's tracked registration lifecycle** (whether the transaction has passed all mutual consistency checks and satisfied the configured network confirmation/finality policy).
> - **CRITICAL INFERENCE RULE:** **`verifyProject() == true` alone proves that a fingerprint exists in mined contract storage, but must NOT, by itself, cause the API to claim that the transaction has satisfied the configured confirmation/finality policy.**
> - **Reporting Unconfirmed On-Chain Registrations:** If a fingerprint exists on-chain (`is_registered: true`) but has not yet passed backend confirmation checks (e.g. still accumulating `CONFIRMATION_DEPTH`, awaiting the PoS `finalized` block tag, or registered externally without backend indexing), the backend reports `registration_status: "PENDING"` (pending backend confirmation/finality verification) alongside `is_registered: true`. Only when the backend worker has verified all 8 consistency checks and the network-specific confirmation/finality policy is `registration_status` returned as `"CONFIRMED"`.
> - **Mempool / Unregistered Caveat:** If a registration transaction is currently unmined in the mempool, `is_registered` is `false`, and `registration_status` is `"PENDING"` (if tracked in the database) or `"UNREGISTERED"` (if untracked).

- **Method:** `POST`
- **Request Headers:** `Content-Type: application/json`

#### Request Body
| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `project_fingerprint` | `string` | Yes | `^0x[0-9a-fA-F]{64}$` | 32-byte SHA-256 fingerprint |

```json
{
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d"
}
```

#### Response: `200 OK` (Policy-Confirmed / Finalized Registration)
```json
{
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
  "is_registered": true,
  "registration_status": "CONFIRMED",
  "owner_wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "block_timestamp": 1791806710,
  "registered_at": "2026-10-12T12:05:10Z",
  "disclaimer": "Blockchain registration proves existence of this fingerprint at the recorded block timestamp by the specified wallet. It does not prove original authorship of the underlying code."
}
```

#### Response: `200 OK` (Mined On-Chain but Awaiting Policy Confirmation / Finality)
```json
{
  "project_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
  "is_registered": true,
  "registration_status": "PENDING",
  "owner_wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "block_timestamp": 1791806710,
  "registered_at": "2026-10-12T12:05:10Z",
  "disclaimer": "Fingerprint is recorded on-chain, but the transaction is currently accumulating required block confirmations or awaiting protocol finality."
}
```

#### Response: `200 OK` (Unregistered or Pending Mined State)
```json
{
  "project_fingerprint": "0x4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b",
  "is_registered": false,
  "registration_status": "UNREGISTERED",
  "owner_wallet_address": null,
  "block_timestamp": null,
  "registered_at": null,
  "disclaimer": "This fingerprint is not found in mined contract storage. If a transaction was just submitted, it may still be pending in the mempool."
}
```

#### Error Responses
- **`400 Bad Request`:** Invalid fingerprint format (not 64 hex characters prefixed with `0x`) or zero hash.
- **`502 Bad Gateway`:** Failed to query blockchain RPC node.

---

### 3.5 `POST /api/v1/analysis`
Submits code content or a repository archive for AI similarity analysis against the registered database corpus.

- **Method:** `POST`
- **Request Formats:**
  1. `application/json` (Multi-file structured list or single source string)
  2. `multipart/form-data` (Validated ZIP archive)

#### Request Body (`application/json`)
| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `project_name` | `string` | Yes | 1 - 100 characters | Name of the submission to analyze |
| `language` | `string` | Yes | Enum: `python`, `solidity`, `javascript`, `typescript` | Programming language for tokenization |
| `source_code` | `string` | Optional* | 1 - 500,000 characters | Single-file code string (*required if `files` is omitted) |
| `files` | `array` | Optional* | Max 500 files (*required if `source_code` is omitted) | Structured multi-file list |
| `files[].path` | `string` | Yes | Max 255 chars, relative path only | Sanitized relative file path |
| `files[].content` | `string` | Yes | Max 500,000 chars per file | Text content of file |
| `comparison_scope` | `string` | No | Enum: `ALL_PROJECTS`, `REGISTERED_ONLY` | Default: `ALL_PROJECTS` |
| `sensitivity_threshold` | `number` | No | Float `0.0` to `1.0` (inclusive), default `0.30` | Minimum similarity threshold to report |

```json
{
  "project_name": "Submitted Token Contract",
  "language": "solidity",
  "sensitivity_threshold": 0.35,
  "comparison_scope": "ALL_PROJECTS",
  "files": [
    {
      "path": "contracts/MyToken.sol",
      "content": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.24;\ncontract MyToken { ... }"
    },
    {
      "path": "contracts/interfaces/IERC20.sol",
      "content": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.24;\ninterface IERC20 { ... }"
    }
  ]
}
```

#### Request Format (`multipart/form-data`) — ZIP Safety Requirements `[PROPOSAL - NOT YET IMPLEMENTED]`
When submitting via ZIP archive:
- **Max Compressed Upload Size:** `10 MB`
- **Max Extracted Content Size:** `50 MB` total uncompressed
- **Max File Count:** `500 files`
- **Path Traversal Protection (Zip Slip):**
  - Absolute paths (starting with `/` or drive letters like `C:\`) are strictly rejected.
  - Path traversal sequences (`..`, `./`) are strictly rejected.
  - Symlinks and hardlinks inside the archive are strictly rejected.
- **Configurable Extension Whitelist:**
  - Files are filtered against a configurable allowed extension list: default `[.sol, .py, .js, .ts, .jsx, .tsx]`.
  - Non-whitelisted extensions (e.g. `.exe`, `.bin`, `.sh`, `.env`, `.png`) are skipped or reject the request.
- **Content Inspection:** In addition to extension checks, files undergo content inspection to verify valid text/UTF-8 encoding; binary files and executable headers (ELF, PE, Mach-O) are strictly rejected.

#### Response: `202 Accepted` (Analysis Queued)
```json
{
  "analysis_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "analysis_status": "QUEUED",
  "project_name": "Submitted Token Contract",
  "language": "solidity",
  "sensitivity_threshold": 0.35,
  "created_at": "2026-10-12T12:10:00Z",
  "estimated_duration_sec": 3
}
```

#### Error Responses
- **`400 Bad Request`:** Empty payload, unsupported language, or unsafe ZIP archive (path traversal / symlinks).
- **`413 Payload Too Large`:** Compressed archive > 10 MB or uncompressed content > 50 MB.
- **`422 Unprocessable Entity`:** Binary content detected or syntax validation failure.

---

### 3.6 `GET /api/v1/analysis/{analysis_id}`
Retrieves the complete results, similarity scores, exact matches, match results breakdown, and warnings for a completed AI similarity analysis.

- **Method:** `GET`
- **Path Parameters:**
  - `analysis_id` (`string`, required): UUIDv4 string

#### Response: `200 OK` (Analysis Completed)
```json
{
  "analysis_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "analysis_status": "COMPLETED",
  "project_name": "Submitted Token Contract",
  "language": "solidity",
  "sensitivity_threshold": 0.35,
  "similarity_percentage": 78.4,
  "exact_matches": [
    "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d"
  ],
  "match_results": [
    {
      "target_project_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "target_project_name": "CodeProof Core Engine",
      "target_fingerprint": "0x9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d",
      "similarity_percentage": 78.4,
      "matched_lines_count": 64,
      "is_on_chain_registered": true,
      "block_timestamp": 1791806710
    }
  ],
  "warnings": [
    "High overlap detected in common standard library imports and interface boilerplate (OpenZeppelin / ERC standards).",
    "Syntactic similarity is an indicator of overlap and does NOT constitute conclusive proof of plagiarism."
  ],
  "created_at": "2026-10-12T12:10:00Z",
  "completed_at": "2026-10-12T12:10:04Z"
}
```

#### Response: `200 OK` (Analysis Processing)
```json
{
  "analysis_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "analysis_status": "PROCESSING",
  "project_name": "Submitted Token Contract",
  "language": "solidity",
  "sensitivity_threshold": 0.35,
  "similarity_percentage": null,
  "exact_matches": [],
  "match_results": [],
  "warnings": [],
  "created_at": "2026-10-12T12:10:00Z",
  "completed_at": null
}
```

#### Error Responses
- **`400 Bad Request`:** Invalid UUID format for `analysis_id`.
- **`404 Not Found`:** Analysis ID does not exist.

---

## 4. Blockchain Module Contract Calls

The FastAPI backend interacts with `blockchain/contracts/ProjectRegistry.sol` using standard EVM RPC calls (`web3.py` or `ethers` provider).

### 4.1 Verified Smart Contract Signatures and Constants
The following functions, selectors, and event topics are verified directly against source declarations in [`blockchain/contracts/ProjectRegistry.sol`](file:///c:/presidency/CodeProof/blockchain/contracts/ProjectRegistry.sol) and independently calculated from canonical ABI signatures:

```solidity
// Verified Source Declarations in ProjectRegistry.sol:

// 1. Project Registration Function
function registerProject(bytes32 fingerprint) external;
// State Mutability: nonpayable
// Return Type: void (empty return)
// Canonical Signature: "registerProject(bytes32)"
// Function Selector: 0x21897cdd (keccak256("registerProject(bytes32)")[0:4])

// 2. Project Verification View Function
function verifyProject(bytes32 fingerprint)
    external
    view
    returns (
        bool isRegistered,
        address owner,
        uint256 timestamp
    );
// State Mutability: view
// Return Types: (bool isRegistered, address owner, uint256 timestamp)
// Canonical Signature: "verifyProject(bytes32)"
// Function Selector: 0x25fff3b0 (keccak256("verifyProject(bytes32)")[0:4])

// 3. Project Existence Check Function
function isProjectRegistered(bytes32 fingerprint) external view returns (bool);
// State Mutability: view
// Return Type: bool
// Canonical Signature: "isProjectRegistered(bytes32)"
// Function Selector: 0xd49a36c9 (keccak256("isProjectRegistered(bytes32)")[0:4])

// 4. Registration Event
event ProjectRegistered(
    bytes32 indexed fingerprint,
    address indexed owner,
    uint256 timestamp
);
// Indexed Parameters:
//   - Topic 1: bytes32 indexed fingerprint (32-byte SHA-256 digest)
//   - Topic 2: address indexed owner (registrant wallet address, left-padded to 32 bytes)
// Unindexed Parameter:
//   - Event Data (data payload): uint256 timestamp (block.timestamp in Unix epoch seconds)
// Canonical Event Signature: "ProjectRegistered(bytes32,address,uint256)"
// Topic 0: 0x24171d8b2972811723effda56408d64ca85a35e6da04d52a37a6bcf1a70cf4ca
```

Canonical ABI location: [`blockchain/abi/ProjectRegistry.json`](file:///c:/presidency/CodeProof/blockchain/abi/ProjectRegistry.json).

---

### 4.2 Registration Lifecycle & Background Confirmation Worker `[PROPOSAL - NOT YET IMPLEMENTED]`

#### 1. Function Selector and Calldata Structure
- **Function Selector:** `0x21897cdd` (`registerProject(bytes32)`)
- **Calldata Layout:** 4 bytes function selector (`0x21897cdd`) followed by 32 bytes normalized fingerprint (68 bytes / 136 hexadecimal characters total, prefixed with `0x`). Example: `0x21897cdd` + `9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cddb12da630045e0d`.

#### 2. Background Polling & Mempool Absence Rules
The background confirmation worker polls the blockchain via `eth_getTransactionReceipt(transaction_hash)` using exponential backoff with jitter:

1. **Pending Transactions (`receipt == null`):**
   - The transaction has not yet been included in a mined block.
   - **CRITICAL RULE ON MEMPOOL ABSENCE:** **Temporary absence from a node's mempool (`eth_getTransactionByHash` returning `null`) does NOT, by itself, cause a transaction to be marked `FAILED`.**
   - *Causes of Transient Mempool Absence:*
     - Propagation latency across node clusters or RPC read replicas behind load balancers.
     - Temporary eviction from local memory pools during transient gas fee spikes (the transaction remains pooled on other validator nodes and can be picked up when gas prices subside).
     - Node restarts, local mempool flushes, or peer disconnections.
     - Mining race condition: when a transaction is packaged into an incoming block, some nodes evict it from the mempool milliseconds before the block and receipt are indexed across read replicas.

#### 3. Nonce Reconciliation & Replacement Verification Algorithm
When `receipt == null` and `eth_getTransactionByHash(transaction_hash) == null`, the worker evaluates the sender wallet's confirmed on-chain nonce:
`sender_nonce = eth_getTransactionCount(owner_wallet_address, "latest")`

1. **Scenario A: `sender_nonce <= tx.nonce` (Nonce Not Yet Consumed):**
   - The sender's nonce has not been mined on-chain. The transaction remains legally valid for future block inclusion.
   - *Action:* The worker **must maintain `registration_status: "PENDING"`**. It must NOT transition to `FAILED`. It continues backoff polling. If configured, it queries fallback RPC providers or allows idempotent re-broadcast.

2. **Scenario B: `sender_nonce > tx.nonce` (Nonce Consumed On-Chain):**
   - A transaction with this nonce was mined into an EVM block. Because account nonces are strictly sequential, `tx.nonce` can never be mined again under the original hash.
   - **CRITICAL SECURITY RULE: No Inference from `verifyProject` Alone:**
     - The worker **MUST NOT** infer that a replacement transaction caused registration solely because `verifyProject(normalized_fingerprint)` reports `isRegistered == true` with the expected owner address.
     - *Rationale:* The fingerprint might have been registered by an earlier transaction at a different nonce, by a concurrent external transaction, or under an unrelated workflow. Assuming replacement without validating the actual transaction mined at that nonce risks falsely confirming an unvalidated transaction or recording an arbitrary transaction hash.
   - **Required Procedure for Replacement Validation:**
     1. **Identify the actual mined transaction:** The worker queries the blockchain to identify the specific transaction mined at `from == owner_wallet_address` and `nonce == tracked_tx.nonce` (by inspecting block transactions at the block height where the sender's nonce incremented, or filtering transaction history/receipts).
     2. **Validate the replacement transaction itself:** Once the candidate replacement transaction `replacement_tx` and its receipt `replacement_receipt` are retrieved, verify all of the following:
        - `replacement_receipt.status == 1` (execution succeeded).
        - `replacement_receipt.to.lower() == CONFIG.PROJECT_REGISTRY_ADDRESS.lower()` (targeted the correct registry).
        - `replacement_receipt.blockHash.lower() == canonical_block.hash.lower()` (included in canonical block).
        - `replacement_tx.from.lower() == owner_wallet_address.lower()`.
        - `replacement_tx.nonce == tracked_tx.nonce`.
        - `replacement_tx.input` starts with selector `0x21897cdd` (`registerProject(bytes32)`).
        - Calldata parameter `replacement_tx.input[10:74].lower() == normalized_fingerprint[2:].lower()`.
        - `replacement_receipt.logs` contains `ProjectRegistered` emitted by `CONFIG.PROJECT_REGISTRY_ADDRESS` with `topics[1] == normalized_fingerprint` and `topics[2] == padded owner`.
        - View call `verifyProject(normalized_fingerprint)` returns `isRegistered == true`, owner matching `owner_wallet_address`, and timestamp matching `canonical_block.timestamp`.
     3. **Update Tracked Hash Only After Validation:** The worker updates the tracked `transaction_hash` in PostgreSQL to `replacement_tx.hash` **only after** all the above checks pass, and then transitions status to `CONFIRMED`.
     4. **Unreliable Identification -> Retain Pending:** If `sender_nonce > tx.nonce` but the actual replacement transaction at that nonce cannot be reliably identified (e.g., RPC node transaction-by-nonce lookup unavailable, or historical log search inconclusive), the worker **MUST NOT** falsely confirm the record. The record **MUST remain `PENDING`** (pending reconciliation), logged for operational investigation, rather than falsely confirmed.
     5. **Definitive Conflicting Replacement / Cancellation:** If the transaction mined at `nonce == tracked_tx.nonce` is identified and verified to be an unrelated transaction (e.g. zero-value self-transfer cancellation, or a call to a different contract/function), the registration transaction was permanently superseded and cancelled.
        *Action:* Transition `registration_status = "FAILED"`, `failure_reason = "Transaction superseded by another mined transaction at the same nonce (nonce replaced or cancelled)"`.

#### 4. Timeout Versus Permanent Failure & Late Mining Reconciliation
1. **Theoretical Reality of EVM Transactions:**
   - A cryptographically signed raw transaction with an unconsumed nonce (`sender_nonce <= tx.nonce`) is valid indefinitely.
   - Timeout, absence from local mempools, absence from fallback RPC nodes, and `verifyProject == false` do **not** individually or collectively prove that an unmined transaction can never be broadcast or mined by a peer, validator, or MEV builder in the future.
2. **Distinguishing Nonterminal Operational Expiry from Objective Terminal Failure:**
   - **Objective Terminal Failure:** On-chain execution reverted (`receipt.status == 0` in a canonical block) or proven nonce supersession (`sender_nonce > tx.nonce` consumed by an unrelated mined transaction). Here, on-chain consensus guarantees the transaction can never execute successfully under this nonce. These terminal states are irreversible.
   - **Nonterminal Operational Timeout:** The backend ceases active receipt polling after `MAX_PENDING_TIMEOUT` (configurable, default 60 minutes) and consecutive missing checks.
   - **Reconciliation of Nonterminal `FAILED` Records:** A record marked `FAILED` due to an operational timeout is strictly **nonterminal**. It may be reconciled back to `PENDING` (if resubmitted by the client or re-observed in mempools) or directly to `CONFIRMED` (if later evidence shows the transaction was included in a canonical block).
3. **Preservation of Existing API Response Schema & Frontend Behavior:**
   - To preserve compatibility with existing API consumers without breaking changes, the four-state enum is maintained and reports `registration_status: "FAILED"` with an explicit reason:
     `failure_reason = "Operational timeout: transaction unmined and absent from observed mempools after timeout; nonce remains unconsumed"`.
   - **Frontend & Client Guidance:** Frontend behavior and API documentation must **not** imply that every `FAILED` record is permanently impossible to register or dead. When `failure_reason` indicates an operational timeout, the UI should offer users the option to re-check status, re-broadcast, or resubmit, reserving permanent failure alerts only for on-chain reverts and verified nonce supersessions.
   - Any proposed addition to the status enum (such as `EXPIRED` or `REQUIRES_RECONCILIATION`) is explicitly designated as **`[PROPOSAL - REQUIRES TEAM AGREEMENT]`** in Section 7.
4. **Late Mining and Rebroadcast Reconciliation (Preventing Inconsistent Duplicate Records):**
   - The PostgreSQL unique expression index `uq_projects_fingerprint` prevents inserting a second duplicate record for the same fingerprint under all circumstances.
   - **Resubmission After Operational Timeout:** If a client resubmits `POST /api/v1/projects/register` for a project whose prior submission timed out (`registration_status == FAILED` with an operational timeout reason), and on-chain state remains unregistered, the backend updates the existing project record with the new `transaction_hash`, resets `registration_status = "PENDING"`, and clears `failure_reason`.
   - **Late Mining Convergence:** If an operationally timed-out transaction is subsequently mined on-chain, periodic background reconciliation (or verification view queries) detects the mined state. The worker fetches the late receipt, verifies the canonical block hash and events, updates the existing database record from `FAILED` to `CONFIRMED`, records the canonical `block_number` and `block_timestamp`, and sets `failure_reason = null`. This guarantees database convergence to on-chain truth without duplicate records.

#### 5. Chain Reorganizations and Network-Appropriate Finality Policy `[PROPOSAL - CONFIGURABLE]`
1. **Network-Appropriate Confirmation & Finality:**
   - The backend must **NOT** claim or imply that a single fixed confirmation count guarantees absolute or irreversible finality universally across all EVM networks.
   - **Relationship Between `CONFIRMATION_DEPTH` and `finalized` Block Tag:**
     - `CONFIRMATION_DEPTH` (descendant block count) provides probabilistic depth against short-range reorganizations on Nakamoto consensus chains, but **never guarantees absolute protocol finality**.
     - The `finalized` block tag (EIP-1898) queries consensus-level economic finality on Ethereum PoS (Casper FFG checkpoints). Once finalized, a block cannot be reverted without slashing a significant fraction of the validator stake.
   - **Proposed / Configurable Policy Specification Per Supported Network `[PROPOSAL - CONFIGURABLE]`:**
     The confirmation policy is configurable per deployment network (`CONFIRMED` is strictly tied to meeting the configured policy):
     - **Ethereum PoS (Mainnet / Sepolia / Holesky):** Proposed policy enforces protocol finality (`NETWORK_FINALITY_MODE = "FINALIZED_TAG"`). It queries `eth_getBlockByNumber("finalized", false)` and transitions to `CONFIRMED` only when protocol finalization is reached (typically ~12.8 minutes / 2 epochs). `CONFIRMATION_DEPTH` alone is not treated as final.
     - **Probabilistic / Proof-of-Work Chains:** Proposed policy enforces `CONFIRMATION_DEPTH` (`NETWORK_FINALITY_MODE = "BLOCK_DEPTH"`, default 12-32 blocks) because the underlying protocol does not support deterministic finality tags. Confirmations reduce reorg probability exponentially but remain probabilistic.
     - **Layer 2 Rollups (Arbitrum, Optimism, Base):** Sequencer receipts offer sequencer-level confirmation (`CONFIRMATION_DEPTH = 1`), which provides soft execution confirmation against the sequencer's state. However, this does **NOT** constitute protocol finality; protocol-level settlement/finality on Ethereum L1 is only achieved after transaction batches and state roots are posted to L1 and the fraud-proof challenge window (7 days for optimistic rollups) or ZK-validity proof verification completes.
     - **Local Development / Test Networks (Hardhat / Anvil):** Configured behavior is a local development/test policy (`CONFIRMATION_DEPTH = 1`, 1 block confirmation for rapid testing); this policy is designed for development environments and must not be implied to universally guarantee irreversible finality on production chains.
2. **Dual Requirements When Using the `finalized` Block Tag:**
   When evaluating finality on PoS networks using the `finalized` block tag, the worker **MUST verify BOTH** of the following conditions:
   1. **Finalized Block Height Check:** The receipt block number is at or below the current finalized block height:
      `finalized_block = eth_getBlockByNumber("finalized", false)`
      `receipt.blockNumber <= finalized_block.number`
   2. **Canonical Block Hash Match:** The receipt block hash matches the canonical block hash at the receipt's block number:
      `canonical_block = eth_getBlockByNumber(receipt.blockNumber, false)`
      `receipt.blockHash.lower() == canonical_block.hash.lower()`
   *(Note: Verifying both conditions is strictly required to prevent a false confirmation if a transaction was mined on an orphaned fork that happened to share the same block number as a canonical finalized block).*
3. **Handling Reorganizations (Reorg Policy):**
   - If a canonical block containing a registration is reorganized out before reaching finality:
     - The worker detects that `canonical_block.hash` no longer matches the tracked `receipt.blockHash`, or `eth_getTransactionReceipt(transaction_hash)` returns null/new block hash.
     - The worker **reverts the database state from `CONFIRMED` back to `PENDING`**, clears `confirmed_at`, and re-checks:
       1. Has the transaction been re-mined into the new canonical chain? If so, retrieve the new receipt, new canonical `blockNumber`, `blockHash`, and `block_timestamp`, and re-run all confirmation checks.
       2. Is the transaction back in the mempool? If so, retain `PENDING` and continue polling.
       3. Did the transaction revert in the new canonical chain? If so, transition to `FAILED`.
       4. Was the fingerprint registered by a competing transaction in the reorg chain? If so, evaluate on-chain state and update accordingly.

#### 6. Mutual Consistency of Confirmation Checks
All 8 checks must refer to the **same mined transaction and canonical block**:
1. **Receipt Execution Status:** `receipt.status == 1` (EVM status 1 indicates success; status 0 indicates revert).
2. **Canonical Block Hash Match:** `receipt.blockHash.lower() == canonical_block.hash.lower()` (matches canonical block).
3. **Network Confirmation / Finality Policy Satisfied:**
   - If configured for PoS finality (`NETWORK_FINALITY_MODE == "FINALIZED_TAG"`): satisfies **both** `receipt.blockNumber <= finalized_block.number` and `receipt.blockHash.lower() == canonical_block.hash.lower()`.
   - If configured for probabilistic depth (`NETWORK_FINALITY_MODE == "BLOCK_DEPTH"`): satisfies `receipt.blockNumber + CONFIRMATION_DEPTH <= current_block.number` and `receipt.blockHash.lower() == canonical_block.hash.lower()`.
4. **Target Contract Address:** `receipt.to.lower() == CONFIG.PROJECT_REGISTRY_ADDRESS.lower()` (case-insensitive checksum/lowercase match against configured registry).
5. **Transaction Sender Validation:** `tx.from.lower() == owner_wallet_address.lower()` (matches expected registrant wallet).
6. **Calldata Validation:**
   - `tx.input` starts with selector `0x21897cdd` (`registerProject(bytes32)`).
   - Calldata parameter `tx.input[10:74].lower() == normalized_fingerprint[2:].lower()` (submitted fingerprint matches calldata).
7. **Event Emission & Topics Validation:**
   - A log in `receipt.logs` is emitted by `log.address.lower() == CONFIG.PROJECT_REGISTRY_ADDRESS.lower()`.
   - `log.topics[0] == 0x24171d8b2972811723effda56408d64ca85a35e6da04d52a37a6bcf1a70cf4ca` (Topic 0 of `ProjectRegistered(bytes32,address,uint256)`).
   - `log.topics[1] == normalized_fingerprint` (indexed `bytes32 fingerprint`).
   - `log.topics[2] == "0x000000000000000000000000" + owner_wallet_address[2:].lower()` (indexed `address owner`, left-padded with 24 zero hex characters to 32 bytes).
   - Decoded event log timestamp: `int(log.data, 16) == canonical_block.timestamp`.
8. **Committed On-Chain State Verification:**
   - View query `verifyProject(normalized_fingerprint)` via `eth_call` returns:
     - `isRegistered == true`
     - `owner.lower() == owner_wallet_address.lower() == tx.from.lower()`
     - `timestamp == canonical_block.timestamp`

Only when all 8 checks pass on the same mined transaction and canonical block does the database update:
- `registration_status = "CONFIRMED"` (signifying policy-confirmed or protocol-finalized according to configured network policy)
- `block_number = receipt.blockNumber`
- `block_timestamp = canonical_block.timestamp`
- `confirmed_at = now()` (ISO 8601 UTC)
- `failure_reason = null`

#### 7. Reverted Transactions
- `receipt.status == 0` in a canonical block:
  - `registration_status = "FAILED"`
  - `block_number = receipt.blockNumber`
  - `block_timestamp = null`
  - `failure_reason = "Transaction reverted on-chain: fingerprint already registered or gas exhausted"`

#### 8. Temporary RPC Inconsistencies & Transport Errors
- Any JSON-RPC network errors, connection timeouts, HTTP 429 rate limits, HTTP 502/503/504 gateway errors, or internal node errors (-32000, -32005) must be treated as transient network conditions.
- The worker applies exponential backoff with jitter and retries.
- **Transient RPC errors must NEVER cause a transaction to be marked `FAILED`. The record remains `PENDING`.**

---

### 4.3 Calling `verifyProject(bytes32 fingerprint)`
- **EVM Function Selector:** `0x25fff3b0`
- **Gas Type:** View call (`eth_call`, zero gas consumed)
- **Return Tuple:** `(bool isRegistered, address owner, uint256 timestamp)`
- **Backend Mapping & Stale Record Reconciliation `[PROPOSAL - NOT YET IMPLEMENTED]`:**

#### Stale Record & Discrepancy Reconciliation Rules:
1. **On-Chain Existence (`isRegistered == true`):**
   - Report `is_registered: true`.
   - Report `registration_status: "CONFIRMED"` **only if** a corresponding backend record exists, is currently recorded as confirmed, and its confirmation remains valid under the configured network policy (i.e. canonical block hash still matches the chain and configured depth or `finalized` tag requirements are satisfied).
   - If the backend record is not confirmed or its confirmation validity check is currently pending/in progress, report `registration_status: "PENDING"`.
2. **On-Chain Non-Existence (`isRegistered == false`) & Discrepancy Handling:**
   - Report `is_registered: false`.
   - **Never return `CONFIRMED`** solely because the backend database previously recorded that status.
   - If the database previously recorded `CONFIRMED` (or `PENDING`), trigger asynchronous reconciliation to investigate the discrepancy and report an appropriate non-confirmed status (`registration_status: "PENDING"`) while reconciliation proceeds.
   - If no database record exists, report `registration_status: "UNREGISTERED"`.
3. **Protection Against Inappropriate Permanent `FAILED` Transitions:**
   - **Do not automatically mark a previously confirmed registration permanently `FAILED`** solely because a single RPC query returns `isRegistered == false`.
   - A single negative read can result from transient RPC inconsistencies (such as an out-of-sync read replica behind a load balancer, provider routing glitches, or temporary node desynchronization) or shallow chain reorganizations (where the transaction may be re-mined into a successor canonical block).
   - The reconciliation worker must re-poll multiple independent fallback RPC providers, inspect canonical block headers, and verify mempool state before modifying persistent database records. Permanent terminal failure is only recorded if definitive evidence proves an on-chain revert or irrecoverable nonce supersession.

#### Proposed Mapping Implementation:
```python
is_reg, owner, ts = contract.functions.verifyProject(fingerprint).call()

# Cross-reference tracked backend database record for confirmation lifecycle
db_record = db.query(Project).filter_by(project_fingerprint=fingerprint).first()

if is_reg:
    # 1. verifyProject() == True confirms cryptographic on-chain existence.
    # Report CONFIRMED only if database record is confirmed AND its confirmation
    # remains valid under the configured network policy (canonical block & depth/finality).
    is_valid = (
        db_record is not None
        and db_record.registration_status == "CONFIRMED"
        and is_confirmation_valid(db_record, CONFIG.NETWORK_FINALITY_POLICY)
    )
    if is_valid:
        status = "CONFIRMED"
    else:
        # If record is unconfirmed or validity is being rechecked, report PENDING while reconciliation proceeds
        if db_record and db_record.registration_status == "CONFIRMED":
            trigger_reconciliation(fingerprint, db_record, reason="RECHECK_CONFIRMATION_VALIDITY")
        status = "PENDING"

    return {
        "project_fingerprint": fingerprint,
        "is_registered": True,
        "registration_status": status,
        "owner_wallet_address": owner,
        "block_timestamp": ts
    }
else:
    # 2. verifyProject() == False: Never return CONFIRMED solely based on stale DB state.
    if db_record and db_record.registration_status == "CONFIRMED":
        # Discrepancy detected: DB recorded CONFIRMED but RPC reports unregistered.
        # 3. Do NOT mark FAILED automatically; trigger reconciliation to account for
        # transient RPC replica lag, node desync, or temporary chain reorganizations.
        trigger_reconciliation(fingerprint, db_record, reason="DISCREPANCY_CONFIRMED_BUT_RPC_FALSE")
        status = "PENDING"
    elif db_record and db_record.registration_status == "PENDING":
        status = "PENDING"
    else:
        status = "UNREGISTERED"

    return {
        "project_fingerprint": fingerprint,
        "is_registered": False,
        "registration_status": status,
        "owner_wallet_address": None,
        "block_timestamp": None
    }
```

---

### 4.4 Calling `isProjectRegistered(bytes32 fingerprint)`
- **EVM Function Selector:** `0xd49a36c9`
- **Gas Type:** View call (`eth_call`)
- **Return Value:** `bool`
- **Use Case:** High-performance binary pre-check used by client wallets or backend validation prior to initiating transactions.

---

## 5. Backend <-> AI Plagiarism Detector Interface

The `ai-detector/` module currently implements a deterministic Python/Java code-similarity baseline using Python's standard library. Its primary entry point is the `analyze_submissions()` Python function. The detector is currently a Python library, not a standalone HTTP service.

The public backend endpoints described in Sections 3.5 and 3.6 remain proposed API contracts. They must not be interpreted as implemented detector endpoints until backend orchestration and integration have been developed and tested.

### 5.1 Implemented Detector Interface

The detector accepts a collection of source-code submissions through the `analyze_submissions()` function.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `submission_id` | String | Non-empty and unique within the input | Identifies a submission |
| `language` | String | `python` or `java`, case-insensitive | Specifies the source-code language |
| `source_code` | String | 1–500,000 characters; null bytes are rejected | Contains the submitted source code |
| `shingle_k` | Integer | Must be at least 1 | Configures the shingle size; defaults to 5 |

The detector accepts a maximum of 100 submissions per analysis. Invalid inputs are rejected through validation errors rather than being treated as valid source code.

Example Python usage:

```python
from codeproof_detector import analyze_submissions

submissions = [
    {
        "submission_id": "submission-1",
        "language": "python",
        "source_code": "def add(a, b):\n    return a + b\n",
    },
    {
        "submission_id": "submission-2",
        "language": "python",
        "source_code": "def sum_values(x, y):\n    return x + y\n",
    },
]

report = analyze_submissions(submissions)
```

The import path above is illustrative. The final import statement must match the actual package structure in `ai-detector/src/`.

### 5.2 Implemented Detector Output

The function returns a JSON-serializable Python dictionary containing the following top-level fields:

| Field | Description |
|---|---|
| `results` | Per-submission analysis results and comparisons |
| `method` | Identifies the similarity-analysis method used |
| `warnings` | Analysis-level warnings |
| `disclaimer` | Explains the limitations of similarity scores |
| `score_to_percentage` | Documents the score-to-percentage conversion |

Each submission result includes its submission identifier, language, token count, comparisons, and applicable warnings.

Comparison results can include:

- `compared_submission_id`: Identifier of the submission being compared.
- `token_similarity`: Similarity derived from token-sequence comparison.
- `structural_similarity`: Similarity derived from code shingles.
- `embedding_similarity`: `null` in the current implementation.
- `combined_similarity`: Combined similarity score.
- `matched_regions`: Information about matching code regions.
- `boilerplate_matched`: Indicates matches associated with common or boilerplate code.
- `warnings`: Comparison-specific warnings.
- `review_recommendation`: A recommendation for human review.

Similarity scores use the range 0–1. A percentage can be calculated by multiplying the corresponding score by 100. These scores indicate similarity, not a confirmed finding of plagiarism.

The current baseline compares submissions written in the same supported language. It does not execute submitted source code. Results are deterministic for the same inputs and configuration.

### 5.3 Proposed Backend-to-Detector Mapping

The following table describes a proposed mapping between the public analysis API and the current detector interface. This mapping requires implementation and integration testing before it can be considered an operational contract.

| Backend/API Field | Proposed Mapping | Status |
|---|---|---|
| `analysis_id` | Backend-generated identifier for tracking an analysis request | `[PROPOSAL]` |
| `project_name` | Backend metadata; not required by the detector | `[PROPOSAL]` |
| `language` | Map to the `language` field for each submission | `[MAPPING TO IMPLEMENT]` |
| `files[].path` | Use as metadata or combine with a unique identifier to construct `submission_id` | `[MAPPING TO IMPLEMENT]` |
| `files[].content` | Map to `source_code` | `[MAPPING TO IMPLEMENT]` |
| `sensitivity_threshold` | Requires an agreed threshold policy; the current detector does not provide a validated plagiarism threshold | `[PROPOSAL]` |
| `corpus_reference_ids` | Backend must retrieve the referenced source material and supply eligible comparison submissions | `[PROPOSAL]` |
| `similarity_percentage` | May be derived from a selected comparison's `combined_similarity` multiplied by 100 | `[MAPPING TO IMPLEMENT]` |
| `match_results` | May be assembled from comparison results and matching-region information | `[MAPPING TO IMPLEMENT]` |

The backend and project team must agree on how comparison submissions are selected, how analysis requests are tracked, how results are stored, and how detector results are mapped to the public response schema.

### 5.4 Integration and Operational Limitations

The following limitations apply to the current Phase 1 detector:

1. **No standalone HTTP endpoint:** The detector exposes a Python function; a `POST /detect` endpoint has not been established by the detector implementation.
2. **No confirmed asynchronous worker:** Celery, Redis, and a background-job workflow must not be treated as implemented without verified code and tests.
3. **No confirmed persistent vector index:** The current baseline does not establish a persistent embedding or vector-search service.
4. **No embedding-based similarity:** `embedding_similarity` is `null` in the current implementation.
5. **Limited language support:** The baseline supports Python and Java. Solidity, JavaScript, TypeScript, and other languages require additional implementation and testing.
6. **No source-code execution:** Submitted programs are analyzed as source text; they are not run by the detector.
7. **Human review remains necessary:** Similarity scores can identify potentially related submissions, but cannot independently establish intent, authorship, or plagiarism.
8. **Blockchain registration is separate:** The detector's similarity analysis and the blockchain's project-registration or fingerprint-verification mechanisms serve different purposes and must be integrated explicitly.

HTTP integration, asynchronous processing, persistent similarity indexes, additional language support, semantic embeddings, and threshold-based decision policies remain future work until implemented, tested, and agreed upon by the team.


---

## 6. Concurrency, Security, and Operational Safeguards

### 6.1 Duplicate Submission Handling & Concurrency Coordination `[PROPOSAL - NOT YET IMPLEMENTED]`

1. **PostgreSQL Unique Expression Index:**
   The PostgreSQL `projects` table must enforce a functional unique expression index on the lowercase fingerprint:
   ```sql
   CREATE UNIQUE INDEX uq_projects_fingerprint ON projects (LOWER(project_fingerprint));
   ```

2. **Dual-Layer Duplicate Prevention Rationale & Storage Clarification:**
   - **Unique Index Role & Storage Clarification:** The functional expression index `uq_projects_fingerprint` is the authoritative database safeguard enforcing case-insensitive uniqueness at the SQL engine level (e.g., rejecting an insert of `0xABC...` if `0xabc...` already exists). However, PostgreSQL expression indexes **do not alter or coerce stored column values to lowercase**; they only index the evaluated result of `LOWER()`. Lowercase storage must be explicitly enforced at the API boundary by the future backend before insertion.
   - **Backend Normalization Role:** Normalizing fingerprints to lowercase at the API boundary ensures uniform data storage across all records. This allows standard database lookups (`SELECT * FROM projects WHERE project_fingerprint = :val`) to execute predictably and efficiently using standard B-tree index scans without requiring runtime `LOWER()` transformations on every query. *(Note: Relational foreign-key references must target the table's primary key `project_id`, as PostgreSQL foreign keys cannot reference a functional expression index).*

3. **Explicit Distinction of Duplicate and Registration States:**
   The system explicitly distinguishes between three different duplicate and lifecycle scenarios:
   - **Database Duplicate (Existing Database Record):** A record with this normalized fingerprint is already persisted in the local PostgreSQL `projects` table. Re-submitting triggers a database unique constraint violation (`uq_projects_fingerprint`).
   - **Pending Registration:** A record exists in the local database with `registration_status: "PENDING"`, indicating the transaction has been broadcast to the EVM mempool but has not yet been mined into an on-chain block.
   - **On-Chain Blockchain Duplicate:** The fingerprint is already recorded in the smart contract's persistent storage (`ProjectRegistry.sol: _records[fingerprint].timestamp != 0`). Any subsequent on-chain registration transaction will revert with `"ProjectRegistry: fingerprint already registered"`.

4. **Graceful Error Handling for Database Uniqueness Violations:**
   - When PostgreSQL raises a `unique_violation` (SQLSTATE `23505`) on `uq_projects_fingerprint`, the backend must gracefully intercept the database exception.
   - The backend must not propagate an unhandled 500 server error; instead, it must return a documented HTTP `409 Conflict` response with error code `DUPLICATE_FINGERPRINT`:
     ```json
     {
       "error": {
         "code": "DUPLICATE_FINGERPRINT",
         "message": "Fingerprint already registered in CodeProof database.",
         "details": [
           {
             "field": "project_fingerprint",
             "issue": "A project with this cryptographic fingerprint has already been submitted."
           }
         ],
         "timestamp": "2026-10-12T12:05:05Z"
       }
     }
     ```

5. **Authoritative Database Safeguards vs. Optional Application Locking:**
   - **Authoritative Database Safeguard:** The unique index `uq_projects_fingerprint` is the authoritative and sufficient database-level safeguard preventing duplicate fingerprints under concurrent inserts. Even if multiple concurrent requests pass initial application checks, PostgreSQL atomically enforces uniqueness and rolls back colliding transactions.
   - **Optional Workflow Locking:** Application-level distributed locks (e.g. Redis lock on `lock:fingerprint:<normalized_hash>` or PostgreSQL transaction advisory locks) are **optional** rather than mandatory. They are only justified if the development team chooses to coordinate multi-step application workflows (such as orchestrating external RPC pre-checks or serializing background worker tasks prior to database insertion).

6. **Blockchain Ground Truth Caveat:**
   - **Independence of On-Chain State:** True blockchain registration status must always be established independently through direct smart contract verification (`verifyProject(bytes32)`) and transaction receipt confirmation, rather than inferred from presence or absence in the local database. A fingerprint may exist on-chain without being recorded in the local database (e.g., registered via an external Web3 script or third-party interface), or a database entry may be `PENDING` while the blockchain transaction is still unmined.
   - **Handling External On-Chain Races:** If an on-chain registration for the same fingerprint mines first via external submission, any concurrent or subsequent transaction submitted by CodeProof will revert with `"ProjectRegistry: fingerprint already registered"`. The backend receipt worker must catch this revert and mark the database status as `FAILED` with an accurate `failure_reason`.

7. **Reconciliation of Timed-Out Submissions and Late Mining:**
   - **Preventing Inconsistent Duplicate Records:** The functional unique expression index `uq_projects_fingerprint` guarantees at the database engine level that two records for the same normalized fingerprint can never coexist.
   - **Nonterminal Nature of Operational Timeouts:** A `FAILED` state caused by an operational timeout (`MAX_PENDING_TIMEOUT` exceeded with mempool absence) is strictly nonterminal. It reflects an operational polling cutoff, not an on-chain rejection. The record may be reconciled back to `PENDING` (on user resubmission or re-broadcast) or directly to `CONFIRMED` (upon late mining confirmation). Frontend applications should present operational timeouts with retry/recheck options rather than claiming the project is permanently unregistrable.
   - **Resubmission Following Operational Timeout:** If a client resubmits `POST /api/v1/projects/register` for a project whose prior submission reached an operational timeout (`registration_status == FAILED` with timeout failure reason), and on-chain state remains unregistered, the backend updates the existing project record with the newly broadcast `transaction_hash`, resets `registration_status = "PENDING"`, and clears `failure_reason`.
   - **Late Mining Convergence:** If an operationally timed-out transaction is subsequently mined on-chain, periodic background reconciliation (or read verification via `POST /api/v1/projects/verify`) detects the mined status. The worker retrieves the late receipt, verifies the canonical block hash and events, and transitions the existing record to `registration_status = "CONFIRMED"`, recording canonical block height and timestamp while setting `failure_reason = null`. Database state safely converges to on-chain truth without duplicate record collisions.

### 6.2 Wallet Ownership and Key Security
- **No Server Private Keys Committed:** Server `.env` files and relayer private keys must never be committed to git.
- **Client Wallet Sovereignty:** For the initial version, the registering wallet is `msg.sender`. Users sign directly via their Web3 wallet (MetaMask / EIP-1193). The backend only indexes the resulting broadcast hash and verifies `msg.sender` against the node.

### 6.3 Proposed Rate Limits and Quotas `[PROPOSAL - NOT YET IMPLEMENTED]`
To prevent RPC node exhaustion, mempool spam, and denial-of-service:
- **IP Rate Limit:** Maximum 10 registration submissions per minute per IP; maximum 5 analysis submissions per minute per IP.
- **Wallet Daily Quota:** Maximum 50 project registrations per wallet address per 24-hour window.
- **Operational Monitoring:** Prometheus metrics tracking:
  - `codeproof_rpc_latency_seconds`
  - `codeproof_mempool_pending_count`
  - `codeproof_analysis_queue_lag_seconds`
  - `codeproof_failed_transactions_total`

---

## 7. Decision Register: Proposals Requiring Team Agreement

| Item | Proposed Default | Alternative / Considerations | Status |
|---|---|---|---|
| **Wallet Registration Architecture** | Direct Client-side Web3 Wallet signing (`msg.sender` is user) | Backend Relayer Wallet with EIP-712 Meta-transactions (server pays gas) | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
| **Code Storage Strategy** | Off-chain encrypted database storage in PostgreSQL | Ephemeral analysis only (code discarded immediately after vectorization) | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
| **Analysis Async Mechanism** | Celery + Redis worker queue with persistent task IDs | FastAPI `BackgroundTasks` with PostgreSQL status polling | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
| **Authentication & User Profiles** | SIWE (Sign-In with Ethereum, EIP-4361) | Standard JWT Email/Password authentication or open v1 API | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
| **Allowed File Extensions Whitelist** | Default: `.sol`, `.py`, `.js`, `.ts`, `.jsx`, `.tsx` | Expandable to `.rs`, `.go`, `.java`, `.cpp` | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
| **Network Finality & Confirmation Policy** | Configurable per network: Ethereum PoS requires `finalized` block tag; probabilistic chains use `CONFIRMATION_DEPTH = 12` | Static fixed confirmation count (which fails to guarantee absolute finality on PoS or creates excessive lag on L2/local chains) | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
| **Operational Timeout Lifecycle Status Enum** | Preserve existing 4-state enum (`PENDING`, `CONFIRMED`, `FAILED`, `UNREGISTERED`) with detailed `failure_reason` | Add dedicated lifecycle enum values such as `EXPIRED` or `REQUIRES_RECONCILIATION` to distinguish operational timeout from irreversible EVM reverts | `[PROPOSAL - REQUIRES TEAM AGREEMENT]` |
