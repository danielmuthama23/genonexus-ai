"""
CRISPR-X Backend — FastAPI service wrapping the same genome-editing, disease
scanning, drug scoring, molecule lab, survival simulation, and audit ledger
logic used by the frontend, so either side (browser-only, or browser+backend)
produces consistent results. See README.md for the honest scope notes.
"""
from typing import List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .data.disease_db import DISEASE_DB, REFERENCE_SEQUENCE, find_disease
from .data import synthetic
from .data.genomecrispr_loader import build_task_queue, load_genomecrispr_records
from .services import (
    genome_service, disease_service, drug_service,
    molecule_lab_service, survival_service, hedera_service, vision_summary_service,
)
from .services.genevision_service import analyze_sequence, list_known_cftr_variants
from .services.genomic_risk_service import (
    analyze_individual_profile,
    ask_counselling_question,
    compare_couple_risk,
    evaluate_inheritance,
    generate_inherited_risk_report,
    get_impact_dashboard,
    get_privacy_audit,
    grant_consent,
    interpret_variant,
    request_counselling,
    revoke_consent,
)
from .services.ledger_service import ledger

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- request/response models ----------

class SequencePayload(BaseModel):
    sequence: List[str]


class DesignGrnaRequest(BaseModel):
    sequence: List[str]
    pos: int


class RepairRequest(BaseModel):
    sequence: List[str]
    pos: int
    normal: str
    mutant: str
    strategy: str  # hdr | nhej | base | prime


class DrugRankRequest(BaseModel):
    target_gene: str


class MoleculeBuildRequest(BaseModel):
    atoms: List[str]
    bonds: List[Tuple[int, int, int]]
    name: Optional[str] = "Custom molecule"
    target_gene: Optional[str] = None


class SurvivalRequest(BaseModel):
    efficacy: float
    n_per_arm: Optional[int] = 40
    followup_months: Optional[int] = 24
    seed: Optional[int] = None


class LedgerAppendRequest(BaseModel):
    action: str
    data: dict


class Detection(BaseModel):
    label: str
    confidence: float


class VisionSummaryRequest(BaseModel):
    detections: List[Detection]


# ---------- health / meta ----------

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


@app.get("/api/v1/health")
def v1_health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "platform": "CRISPR-X Nexus",
        "capabilities": [
            "genomic_intelligence",
            "variant_interpretation",
            "risk_assessment",
            "consent_guardrails",
            "clinical_navigation",
            "genevision_ai",
        ],
    }


@app.get("/api/reference")
def get_reference():
    return {"sequence": REFERENCE_SEQUENCE, "length": len(REFERENCE_SEQUENCE)}


@app.get("/api/diseases")
def get_diseases():
    return DISEASE_DB


@app.get("/api/genomecrispr/records")
def genomecrispr_records(limit: int = 10):
    return load_genomecrispr_records(limit=limit)


@app.get("/api/genomecrispr/tasks")
def genomecrispr_tasks(limit: int = 10):
    return build_task_queue(limit=limit)


@app.get("/api/genomecrispr/summary")
def genomecrispr_summary():
    rows = load_genomecrispr_records(limit=None)
    genes = sorted({row["symbol"] for row in rows if row.get("symbol")})
    screen_types = sorted({row["screentype"] for row in rows if row.get("screentype")})
    return {"total_rows": len(rows), "genes": genes[:10], "screen_types": screen_types, "unique_genes": len(genes)}


# ---------- disease scanning ----------

@app.post("/api/disease/scan")
def scan_disease(payload: SequencePayload):
    return disease_service.scan(payload.sequence)


# ---------- CRISPR genome editing ----------

@app.post("/api/genome/design-grna")
def design_grna(req: DesignGrnaRequest):
    return genome_service.design_grna(req.sequence, req.pos)


@app.post("/api/genome/cut")
def cut(req: DesignGrnaRequest):
    return genome_service.cut(req.sequence, req.pos)


@app.post("/api/genome/repair")
def repair(req: RepairRequest):
    try:
        seq, msg = genome_service.repair(req.sequence, req.pos, req.normal, req.mutant, req.strategy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"sequence": seq, "message": msg}


# ---------- drug candidate screening ----------

@app.post("/api/drug/rank")
def rank_drugs(req: DrugRankRequest):
    return drug_service.rank_compounds(req.target_gene)


# ---------- molecule construction lab ----------

@app.post("/api/molecule/build")
def build_molecule(req: MoleculeBuildRequest):
    try:
        return molecule_lab_service.build_and_score(req.atoms, req.bonds, req.name, req.target_gene)
    except molecule_lab_service.InvalidMoleculeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- clinical outcome simulator ----------

