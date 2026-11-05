"""Minimal but real tests — run with: pytest tests/ -v"""
import sys
import os
from pathlib import Path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.data.disease_db import REFERENCE_SEQUENCE
from app.data.genomecrispr_loader import load_genomecrispr_records
from app.services import molecule_lab_service
from app.services.atcg_yolo_service import build_demo_dataset

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_disease_scan_detects_sca_mutation():
    seq = list(REFERENCE_SEQUENCE)
    seq[6] = "T"  # sickle cell mutant base
    r = client.post("/api/disease/scan", json={"sequence": seq})
    matches = [d["id"] for d in r.json() if d["match"]]
    assert "sca" in matches


def test_hdr_repair_restores_normal_base():
    seq = list(REFERENCE_SEQUENCE)
    seq[6] = "T"
    r = client.post("/api/genome/repair", json={
        "sequence": seq, "pos": 6, "normal": "A", "mutant": "T", "strategy": "hdr"
    })
    assert r.json()["sequence"][6] == "A"


def test_drug_ranking_returns_all_compounds():
    r = client.post("/api/drug/rank", json={"target_gene": "HBB"})
    data = r.json()
    assert len(data) == 8
    assert all("affinity_score" in c for c in data)


def test_molecule_lab_builds_valid_molecule():
    r = client.post("/api/molecule/build", json={
        "atoms": ["C", "C", "O"], "bonds": [[0, 1, 1], [1, 2, 1]], "name": "ethanol-test"
    })
    assert r.status_code == 200
    assert r.json()["formula"] == "C2H6O"


def test_molecule_lab_rejects_invalid_valence():
    r = client.post("/api/molecule/build", json={
        "atoms": ["C", "N", "N", "N", "N", "N"],
        "bonds": [[0, 1, 1], [0, 2, 1], [0, 3, 1], [0, 4, 1], [0, 5, 1]],
    })
    assert r.status_code == 400


def test_ledger_chain_integrity():
    client.post("/api/ledger/append", json={"action": "a", "data": {}})
    client.post("/api/ledger/append", json={"action": "b", "data": {}})
    r = client.get("/api/ledger/verify")
    assert r.json()["ok"] is True


def test_survival_simulation_shape():
    r = client.post("/api/survival/simulate", json={"efficacy": 0.3, "n_per_arm": 10, "seed": 1})
    data = r.json()
    assert "log_rank_p" in data
    assert 0 <= data["log_rank_p"] <= 1


def test_hedera_not_configured_by_default():
    r = client.get("/api/hedera/status")
    assert r.json()["configured"] is False


def test_vision_summary_template_fallback():
    r = client.post("/api/vision/summarize", json={
        "detections": [{"label": "person", "confidence": 0.9}, {"label": "laptop", "confidence": 0.7}]
    })
    data = r.json()
    assert data["source"] == "template"
    assert "person" in data["summary"]


def test_vision_summary_uses_openai_when_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from app.services import vision_summary_service
    called = {}

    class DummyResponse:
        def __init__(self):
            self.choices = [type("Choice", (), {"message": type("Message", (), {"content": "The image contains a nucleotide pattern consistent with CFTR analysis."})()})()]

    class DummyClient:
        def __init__(self, api_key=None):
            called["key"] = api_key
        def chat(self):
            return type("Chat", (), {"completions": type("Completions", (), {"create": lambda self, **kwargs: DummyResponse()})()})()

    monkeypatch.setattr(vision_summary_service, "_OPENAI_SDK_AVAILABLE", True, raising=False)
    monkeypatch.setattr(vision_summary_service, "OpenAI", DummyClient, raising=False)
    result = vision_summary_service.summarize([{"label": "A", "confidence": 0.9}, {"label": "T", "confidence": 0.8}])
    assert result["source"] == "llm"
    assert "CFTR" in result["summary"] or "nucleotide" in result["summary"].lower()


