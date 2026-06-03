# ML-Integrated Private Blockchain for Securing Clinical Trials Data

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react&logoColor=white)](https://reactjs.org)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.19-purple?style=flat-square&logo=solidity&logoColor=white)](https://soliditylang.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0.3-orange?style=flat-square)](https://xgboost.readthedocs.io)

An enterprise-grade, end-to-end private blockchain architecture designed to guarantee the integrity, auditability, and regulatory compliance of clinical trial records. The system combines secure client-side **SHA-256** Cryptographic Hashing, decentralized storage via **IPFS**, on-chain smart contract validation, a robust machine learning fraud-detection gate utilizing **8 distinct ML models** (led by XGBoost), and an automated AI-driven governance loop.

---

## Technical Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│             👤 Clinical Trial Coordinator UI           │
└──────────────────────────┬─────────────────────────────┘
                           │ (CSV Ingestion)
                           ▼
┌────────────────────────────────────────────────────────┐
│         Step 1: Ingestion & Schema Verification        │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│        Step 2: SHA-256 Hashing & Avalanche Demo        │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│     Step 3: Transaction Creation (Trial ID & Hash)     │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│    Step 4: Role-Based Node Access (RBAC Validation)    │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│          Step 5: Pre-Chain ML Verification Gate        │
└──────────────────────────┬─────────────────────────────┘
                           ├──────────────────────────────┐
                    (If Valid Data)              (If Anomalous / >25%)
                           ▼                              ▼
┌────────────────────────────────────────┐  ┌────────────────────────────┐
│ Step 6: Smart Contract Protocol Check  │  │ ❌ Reject & Flag Dataset   │
│   (Sequence Check & Patient Consent)   │  │    (Admin Review Queue)    │
└──────────────────┬─────────────────────┘  └────────────────────────────┘
                   ▼
┌────────────────────────────────────────┐
│    Step 7/8: PoA & DPoS Consensus      │
│      (Reputation-Weighted Vote)        │
└──────────────────┬─────────────────────┘
                   ▼
┌────────────────────────────────────────┐
│  Step 9: Commit & Append Block to Chain│
└──────────────────┬─────────────────────┘
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐┌──────────────────┐
│  Step 10: IPFS   ││ Step 10: Ledger  │
│(Encrypted Record)││(CID + SHA-256)   │
└────────┬─────────┘└────────┬─────────┘
         └─────────┬─────────┘
                   ▼
┌────────────────────────────────────────┐
│    Step 11: Compliance Audit Logging   │
│         (HIPAA / GDPR / GCP)           │
└──────────────────┬─────────────────────┘
                   ▼
┌────────────────────────────────────────┐
│     Step 12: AI Governance Engine      │
│    (Reputation Scoring & Telemetry)    │
└────────────────────────────────────────┘
```



---

## Directory Structure

```
blockchainproject/
├── backend/                  # FastAPI Core Gateway (Steps 1–4, 7–12)
│   ├── main.py              # Unified API routes & backend orchestration
│   ├── hashing.py           # SHA-256 cryptography, avalanche demo, and verify routes
│   ├── transaction.py       # Pydantic transaction schemas & Mempool transaction handling
│   ├── nodes.py             # Role-Based Access Control (RBAC) Node registry
│   ├── config.py            # Global environment variable and system settings
│   ├── security.py          # Node keypair (ED25519) cryptographic signature signing
│   ├── persistence.py       # SQLite database persistence logic
│   └── contract_client.py   # Web3.py client connector for Ethereum/Hardhat smart contracts
├── blockchain/              # Ledger & Protocol Operations
│   ├── chain.py             # Blockchain block structure, Merkle Tree implementation, and verification
│   ├── consensus.py         # Proof of Authority (PoA) reputation logic & DPoS delegate selection
│   └── governance.py        # AI telemetry engine, metric log tracking, and drift analysis
├── contracts/               # Solidity Smart Contracts (Hardhat Suite)
│   ├── src/
│   │   └── ClinicalTrialRegistry.sol  # Solidity registry enforcing sequence validation & RBAC
│   ├── scripts/
│   │   └── deploy.js        # Contract deployment scripts
│   ├── hardhat.config.js    # Hardhat compilation and local network config
│   └── package.json         # Smart contract dev dependencies
├── ml/                      # Machine Learning Pre-chain Pipeline
│   ├── train_models.py      # Standard models training (LR, SVM, RF, DT, KNN, NB, XGBoost, MLP)
│   ├── preprocess_pipeline.py # Dataset preprocessing, categorical encoding, and model pipelines
│   ├── saved_models/        # Serialized models (.joblib) & baseline validation summary
│   └── plots/               # Pre-generated ROC/AUC curves and evaluation charts
├── ipfs/                    # IPFS Storage Wrapper
│   └── ipfs_client.py       # Client-side AES-256-GCM encryption & IPFS daemon connector
├── dataset/                 # Source Datasets
│   ├── generate_dataset.py  # Script generating clinical trial cohorts with controlled anomalies
│   └── clinical_trials.csv  # Synthetic dataset of 2,000 trial records (~23% anomalies)
├── start.sh                 # Unix shell daemon launcher
├── package.json             # Root-level unified run commands
└── requirements.txt         # Core Python libraries
```

---

## Quick Start Guide

### Prerequisites
* **Python**: Version 3.10 or higher
* **Node.js**: Version 18.0 or higher
* **IPFS Daemon**: (Optional) IPFS desktop/daemon for real nodes. The client falls back to **Mock Mode** automatically if the IPFS daemon is unreachable.
* **Ethereum Virtual Machine**: (Optional) Ganache or Hardhat node running on `http://127.0.0.1:8545` for active Solidity deployment.

---

### Step-by-Step Installation

#### 1. Setup the Python Virtual Environment
Initialize a local virtual environment to isolate the package scope:

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

#### 2. Generate the Synthetic Dataset
Run the data generator to construct a clinical cohort complete with demographic distributions, adverse flags, and synthetic anomalies (~23% anomalies matching real-world clinical trial data inconsistencies):
```bash
python dataset/generate_dataset.py
```
This produces `dataset/clinical_trials.csv` with 2,000 records.

---

#### 3. Train the Pre-chain ML Classification Models
Pre-train the 8 classifiers used to inspect trial transactions before block proposal:
```bash
python ml/train_models.py
```
This trains all models, outputs performance statistics, stores serialized models in `ml/saved_models/`, and generates comparison charts under `ml/plots/`.

---

#### 4. Run the Dev Server

You can run the frontend, backend, and database dependencies in one step using the root level scripts:

```bash
# Run the unified launcher (calls start.sh, sets up both ports)
npm run start
```
Alternatively, start the components manually:

**Backend (FastAPI):**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs are available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

**Frontend (React UI):**
```bash
cd frontend-app
npm install
npm start
```
The client dashboard opens at **[http://localhost:3000](http://localhost:3000)**.

---

#### 5. Deploy Smart Contracts (Optional)
Run a local Hardhat node or Ganache instance, and deploy the registry contract:
```bash
cd contracts
npm install
npx hardhat run scripts/deploy.js --network localhost
```

---

## 12-Step Implementation Mapping

| Step | Platform Capability | Module File / API Route |
| :--- | :--- | :--- |
| **1** | Dataset Ingestion & Validation Check | `backend/main.py` ➔ `/api/dataset/upload` |
| **2** | Cryptographic Hashing & Avalanche Demo | `backend/hashing.py` ➔ `/api/hash/avalanche` |
| **3** | Transaction Creation & Pool Submission | `backend/transaction.py` ➔ `/api/transactions/submit` |
| **4** | RBAC Node Validation Rules | `backend/nodes.py` ➔ `/api/nodes/register` |
| **5** | Machine Learning Fraud Screening Gate | `ml/train_models.py` ➔ `/api/ml/predict` |
| **6** | Smart Contract Protocol Sequence Validation | `contracts/src/ClinicalTrialRegistry.sol` |
| **7** | PoA Reputation-weighted Protocol Proposals | `blockchain/consensus.py` ➔ `/api/consensus/propose` |
| **8** | Delegate Elections (DPoS Extension) | `blockchain/consensus.py::DPoSElection` |
| **9** | Block Creation & Ledger Verification | `blockchain/chain.py` ➔ `/api/blockchain/mine` |
| **10** | AES-256 Encryption & IPFS Pinning | `ipfs/ipfs_client.py` ➔ `/api/ipfs/upload` |
| **11** | Compliance Audit Logger | `backend/main.py` ➔ `/api/governance/audit-trial` |
| **12** | AI Governance & Scoring Feedback Loop | `blockchain/governance.py` ➔ `/api/governance/health` |

---

## Machine Learning Fraud Gate Performance

The pre-chain screening block uses an **XGBoost Classifier** as the gate model. Under default clinical anomaly settings, models score the following baseline metrics:

| Rank | Model Pipeline | Accuracy | Precision | Recall | F1-Score | AUC-ROC | Train Time | Predict Time | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | **XGBoost** 🏆 | **86.82%** | **100.00%**| **40.63%** | **55.14%** | **0.7400** | **0.5574s** | **0.0164s** | **Active Gate Filter** |
| **#2** | Decision Tree | 85.62% | 100.00%| 36.42% | 53.40% | 0.7143 | 0.0257s | 0.0011s | Available Pipeline |
| **#3** | Random Forest | 85.62% | 100.00%| 36.42% | 53.40% | 0.7230 | 0.1760s | 0.0440s | Available Pipeline |
| **#4** | SVM (RBF) | 85.57% | 99.43% | 36.42% | 53.31% | 0.7195 | 12.0003s| 1.4998s | Available Pipeline |
| **#5** | KNN (K=5) | 84.86% | 89.05% | 37.68% | 52.96% | 0.7320 | 0.0219s | 0.1600s | Available Pipeline |
| **#6** | Logistic Regression| 85.05% | 96.53% | 35.16% | 51.54% | 0.7083 | 0.0205s | 0.0040s | Available Pipeline |
| **#7** | Naive Bayes | 83.81% | 80.27% | 37.68% | 51.29% | 0.6970 | 0.0053s | 0.0110s | Available Pipeline |
| **#8** | ANN (MLP) | 84.76% | 97.55% | 33.47% | 49.84% | 0.6938 | 7.8032s | 0.2051s | Available Pipeline |


---

## Primary API Gateways

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/` | Retrieve node status, chain size, and system configurations. |
| **POST** | `/api/dataset/upload` | Stream clinical CSVs, run ML screening, and reject fraud datasets. |
| **POST** | `/api/hash/avalanche` | Demo the SHA-256 avalanche effect on single byte changes. |
| **POST** | `/api/transactions/submit` | Sign transaction inputs and check against the active ML Gate. |
| **POST** | `/api/blockchain/mine` | Drain the mempool and commit transaction batches to a new block. |
| **GET** | `/api/blockchain/verify` | Perform a hash-link validation sequence over the active ledger. |
| **POST** | `/api/ipfs/upload` | Encrypt datasets using AES-256 and pin the content-addressed blocks. |
| **GET** | `/api/governance/health` | Track network consensus stats, average block times, and accuracy telemetry. |

---

## Solidity Smart Contract Hookups

* `registerNode(address, role, org)`: Instantiates a network identity with static permissions.
* `submitTrial(trialId, dataHash, ipfsCid, dropoutRate, mlApproved, compliance)`: Pins a verified trial index on-chain.
* `verifyConsent(trialId, consentHash)`: Cryptographically registers patient consent before active inclusion.
* `advancePhase(trialId)`: Restricts advancement sequence enforcing order `Phase I ➔ II ➔ III ➔ IV`.
* `haltTrial(trialId, reason)`: Emits an emergency alert, locking modifications.
* `auditTrial(trialId, action)`: Compliance-specific tracker storing regulatory reviews.

---

## Clinical trial Schema Fields

| Schema Field | Data Type | Constraint Validation details |
| :--- | :--- | :--- |
| `trial_id` | String | Unique registry code (e.g. NCT03000001) |
| `patient_id` | String | Hashed index preventing patient identification |
| `age_group` | Categorical | Canonical groups: `<18`, `18-35`, `36-50`, `51-65`, `65+` |
| `drug_name` | String | Blinded/hashed study drug identifier |
| `dosage_level_mg` | Float | Active substance amount administered |
| `phase` | Categorical | Permissible stages: `I`, `II`, `III`, `IV` |
| `response_time_days` | Integer | Observation duration |
| `adverse_event` | Categorical | Classification: `None`, `Mild`, `Moderate`, `Severe`, `Life-threatening` |
| `adverse_event_flag`| Integer | Boolean (0/1) indicating severe adverse occurrences |
| `consent_hash` | String | SHA-256 verification hash matching physical signatures |
| `manipulated` | Integer | **Target Label**: Valid (0) vs Anomalous/Manipulated (1) |

---

## Reference Specifications

* **Clinical Trial Registry**: [ClinicalTrials.gov Standards](https://clinicaltrials.gov/)
* **HIPAA/GDPR Directives**: [US HHS Privacy Rules](https://www.hhs.gov/hipaa/index.html)
* **FDA Good Clinical Practices**: [FDA GCP Guidelines](https://www.fda.gov/)
* **Upstream Inspiration**: [medicine-trial reference code](https://github.com/PrathamPShetty/medicine-trial.git)
