# CodeProof — Integration Test Plan

## 1. Document Information

| Field | Details |
|---|---|
| Project | CodeProof |
| Document | Integration Test Plan |
| Version | 1.0 |
| Purpose | Validate the behavior of the project's modules and their interactions |
| Status | Test plan; execution results are recorded separately |

## 2. Objective

The objective of this test plan is to verify that CodeProof's frontend, backend API, AI-assisted code similarity detector, and blockchain registry behave correctly individually and when integrated.

Testing will focus on functional correctness, input validation, error handling, duplicate prevention, fingerprint verification, and consistency between returned results and actual system behavior.

## 3. Scope

The planned tests cover:

- Backend health and API availability.
- Valid and invalid source-code analysis requests.
- Similarity analysis for identical, modified, and unrelated source code.
- Blockchain registration and verification of project fingerprints.
- Duplicate and invalid fingerprint handling.
- Frontend interactions with configured backend and blockchain services.
- Integration errors, unavailable services, and incorrect configuration.

Tests must be adapted to the functionality currently implemented. A planned test must not be reported as passed until it has actually been executed.

## 4. Test Environment

| Component | Test configuration |
|---|---|
| Operating system | Windows development environment |
| Backend | Python, FastAPI, Uvicorn |
| AI detector | Python-based source-code similarity module |
| Blockchain | Local Hardhat development network |
| Frontend | React, TypeScript, Vite |
| API documentation | FastAPI Swagger UI at `/docs` |
| Test frameworks | pytest and Hardhat test runner |

Record the actual software versions, contract address, network configuration, and environment details when executing the tests. Never publish API keys, private keys, passwords, or other secrets.

## 5. Test Cases

### A. Backend API Tests

| ID | Test scenario | Expected result |
|---|---|---|
| API-01 | Send a request to `/health` | The endpoint returns the configured healthy response |
| API-02 | Submit a valid code-analysis request | The API returns a response matching the documented schema |
| API-03 | Submit a request with missing required fields | The API returns a validation error |
| API-04 | Submit an unsupported language or invalid input | The API handles the input according to its validation rules |
| API-05 | Submit empty or whitespace-only source code | The API rejects it or handles it according to the documented contract |
| API-06 | Inspect `/docs` | Interactive API documentation is accessible when the service is running |

### B. AI Detector Tests

| ID | Test scenario | Expected result |
|---|---|---|
| AI-01 | Compare identical source-code submissions | The detector reports very high or complete similarity for the tested identical inputs |
| AI-02 | Compare code with formatting or comment changes | The detector demonstrates its documented tolerance to formatting and comments |
| AI-03 | Compare code with renamed identifiers | The detector returns measured scores; reduced similarity is possible |
| AI-04 | Compare unrelated implementations | The detector generally reports lower similarity than for identical code |
| AI-05 | Compare submissions containing a shared code fragment | The detector identifies similarity where its supported matching logic permits |
| AI-06 | Submit malformed or unsupported source code | The detector handles the input safely and returns an appropriate result or validation error |
| AI-07 | Review a short source-code comparison | Any applicable reliability warning is included in the result |

Similarity scores are heuristic measurements. They must not be interpreted as definitive proof of plagiarism.

### C. Blockchain Tests

| ID | Test scenario | Expected result |
|---|---|---|
| BC-01 | Register a valid, previously unregistered fingerprint | Registration succeeds and the contract emits its registration event |
| BC-02 | Verify a registered fingerprint | The registered status, owner address, and timestamp match the recorded data |
| BC-03 | Verify an unregistered fingerprint | The contract reports that the fingerprint is not registered |
| BC-04 | Register the same fingerprint twice | The second registration reverts as a duplicate |
| BC-05 | Attempt to register a zero fingerprint | The contract rejects the registration |
| BC-06 | Register two distinct fingerprints | Both can be registered independently |
| BC-07 | Restart the local development chain | The tester checks whether deployment and registration state need to be recreated |

Local blockchain data may not persist after the development network is restarted. Record the network and contract address used for each run.

### D. Integration Tests

| ID | Test scenario | Expected result |
|---|---|---|
| INT-01 | Submit source code through the backend analysis endpoint | The response contains the expected analysis fields |
| INT-02 | Register a project using the configured frontend and blockchain | The interface reports success only when the registration is confirmed |
| INT-03 | Verify a registered project through the supported verification workflow | The result agrees with the blockchain record |
| INT-04 | Verify an unregistered project | The application reports that no registration was found |
| INT-05 | Submit the same project fingerprint again | Duplicate handling is consistent with the contract and API design |
| INT-06 | Stop a required service and retry an operation | The application handles the failure without falsely reporting success |
| INT-07 | Compare code and check its registration record | Similarity analysis and blockchain verification are presented as separate results |

Execute an integration case only when the relevant connection between modules is implemented and configured.

## 6. Test Execution Procedure

1. Pull or open the intended project revision and record its commit ID.
2. Install dependencies using the instructions for each module.
3. Run the backend and confirm its health endpoint.
4. Execute the AI detector unit tests and evaluation scenarios.
5. Start the local blockchain and deploy the registry contract if required.
6. Execute the blockchain tests.
7. Run the applicable frontend-to-backend and frontend-to-blockchain workflows.
8. Record actual outcomes, errors, and evidence in `TEST_RESULTS.md`.
9. Re-run failed tests after fixes and record the final result separately from the initial result.

## 7. Entry and Exit Criteria

### Entry criteria

- Required dependencies are installed.
- The test environment is configured.
- The intended source-code revision is identified.
- Test inputs are available.

### Exit criteria

- All applicable planned tests have an execution status.
- Failures and known limitations are documented.
- No test is marked as passed without evidence.
- Critical integration issues are reported to the team.

## 8. Defect Reporting

For each defect, record:

- Defect ID
- Related test case
- Steps to reproduce
- Expected behavior
- Actual behavior
- Severity
- Evidence, such as sanitized logs or screenshots
- Status and resolution

## 9. Limitations

The local development environment may differ from production. Blockchain timestamps represent recorded transaction time, not proof of original authorship. Source-code similarity depends on the detector's algorithms and supported languages. Integration tests can only validate connections that are actually implemented and enabled.

## 10. Conclusion

This test plan establishes a structured approach for checking CodeProof's API, similarity detector, blockchain registry, and implemented integrations. Actual test outcomes will be documented separately to maintain a clear distinction between planned validation and verified results.