def test_detect_atcg_sequence_helpers_reconstruct_ordered_bases():
    from app.services.atcg_yolo_service import reconstruct_sequence_from_detections
    detections = [
        {"label": "A", "confidence": 0.95, "x_center": 0.15},
        {"label": "T", "confidence": 0.97, "x_center": 0.35},
        {"label": "G", "confidence": 0.94, "x_center": 0.55},
        {"label": "C", "confidence": 0.91, "x_center": 0.75},
    ]
    assert reconstruct_sequence_from_detections(detections) == "ATGC"


def test_reconstruct_sequence_accepts_default_reference_string():
    from app.services.atcg_yolo_service import reconstruct_sequence_from_detections
    expected = "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTG"
    assert reconstruct_sequence_from_detections(expected) == expected
    assert reconstruct_sequence_from_detections(list(expected)) == expected


def test_reconstruct_sequence_deduplicates_noisy_repeated_g_streaks():
    from app.services.atcg_yolo_service import reconstruct_sequence_from_detections
    detections = [
        {"label": "A", "confidence": 0.97, "x_center": 0.10},
        {"label": "G", "confidence": 0.91, "x_center": 0.11},
        {"label": "G", "confidence": 0.90, "x_center": 0.12},
        {"label": "G", "confidence": 0.89, "x_center": 0.13},
        {"label": "G", "confidence": 0.88, "x_center": 0.14},
        {"label": "G", "confidence": 0.87, "x_center": 0.15},
        {"label": "G", "confidence": 0.86, "x_center": 0.16},
        {"label": "T", "confidence": 0.95, "x_center": 0.30},
    ]
    result = reconstruct_sequence_from_detections(detections)
    assert "GGGGGG" not in result
    assert result.startswith("AG")


def test_frontend_preserves_input_sequence_without_hardcoded_overrides():
    html = Path(ROOT, "frontend", "index.html").read_text(encoding="utf-8")
    assert "SEQUENCE_RECONSTRUCTION_OVERRIDES" not in html
    assert "ATGGTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTG': 'GGGCCAGCGACCCGAGGAAAAGTCGCCGCC'" not in html


def test_genomecrispr_csv_loads_real_records():
    rows = load_genomecrispr_records(limit=5)
    assert len(rows) == 5
    assert all("sequence" in row and "symbol" in row for row in rows)
    assert rows[0]["symbol"] == "A1CF"


def test_platform_branding_and_genomic_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["app"] == "CRISPR-X Nexus"
    assert "genomic_intelligence" in payload["capabilities"]


def test_variant_interpretation_has_evidence_and_classification():
    r = client.post("/api/v1/variants/interpret", json={
        "gene": "HBB",
        "variant_id": "NM_000518.5:c.20A>T",
        "condition": "Sickle cell disease",
        "zygosity": "heterozygous",
        "inheritance": "autosomal_recessive",
        "classification": "Pathogenic"
    })
    assert r.status_code == 200
    payload = r.json()
    assert payload["classification"] == "Pathogenic"
    assert payload["evidence_level"] in {"established", "moderate"}
    assert "evidence" in payload
    assert "clinical_disclaimer" in payload


def test_couple_risk_assessment_for_shared_recessive_carriers():
    r = client.post("/api/v1/compatibility/compare", json={
        "individual_a": {"name": "A", "gene": "HBB", "status": "carrier", "pattern": "autosomal_recessive"},
        "individual_b": {"name": "B", "gene": "HBB", "status": "carrier", "pattern": "autosomal_recessive"},
        "consent": True,
    })
    assert r.status_code == 200
    payload = r.json()
    assert payload["risk_model"] == "autosomal_recessive"
    assert payload["affected_probability"] == 0.25
    assert payload["carrier_probability"] == 0.5
    assert payload["professional_review_required"] is True


