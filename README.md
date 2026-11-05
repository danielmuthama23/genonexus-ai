# CRISPR-X Nexus

CRISPR-X Nexus is a working genomic intelligence prototype for disease screening, carrier-risk assessment, CRISPR workflow simulation, and AI-assisted DNA analysis. The repo currently includes a FastAPI backend, a static browser UI, a synthetic ATCG object-detection pipeline, and a set of verified genomic-risk and research workflows.

## Verified status

This project is currently working in the local environment and passes its automated checks.

- Backend API: verified working
- Static frontend: served locally and usable
- Disease scan and repair logic: verified working
- Drug ranking, molecule building, survival simulation, and ledger validation: verified working
- Genomic risk, consent, counselling, and CFTR variant endpoints: verified working
- Optional AI vision summaries: working with real OpenAI/Anthropic credentials; otherwise falls back to a deterministic template summary
- Current verification: pytest passes in the project virtual environment

## Project structure

```text
GenoNexus AI/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── mcp_server.py
│   │   ├── data/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── run.sh
│   └── .env.example
├── frontend/
│   └── index.html
├── datasets/
│   └── atcg_yolo/
├── yolo_atcg_model/
│   ├── __init__.py
│   ├── dataset.py
│   ├── infer.py
│   ├── README.md
│   ├── requirements.txt
│   └── train.py
├── README.md
├── docker-compose.yml
├── Procfile
├── render.yaml
├── requirements.txt
└── .venv/
```

## What is working right now

### Genomic intelligence and clinical workflow endpoints

The FastAPI app exposes a real backend for:

- gene and disease scanning against a reference sequence
- CRISPR design and repair logic (`/api/genome/*`)
- drug ranking for target genes (`/api/drug/rank`)
- molecule building and validation (`/api/molecule/build`)
- survival modeling (`/api/survival/simulate`)
- synthetic cohort and sequence generation (`/api/synthetic/*`)
- audit ledger operations (`/api/ledger/*`)
- genomic variant interpretation (`/api/v1/variants/interpret`)
- couple compatibility, consent, privacy, counselling, and report generation (`/api/v1/*`)
- CFTR variant catalog and genevision analysis (`/api/v1/genevision/*`)

### AI vision summary layer

The vision summarization flow supports:

- deterministic fallback summaries when no model is configured
- real OpenAI-compatible summaries when `OPENAI_API_KEY` is available
- real Anthropic summaries when `ANTHROPIC_API_KEY` is available
- provider status reporting via `/api/vision/status`

This is intended for research workflows; it is not a clinical diagnostic output path.

### Frontend experience

The static frontend in `frontend/index.html` is designed to provide a browser UI for:

- sequence inspection
- CRISPR repair workflows
- disease matching
- molecule construction lab
- vision/ATCG sequence review
- gene risk and compatibility simulations

It is served locally and interacts with the backend API.

### ATCG YOLO prototype

The repository includes a synthetic DNA object-detection workflow for letters A/T/C/G:

- `datasets/atcg_yolo/` contains the training dataset and labels
- `yolo_atcg_model/dataset.py` builds synthetic YOLO training examples
- `yolo_atcg_model/train.py` trains the model
- `yolo_atcg_model/infer.py` performs inference and supports PNG/JPG/PDF inputs

This project is best understood as a research prototype and educational workflow rather than a validated clinical sequencing system.

## Quick start

### 1) Create and activate the environment

```bash
cd "/home/dti/Documents/dan_soi-code/GenoNexus AI"
python3 -m venv .venv
. .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 3) Start the backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

- http://localhost:8000
- http://localhost:8000/docs

### 4) Start the frontend

```bash
cd ../frontend
python3 -m http.server 8080
```

Open:

- http://localhost:8080

## Useful commands

### Run the full test suite

```bash
cd "/home/dti/Documents/dan_soi-code/GenoNexus AI"
. .venv/bin/activate
pytest -q
```

### Run the YOLO dataset builder

```bash
cd "/home/dti/Documents/dan_soi-code/GenoNexus AI"
. .venv/bin/activate
python -m yolo_atcg_model.dataset --dataset-root ./datasets/atcg_yolo --images-per-class 60
```

### Train the prototype model

```bash
cd "/home/dti/Documents/dan_soi-code/GenoNexus AI"
. .venv/bin/activate
python -m yolo_atcg_model.train --dataset-root ./datasets/atcg_yolo --epochs 30 --imgsz 1024
```

### Run inference on an image or PDF

```bash
cd "/home/dti/Documents/dan_soi-code/GenoNexus AI"
. .venv/bin/activate
python -m yolo_atcg_model.infer --model ./datasets/atcg_yolo/runs/atcg_medical_model/weights/best.pt --image ./sample.png
```

## Verified local test result

From the project root, the current verified result is:

```text
24 passed in 8.74s
```

## Limits and disclaimers

This is a research prototype and educational platform, not a regulated clinical system.

- it models genomic workflows and decision-support logic rather than real patient care
- ATCG detection is based on synthetic and image-based letter recognition, not direct sequencing instrumentation or validated clinical analytics
- variant interpretation and carrier-risk outputs are exploratory and should be treated as decision-support only
- real Hedera and LLM integrations are credential-gated and remain optional

## Notes

The repo combines a functional FastAPI application with experimental ML, synthetic-data tooling, and a browser UI. The goal is to provide a credible end-to-end prototype for genomic risk analysis, gene editing simulation, and visual sequence interpretation while clearly separating research workflows from clinical-grade use.

## Project workflow timeline

This gallery records the project progression in snapshot order, from the earliest captured workflow state to the latest. Each image reflects a chronological milestone in the app's development and UX flow.

### 1) Initial workflow snapshot

![Workflow snapshot 1](screenshots/Screenshot%202026-11-06%20at%2001-10-55%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 2) Early gene-risk and platform iteration

![Workflow snapshot 2](screenshots/Screenshot%202026-11-06%20at%2001-11-17%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 3) Prototype refinement and interface review

![Workflow snapshot 3](screenshots/Screenshot%202026-11-06%20at%2001-11-41%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 4) Continued workflow review

![Workflow snapshot 4](screenshots/Screenshot%202026-11-06%20at%2001-12-06%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 5) Risk-analysis state progression

![Workflow snapshot 5](screenshots/Screenshot%202026-11-06%20at%2001-12-35%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 6) Next-stage workflow capture

![Workflow snapshot 6](screenshots/Screenshot%202026-11-06%20at%2001-13-06%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 7) UI progression and sequence assessment

![Workflow snapshot 7](screenshots/Screenshot%202026-11-06%20at%2001-13-29%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 8) Feature polish and deeper workflow review

![Workflow snapshot 8](screenshots/Screenshot%202026-11-06%20at%2001-13-45%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 9) Workflow refinement milestone

![Workflow snapshot 9](screenshots/Screenshot%202026-11-06%20at%2001-14-06%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 10) Interface maturity and review

![Workflow snapshot 10](screenshots/Screenshot%202026-11-06%20at%2001-14-25%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 11) Deepened platform workflow review

![Workflow snapshot 11](screenshots/Screenshot%202026-11-06%20at%2001-14-53%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

### 12) Latest captured workflow state

![Workflow snapshot 12](screenshots/Screenshot%202026-11-06%20at%2001-15-06%20CRISPR-X%20Nexus%20%E2%80%94%20Genomic%20Risk%20Intelligence%20Platform.png)

This timeline is intentionally kept lightweight and chronological so the project story is easy to follow in the repository without adding unrelated or oversized assets.
