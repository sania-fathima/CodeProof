# CodeProof
### Blockchain-Based Project Ownership Verification and AI-Assisted Code Similarity Detection

CodeProof is a web-based academic project designed to combine blockchain-based project fingerprint registration with source-code similarity analysis. It provides a way to record a project's digital fingerprint and help identify potentially similar Python and Java code submissions.

> **Important:** Blockchain registration provides a timestamped record associated with a fingerprint; it does not independently prove who originally created a project. Code similarity scores are indicators for further review, not definitive proof of plagiarism.

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)

## Project Overview

CodeProof addresses two related challenges in academic software projects:

1. **Project ownership records:** A cryptographic fingerprint can be registered on a blockchain, associating it with a registering address and a registration timestamp.
2. **Code similarity analysis:** Source-code submissions can be compared to identify similar token patterns and code structure that may warrant further investigation.

The application brings these capabilities together through a web interface, a Python backend, a code-analysis module, and a Solidity smart contract.

## Key Features

- **Blockchain registration:** Register a project fingerprint through the `ProjectRegistry` smart contract.
- **Ownership-record verification:** Check whether a fingerprint has been registered and retrieve its associated owner and timestamp.
- **Duplicate protection:** The contract rejects duplicate fingerprint registrations and invalid zero fingerprints.
- **Source-code similarity analysis:** Compare supported Python and Java submissions using token-based and structural similarity measures.
- **Similarity reporting:** Present comparison scores and matched code regions where available.
- **Modular architecture:** Separate frontend, backend, blockchain, AI detector, tests, and documentation components.

Feature availability depends on the integration and configuration of each module. See the module documentation for implementation details.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend API | Python, FastAPI, Uvicorn |
| Blockchain | Solidity, Hardhat, ethers.js |
| AI-assisted code analysis | Python, token-based similarity and structural comparison |
| Testing | pytest, Hardhat tests |
| Database | PostgreSQL is part of the planned/contracted architecture; verify the active integration before relying on database-backed features |

## Project Structure

```text
CodeProof/
├── ai-detector/   # Source-code similarity analysis
├── backend/       # FastAPI application and API tests
├── blockchain/    # Smart contract, deployment scripts and tests
├── docs/          # API contract and project documentation
├── frontend/      # React + TypeScript web application
├── tests/         # Project-level tests
├── .gitignore
├── pytest.ini
└── README.md
```

## How It Works

### 1. Register a project

The registration workflow generates a fingerprint for a project and submits it to the blockchain registry. The smart contract records the fingerprint, registering address, and timestamp.

### 2. Verify a project

A submitted fingerprint can be checked against the registry. A registered fingerprint returns its associated registration information; an unregistered fingerprint is reported as not found.

### 3. Compare source code

The AI detector compares supported source-code submissions using token-based overlap and structural sequence similarity. The resulting scores help reviewers identify code that may need closer examination.

### 4. Review the evidence

Blockchain records and code similarity results serve different purposes: the registry records a fingerprint, while similarity analysis compares source code. Neither result alone establishes plagiarism or conclusively proves authorship.

## Getting Started

### Prerequisites

Install the tools needed for the modules you intend to run:

- Git
- Node.js and npm
- Python
- A local Hardhat blockchain for local smart-contract testing
- The Python packages listed in the relevant `requirements.txt` files

### 1. Clone the repository

```bash
git clone https://github.com/sania-fathima/CodeProof.git
cd CodeProof
```

### 2. Start the blockchain module

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat test
```

To run local blockchain verification, follow the instructions in `blockchain/README.md` and use the deployment address for the current local Hardhat session. A local deployment address is not a permanent public-network address.

### 3. Start the backend

Open a terminal in the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies and start the API:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Useful endpoints, when the backend is running:

- Health check: `http://localhost:8000/health`
- Interactive API documentation: `http://localhost:8000/docs`
- Similarity analysis: `POST http://localhost:8000/api/v1/analyze`

Refer to the backend documentation for the request format and supported validation rules.

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, commonly `http://localhost:5173`.

**Integration note:** Blockchain and backend services must be running and configured for the relevant frontend workflows. Check the frontend and blockchain documentation for RPC settings, contract address, and network requirements.

## Running Tests

Run the AI detector tests from the repository root:

```bash
python -m pytest .\ai-detector\tests -q
```

Run the backend tests:

```bash
python -m pytest .\backend\tests -q
```

Run the blockchain tests:

```bash
cd blockchain
npx hardhat test
```

Previously recorded development results include 33 passing AI detector tests, 6 passing backend tests, and 11 passing blockchain tests. These are historical results; rerun the commands in your current environment to confirm the latest state.

The evaluation script and report are available in:

- `ai-detector/examples/evaluate_similarity.py`
- `ai-detector/EVALUATION_REPORT.md`

## Current Limitations

- The detector currently focuses on Python and Java source code.
- Similarity scores are heuristic indicators and are not a definitive plagiarism verdict.
- Short programs may produce unreliable scores.
- Renaming identifiers or changing implementation structure can affect similarity measurements.
- Embedding-based similarity is not implemented in the current baseline.
- Blockchain registration records a fingerprint and registration metadata; it does not establish original authorship by itself.
- Local blockchain deployments are for development and testing, not permanent public verification.
- Full end-to-end functionality depends on the configuration and integration of the frontend, backend, and blockchain modules.

## Future Improvements

- Evaluate the detector on a larger labelled dataset and report appropriate evaluation metrics.
- Improve detection of renamed identifiers and structurally similar implementations.
- Explore embedding-based similarity and additional programming languages.
- Strengthen end-to-end integration and error handling.
- Add persistent storage and authentication where required.
- Provide clearer evidence summaries for reviewers and instructors.

## Contributors

CodeProof is a collaborative academic project. Team members contribute across blockchain development, AI-assisted code similarity detection, backend development, frontend development, and integration testing/documentation.

See the repository's GitHub contributors and commit history for recorded contributions.

---

**Project status:** Academic prototype under development.