def test_consent_revocation_blocks_pairing():
    client.post("/api/v1/consent/grant", json={
        "subject_reference": "person-1",
        "permission": "couple_assessment",
        "role": "individual",
    })
    client.post("/api/v1/consent/revoke", json={
        "subject_reference": "person-1",
        "permission": "couple_assessment",
        "role": "individual",
    })
    r = client.post("/api/v1/compatibility/compare", json={
        "individual_a": {"name": "A", "gene": "HBB", "status": "carrier", "pattern": "autosomal_recessive"},
        "individual_b": {"name": "B", "gene": "HBB", "status": "carrier", "pattern": "autosomal_recessive"},
        "consent": True,
        "session_user": {"role": "partner"},
        "consent_status": "revoked",
    })
    assert r.status_code == 403


def test_counselling_request_generates_summary_and_referral():
    r = client.post("/api/v1/counselling/request", json={
        "patient_name": "Sample Patient",
        "risk_summary": "Both partners are carriers for HBB.",
        "priority": "high",
    })
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "pending"
    assert "referral_id" in payload
    assert "molecular_summary" in payload


def test_impact_dashboard_reports_measured_metrics():
    r = client.get("/api/v1/impact/dashboard")
    assert r.status_code == 200
    payload = r.json()
    assert "genetic_risk_comprehension" in payload
    assert "counselling_referral_uptake" in payload
    assert "consent_compliance" in payload


def test_genevision_knows_cftr_reference_variants():
    r = client.get("/api/v1/genevision/variants")
    assert r.status_code == 200
    payload = r.json()
    assert "F508del" in {v["name"] for v in payload["variants"]}
    assert any(v["gene"] == "CFTR" for v in payload["variants"])


def test_genevision_extracts_and_matches_cftr_sequence():
    r = client.post("/api/v1/genevision/analyze", json={
        "sequence": "ATGCCTTCTTATGGTGTTTCCTGGATTATGCCTGGC",
        "source_type": "annotated_sequence",
        "reference_gene": "CFTR"
    })
    assert r.status_code == 200
    payload = r.json()
    assert payload["recognized_bases"]["A"] > 0
    assert payload["recognized_bases"]["T"] > 0
    assert payload["recognized_bases"]["G"] > 0
    assert payload["recognized_bases"]["C"] > 0
    assert payload["sequence"]
    assert payload["reference_matches"] or payload["candidate_variants"]


def test_atcg_yolo_demo_dataset_creates_images_and_labels(tmp_path):
    dataset_dir = tmp_path / "atcg_demo"
    dataset = build_demo_dataset(str(dataset_dir), examples_per_base=2)
    assert dataset["images"] > 0
    assert dataset["labels"] > 0
    assert (dataset_dir / "images" / "train").exists()
    assert (dataset_dir / "images" / "val").exists()
    label_files = list((dataset_dir / "images" / "train" / "labels").glob("*.txt"))
    assert label_files
    assert label_files[0].read_text().strip()


def test_atcg_infer_prepares_png_and_pdf_inputs(tmp_path):
    from yolo_atcg_model.infer import prepare_input_image

    png_path = tmp_path / "helix.png"
    png_path.write_bytes(b"fake-png")
    assert prepare_input_image(str(png_path)) == str(png_path)

    from PIL import Image

    pdf_path = tmp_path / "helix.pdf"
    image = Image.new("RGB", (320, 180), color="white")
    image.save(pdf_path, "PDF")
    converted = prepare_input_image(str(pdf_path))
    assert converted.endswith(".png")
    assert Path(converted).exists()


def test_genevision_reconstructs_sequence_from_yolo_detections():
    payload = {
        "detections": [
            {"label": "A", "confidence": 0.98, "x_center": 0.10, "y_center": 0.50},
            {"label": "T", "confidence": 0.96, "x_center": 0.30, "y_center": 0.50},
            {"label": "G", "confidence": 0.93, "x_center": 0.50, "y_center": 0.50},
            {"label": "C", "confidence": 0.92, "x_center": 0.70, "y_center": 0.50},
        ],
        "reference_gene": "CFTR",
    }
    r = client.post("/api/v1/genevision/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["sequence"] == "ATGC"
    assert data["source_type"] == "annotated_sequence"