@app.post("/api/survival/simulate")
def simulate_survival(req: SurvivalRequest):
    return survival_service.run_simulation(
        efficacy=req.efficacy, n_per_arm=req.n_per_arm,
        followup_months=req.followup_months, seed=req.seed,
    )


# ---------- synthetic data ----------

@app.get("/api/synthetic/cohort")
def get_cohort(n: int = 6, seed: int = 42):
    return synthetic.generate_cohort(n=n, seed=seed)


@app.get("/api/synthetic/reads")
def get_reads(n_samples: int = 6, error_rate: float = 0.04, seed: int = 7):
    return synthetic.generate_reads(REFERENCE_SEQUENCE, n_samples=n_samples, error_rate=error_rate, seed=seed)


# ---------- audit ledger ----------

@app.post("/api/ledger/append")
def ledger_append(req: LedgerAppendRequest):
    return ledger.append(req.action, req.data)


@app.get("/api/ledger")
def ledger_list():
    return ledger.chain


@app.get("/api/ledger/verify")
def ledger_verify():
    return ledger.verify()


# ---------- Hedera (real SDK, credential-gated) ----------

@app.get("/api/hedera/status")
def hedera_status():
    return hedera_service.status()


# ---------- genomic intelligence ----------

@app.post("/api/v1/variants/interpret")
def interpret_variant_endpoint(payload: dict):
    return interpret_variant(payload)


@app.post("/api/v1/compatibility/compare")
def compare_couple_endpoint(payload: dict):
    try:
        return compare_couple_risk(
            payload.get("individual_a", {}),
            payload.get("individual_b", {}),
            bool(payload.get("consent", False)),
            session_user=payload.get("session_user"),
            consent_status=payload.get("consent_status"),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@app.post("/api/v1/consent/grant")
def consent_grant(payload: dict):
    return grant_consent(
        payload.get("record_type", "comparison"),
        payload.get("subject_reference", "anonymous-user"),
        payload.get("permission", "couple_assessment"),
        role=payload.get("role", "individual"),
    )


@app.post("/api/v1/consent/revoke")
def consent_revoke(payload: dict):
    return revoke_consent(
        payload.get("record_type", "comparison"),
        payload.get("subject_reference", "anonymous-user"),
        payload.get("permission", "couple_assessment"),
        role=payload.get("role", "individual"),
    )


@app.get("/api/v1/privacy/audit")
def privacy_audit():
    return {"audit_records": get_privacy_audit()}


@app.post("/api/v1/profiles/analyze")
def profile_analyze(payload: dict):
    return analyze_individual_profile(payload)


@app.post("/api/v1/inheritance/analyze")
def inheritance_analyze(payload: dict):
    return evaluate_inheritance(
        payload.get("pattern", "autosomal_recessive"),
        payload.get("genotype_a", "Aa"),
        payload.get("genotype_b", "Aa"),
    )


@app.post("/api/v1/counselling/ask")
def counselling_ask(payload: dict):
    return ask_counselling_question(payload.get("question", ""), payload.get("profile_context"))


@app.post("/api/v1/counselling/request")
def counselling_request(payload: dict):
    return request_counselling(payload)


@app.get("/api/v1/impact/dashboard")
def impact_dashboard():
    return get_impact_dashboard()


@app.post("/api/v1/reports/generate")
def risk_report(payload: dict):
    return generate_inherited_risk_report(
        payload.get("profile", {}),
        payload.get("partner_profile"),
    )


@app.get("/api/v1/genevision/variants")
def genevision_variants():
    return list_known_cftr_variants()


@app.post("/api/v1/genevision/analyze")
def genevision_analyze(payload: dict):
    try:
        return analyze_sequence(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------- AI vision summary (real Anthropic API, credential-gated) ----------

@app.get("/api/vision/status")
def vision_status():
    return vision_summary_service.status()


@app.post("/api/vision/summarize")
def vision_summarize(req: VisionSummaryRequest):
    detections = [d.model_dump() for d in req.detections]
    return vision_summary_service.summarize(detections)


@app.post("/api/hedera/create-topic")
def hedera_create_topic():
    """Create a real HCS topic. Requires HEDERA_ACCOUNT_ID/HEDERA_PRIVATE_KEY
    to be set — raises a clear 400 otherwise rather than pretending to succeed."""
    try:
        return hedera_service.create_topic()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/hedera/anchor-latest-block")
def hedera_anchor_latest_block():
    """Submit the most recent local ledger block as a real HCS message.
    Requires Hedera to be fully configured (account, key, and topic id)."""
    if not ledger.chain:
        raise HTTPException(status_code=400, detail="Ledger is empty — append a block first")
    try:
        return hedera_service.submit_ledger_block(ledger.chain[-1])
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
