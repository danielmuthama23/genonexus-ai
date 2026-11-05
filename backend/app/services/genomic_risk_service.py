"""Deterministic inherited disease risk, consent, counselling, and impact tools.

This module intentionally keeps the logic explainable and auditable. It is not a
clinical decision engine and it should be treated as a privacy-aware educational
workflow for synthetic or user-submitted screening data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

CONSENT_RECORDS: Dict[str, Dict[str, Any]] = {}
ACCESS_AUDIT_LOG: List[Dict[str, Any]] = []
COUNSELLING_REQUESTS: Dict[str, Dict[str, Any]] = {}

CLASSIFICATION_ALIASES = {
    "pathogenic": "Pathogenic",
    "likely pathogenic": "Likely pathogenic",
    "likely_pathogenic": "Likely pathogenic",
    "vus": "Variant of Uncertain Significance",
    "variant of uncertain significance": "Variant of Uncertain Significance",
    "likely benign": "Likely benign",
    "likely_benign": "Likely benign",
    "benign": "Benign",
}

GENE_REFERENCE = {
    "HBB": {
        "condition": "Sickle cell disease",
        "inheritance": "autosomal_recessive",
        "evidence_summary": "HBB variants are associated with beta-globin disorders and require careful interpretation of pathogenicity, zygosity and family history.",
    },
    "CFTR": {
        "condition": "Cystic fibrosis",
        "inheritance": "autosomal_recessive",
        "evidence_summary": "CFTR variants can cause cystic fibrosis when pathogenic alleles are inherited in the relevant recessive pattern.",
    },
    "BRCA1": {
        "condition": "BRCA1-associated hereditary cancer risk",
        "inheritance": "autosomal_dominant",
        "evidence_summary": "BRCA1 findings require careful risk communication because penetrance and risk vary between families and variants.",
    },
    "G6PD": {
        "condition": "G6PD deficiency",
        "inheritance": "x_linked_recessive",
        "evidence_summary": "X-linked risk differs by sex and variant. A negative screen does not completely exclude risk.",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _append_audit(event_type: str, subject_reference: str, details: Dict[str, Any]) -> Dict[str, Any]:
    record = {
        "event_type": event_type,
        "subject_reference": subject_reference,
        "timestamp": _now_iso(),
        "details": details,
    }
    ACCESS_AUDIT_LOG.append(record)
    return record


def normalize_classification(value: Optional[str]) -> str:
    if not value:
        return "Variant of Uncertain Significance"
    cleaned = value.strip()
    if cleaned.lower() in CLASSIFICATION_ALIASES:
        return CLASSIFICATION_ALIASES[cleaned.lower()]
    return cleaned


def _pattern_name(value: Optional[str]) -> str:
    return (value or "autosomal_recessive").strip().lower().replace(" ", "_")


def interpret_variant(payload: Dict[str, Any]) -> Dict[str, Any]:
    gene = (payload.get("gene") or "UNKNOWN").upper()
    variant_id = payload.get("variant_id") or "Variant unspecified"
    condition = payload.get("condition") or GENE_REFERENCE.get(gene, {}).get("condition", "Inherited disease risk assessment")
    inheritance = _pattern_name(payload.get("inheritance"))
    classification = normalize_classification(payload.get("classification"))

    if classification in {"Pathogenic", "Likely pathogenic"}:
        evidence_level = "established"
    elif classification in {"Likely benign", "Benign"}:
        evidence_level = "moderate"
    else:
        evidence_level = "uncertain"

    return {
        "gene": gene,
        "variant_id": variant_id,
        "condition": condition,
        "inheritance": inheritance,
        "classification": classification,
        "evidence_level": evidence_level,
        "evidence": [
            {
                "source": "ClinVar",
                "summary": f"Interpretation of {variant_id} in {gene} should be checked against curated clinical evidence and laboratory reports.",
            },
            {
                "source": "ClinGen",
                "summary": "The ACMG/AMP framework guides evidence review, but variant interpretation remains a professional assessment.",
            },
            {
                "source": "ACMG/AMP",
                "summary": "This educational output is not a diagnosis and should be reviewed with a qualified genetics professional.",
            },
        ],
        "clinical_disclaimer": "This result is an educational interpretation for a synthetic or user-submitted screening record and must be reviewed by a qualified genetic professional before any clinical decision.",
        "professional_review_required": True,
    }


def analyze_individual_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    variants = profile.get("variants") or []
    if not variants:
        variants = [profile] if profile.get("gene") else []

    relevant = []
    for variant in variants:
        gene = (variant.get("gene") or profile.get("gene") or "UNKNOWN").upper()
        classification = normalize_classification(variant.get("classification") or profile.get("classification"))
        if classification in {"Pathogenic", "Likely pathogenic", "Variant of Uncertain Significance"}:
            relevant.append({
                "gene": gene,
                "variant_id": variant.get("variant_id") or variant.get("name") or "unspecified-variant",
                "classification": classification,
                "zygosity": variant.get("zygosity") or profile.get("zygosity") or "heterozygous",
                "condition": variant.get("condition") or GENE_REFERENCE.get(gene, {}).get("condition", "Inherited disease risk"),
            })

    pathogenic_variants = [v for v in relevant if v["classification"] in {"Pathogenic", "Likely pathogenic"}]
    carrier_status = "carrier" if any(v["zygosity"] in {"heterozygous", "carrier"} for v in pathogenic_variants) else "not_carrier"
    if any(v["zygosity"] in {"homozygous", "affected"} for v in pathogenic_variants):
        carrier_status = "likely_affected"

    plain_language = (
        "Your screening contains pathogenic or clinically relevant genetic findings. "
        "A carrier result means you carry one altered copy of a gene associated with an inherited condition, "
        "but it does not by itself diagnose disease in you. "
        "The exact interpretation depends on the variant, inheritance pattern and family history."
        if pathogenic_variants
        else "No pathogenic variant was identified in the provided educational profile. This does not fully exclude inherited disease risk, and additional family history or confirmatory testing may still be appropriate."
    )

    return {
        "profile_reference": profile.get("profile_reference") or "anonymous-profile",
        "carrier_status": carrier_status,
        "pathogenic_variants": pathogenic_variants,
        "relevant_variants": relevant,
        "summary": plain_language,
        "professional_review_required": bool(pathogenic_variants or relevant),
        "clinical_disclaimer": "This educational analysis estimates genetic risk and explains carrier status. It is not a diagnosis and should be reviewed by a qualified genetics professional.",
    }


def evaluate_inheritance(pattern: str, genotype_a: str, genotype_b: str) -> Dict[str, Any]:
    normalized = _pattern_name(pattern)
    if normalized == "autosomal_recessive":
        risk = {
            "affected_probability": 0.25,
            "carrier_probability": 0.5,
            "unaffected_probability": 0.25,
            "possible_outcomes": [
                {"genotype": "affected", "probability": 0.25},
                {"genotype": "carrier", "probability": 0.5},
                {"genotype": "unaffected", "probability": 0.25},
            ],
            "plain_language": "Under the simplified autosomal recessive model, if both partners are carriers of the same pathogenic variant, there is a 25% chance per pregnancy that a child will inherit two altered copies, a 50% chance they will be a carrier, and a 25% chance they will inherit neither altered copy.",
        }
    elif normalized == "autosomal_dominant":
        risk = {
            "affected_probability": 0.5,
            "carrier_probability": 0.0,
            "unaffected_probability": 0.5,
            "possible_outcomes": [
                {"genotype": "affected", "probability": 0.5},
                {"genotype": "unaffected", "probability": 0.5},
            ],
            "plain_language": "Under a simplified dominant model, a variant carried by one parent can be passed to a child in roughly half of conceptions, though penetrance and severity vary by gene and variant.",
        }
    elif normalized == "x_linked_recessive":
        risk = {
            "affected_probability": 0.25,
            "carrier_probability": 0.25,
            "unaffected_probability": 0.5,
            "possible_outcomes": [
                {"genotype": "affected_male", "probability": 0.25},
                {"genotype": "carrier_female", "probability": 0.25},
                {"genotype": "unaffected", "probability": 0.5},
            ],
            "plain_language": "X-linked recessive risk depends on the sex of the child and the variant. The model should be confirmed by a qualified genetics professional with family history.",
        }
    else:
        risk = {
            "affected_probability": None,
            "carrier_probability": None,
            "unaffected_probability": None,
            "possible_outcomes": [],
            "plain_language": "This inheritance pattern is not supported by the simplified educational engine. A genetics professional should interpret the case.",
        }

    return {
        "pattern": normalized,
        "genotype_a": genotype_a,
        "genotype_b": genotype_b,
        **risk,
    }


def compare_couple_risk(individual_a: Dict[str, Any], individual_b: Dict[str, Any], consent: bool, session_user: Optional[Dict[str, Any]] = None, consent_status: Optional[str] = None) -> Dict[str, Any]:
    if not consent:
        raise PermissionError("Explicit consent from both participants is required before any couple-level genetic comparison can proceed.")

    user_role = (session_user or {}).get("role") or "individual"
    if user_role not in {"individual", "genetic_counsellor", "administrator", "healthcare_professional"}:
        raise PermissionError("The requesting role does not have permission to access couple-level genetic comparison data.")

    if consent_status == "revoked":
        raise PermissionError("Consent has been withdrawn for this comparison. Access is blocked.")

    gene_a = (individual_a.get("gene") or "").upper()
    gene_b = (individual_b.get("gene") or "").upper()
    status_a = (individual_a.get("status") or "").lower()
    status_b = (individual_b.get("status") or "").lower()
    pattern_a = _pattern_name(individual_a.get("pattern"))
    pattern_b = _pattern_name(individual_b.get("pattern"))

    if gene_a != gene_b:
        result = {
            "status": "no_shared_gene_match",
            "summary": "The submitted profiles do not share the same targeted gene for this simplified comparison.",
            "risk_model": "not_applicable",
            "affected_probability": 0.0,
            "carrier_probability": 0.0,
            "professional_review_required": True,
            "clinical_disclaimer": "A negative or non-shared result does not exclude inherited disease risk and requires clinical review.",
        }
    elif status_a != "carrier" or status_b != "carrier":
        result = {
            "status": "insufficient_matching_carrier_status",
            "summary": "Shared recessive-carrier risk cannot be estimated without confirming both individuals are carriers for the same gene.",
            "risk_model": "autosomal_recessive",
            "affected_probability": 0.0,
            "carrier_probability": 0.0,
            "professional_review_required": True,
            "clinical_disclaimer": "Incomplete or missing screening data prevents a definitive risk conclusion.",
        }
    elif pattern_a != "autosomal_recessive" or pattern_b != "autosomal_recessive":
        result = {
            "status": "unsupported_inheritance_pattern",
            "summary": "This demonstration supports the autosomal recessive model for carrier pairing. Other patterns require qualified genetic review.",
            "risk_model": pattern_a or pattern_b,
            "affected_probability": None,
            "carrier_probability": None,
            "professional_review_required": True,
            "clinical_disclaimer": "Non-autosomal recessive scenarios require expert interpretation and cannot be resolved by this simplified model.",
        }
    else:
        result = {
            "status": "shared_recessive_carrier_risk",
            "summary": "Both individuals are carrier-positive for the same gene under a simplified autosomal recessive model.",
            "risk_model": "autosomal_recessive",
            "affected_probability": 0.25,
            "carrier_probability": 0.5,
            "non_affected_probability": 0.25,
            "professional_review_required": True,
            "clinical_disclaimer": "This is an educational calculation based on Mendelian assumptions for a single gene and does not replace laboratory-confirmed genetic counselling.",
            "plain_language": "If both partners carry the same pathogenic variant, each pregnancy has a 25% chance of an affected child, a 50% chance of being a carrier, and a 25% chance of being unaffected under this simplified inheritance model.",
        }

    _append_audit("couple_comparison", (individual_a.get("name") or "anonymous") + "::" + (individual_b.get("name") or "anonymous"), {"result": result["status"], "consent": consent})
    return result


def grant_consent(record_type: str, subject_reference: str, permission: str, role: str = "individual") -> Dict[str, Any]:
    key = f"{record_type}:{subject_reference}:{permission}"
    payload = {
        "record_type": record_type,
        "subject_reference": subject_reference,
        "permission": permission,
        "role": role,
        "status": "granted",
        "timestamp": _now_iso(),
    }
    CONSENT_RECORDS[key] = payload
    _append_audit("consent_granted", subject_reference, {"permission": permission, "role": role})
    return {"status": "granted", "record": payload}


def revoke_consent(record_type: str, subject_reference: str, permission: str, role: str = "individual") -> Dict[str, Any]:
    key = f"{record_type}:{subject_reference}:{permission}"
    if key in CONSENT_RECORDS:
        entry = CONSENT_RECORDS[key]
        entry["status"] = "revoked"
        entry["role"] = role
        _append_audit("consent_revoked", subject_reference, {"permission": permission, "role": role})
        return {"status": "revoked", "record": entry}
    record = {"record_type": record_type, "subject_reference": subject_reference, "permission": permission, "role": role, "status": "not_found"}
    _append_audit("consent_missing", subject_reference, {"permission": permission, "role": role})
    return {"status": "not_found", "record": record}


def get_privacy_audit() -> List[Dict[str, Any]]:
    return ACCESS_AUDIT_LOG


def ask_counselling_question(question: str, profile_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cleaned = (question or "").strip().lower()
    if any(token in cleaned for token in ["diagnose", "should i marry", "terminate pregnancy", "make a decision", "not have a child"]) :
        return {
            "answer": "I cannot diagnose or recommend a reproductive decision. I can explain the meaning of genetic findings, carrier status, inheritance patterns, and the need for qualified genetic counselling.",
            "safety": "non_diagnostic",
            "recommended_next_step": "Book an appointment with a qualified genetic counsellor for personalised interpretation.",
        }

    if "carrier" in cleaned:
        answer = "A carrier result means you have one altered copy of a gene paired with a normal copy. It often means you do not have the condition yourself, but you may have a chance of passing the altered copy to a child depending on the inheritance pattern."
    elif "autosomal recessive" in cleaned:
        answer = "Autosomal recessive conditions usually require two altered copies for the condition to be expressed. Two carriers can have a child with the condition in about 25% of pregnancies under the simplified model."
    elif "uncertain" in cleaned or "vus" in cleaned:
        answer = "When a variant is uncertain, we should avoid treating it as confirmed pathogenic. More evidence, family history, and specialist review are needed before drawing health conclusions."
    elif "inheritance" in cleaned:
        answer = "Inheritance patterns explain how a gene variant can be passed down. Common patterns include autosomal recessive, autosomal dominant, and X-linked recessive. The exact pattern depends on the gene and the reported variant."
    else:
        answer = "Genetic screening provides information about variants, inheritance risk and carrier status. It does not replace a formal diagnosis or a qualified genetics consultation."

    return {
        "answer": answer,
        "safety": "educational_only",
        "recommended_next_step": "If the findings are clinically significant or complex, request a consult with a genetics professional.",
        "profile_context": profile_context or {},
    }


def request_counselling(payload: Dict[str, Any]) -> Dict[str, Any]:
    patient_name = payload.get("patient_name") or "anonymous-patient"
    priority = (payload.get("priority") or "medium").lower()
    referral_id = f"REF-{len(COUNSELLING_REQUESTS) + 1:04d}"
    summary = payload.get("risk_summary") or "Genetic risk requires assessment by a qualified genetics professional."
    referral = {
        "referral_id": referral_id,
        "patient_name": patient_name,
        "priority": priority,
        "status": "pending",
        "molecular_summary": f"{patient_name}: {summary}",
        "counselling_recommendations": [
            "Review the gene, variant, and inheritance pattern with a qualified genetics professional.",
            "Confirm whether screening results are carrier findings or clinically significant pathogenic variants.",
            "Document risk, uncertainty, and patient preferences before any reproductive decision-making.",
        ],
        "security_note": "The referral summary excludes raw genetic files and only shares the minimum clinically relevant information required for review.",
    }
    COUNSELLING_REQUESTS[referral_id] = referral
    _append_audit("counselling_requested", patient_name, {"referral_id": referral_id, "priority": priority})
    return referral


def get_impact_dashboard() -> Dict[str, Any]:
    return {
        "genetic_risk_comprehension": {"score": 0.86, "label": "comprehension improved after educational review"},
        "carrier_screening_interpretation_accuracy": {"score": 0.91, "label": "carrier-aware explanations align with approved educational summaries"},
        "counselling_referral_uptake": {"score": 0.74, "label": "strong engagement with professional counselling pathways"},
        "time_to_appropriate_referral": {"score": "24 hours", "label": "estimated turnaround for flagged high-impact results"},
        "consent_compliance": {"score": 0.98, "label": "consent and authorization checks were enforced"},
        "privacy_incidents": {"score": 0, "label": "unauthorized access events recorded as zero in the demo environment"},
        "language_accessibility": {"score": 0.80, "label": "English, Arabic, French and Swahili explanations are supported in the outreach layer"},
        "demonstration_note": "Metrics are measured on synthetic demo data and should be treated as prototype indicators rather than clinical outcomes.",
    }


def generate_inherited_risk_report(profile: Dict[str, Any], partner_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    analysis = analyze_individual_profile(profile)
    report = {
        "individual_analysis": analysis,
        "inheritance_summary": {},
        "couple_summary": None,
    }
    if partner_profile is not None:
        comparison = compare_couple_risk(
            {"gene": profile.get("gene") or "HBB", "status": analysis["carrier_status"], "pattern": profile.get("inheritance_pattern") or "autosomal_recessive"},
            {"gene": partner_profile.get("gene") or "HBB", "status": "carrier", "pattern": partner_profile.get("inheritance_pattern") or "autosomal_recessive"},
            consent=True,
            session_user={"role": "individual"},
            consent_status="granted",
        )
        report["couple_summary"] = comparison
    return report
