"""
AI summary of YOLOv8/ATCG object-detection results. The app prefers a real
OpenAI-compatible model when OPENAI_API_KEY is configured; otherwise it falls
back to Anthropic if that SDK is installed and configured. If no LLM is set up,
we return a deterministic template summary rather than pretending a model was
used.
"""
import os
from typing import List, Dict

try:
    import anthropic
    _ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    _ANTHROPIC_SDK_AVAILABLE = False

try:
    from openai import OpenAI
    _OPENAI_SDK_AVAILABLE = True
except ImportError:
    _OPENAI_SDK_AVAILABLE = False


def status() -> dict:
    configured = []
    if _OPENAI_SDK_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        configured.append("openai")
    if _ANTHROPIC_SDK_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
        configured.append("anthropic")
    if configured:
        return {"configured": True, "providers": configured}
    reasons = []
    if not _OPENAI_SDK_AVAILABLE:
        reasons.append("openai package not installed")
    if not os.getenv("OPENAI_API_KEY"):
        reasons.append("OPENAI_API_KEY not set")
    if not _ANTHROPIC_SDK_AVAILABLE:
        reasons.append("anthropic package not installed")
    if not os.getenv("ANTHROPIC_API_KEY"):
        reasons.append("ANTHROPIC_API_KEY not set")
    return {"configured": False, "reason": "; ".join(reasons) if reasons else "no LLM configured"}


def _template_summary(detections: List[Dict]) -> str:
    if not detections:
        return "No objects were detected above the confidence threshold, so there's nothing to summarize."
    counts: Dict[str, int] = {}
    for d in detections:
        counts[d["label"]] = counts.get(d["label"], 0) + 1
    parts = [f"{n} {label}s" if n > 1 else f"a {label}" for label, n in counts.items()]
    top = max(detections, key=lambda d: d["confidence"])
    return (
        f"This image contains {', '.join(parts)}. The most confident detection is "
        f"\"{top['label']}\" at {top['confidence']*100:.0f}%. "
        f"(Template summary — set ANTHROPIC_API_KEY for a real LLM-written summary.)"
    )


def _call_openai_summary(detections: List[Dict]) -> str:
    if not (_OPENAI_SDK_AVAILABLE and os.getenv("OPENAI_API_KEY")):
        return ""
    detection_list = "\n".join(
        f"- {d['label']} (confidence {d['confidence']*100:.0f}%)" for d in detections
    )
    prompt = (
        "This is a DNA nucleotide detection task. Explain the likely sequence pattern in plain language for a genomic analysis workflow, "
        "with a focus on ATCG bases and whether the pattern looks consistent with a CFTR-related sequence review.\n\n"
        f"Detections:\n{detection_list}\n\n"
        "Write a short 2-sentence explanation that is evidence-based and does not claim a clinical diagnosis."
    )
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        chat_client = client.chat
        if callable(chat_client):
            chat_client = chat_client()
        if not hasattr(chat_client, "completions"):
            return ""

        response = chat_client.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=180,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def _call_anthropic_summary(detections: List[Dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not (_ANTHROPIC_SDK_AVAILABLE and api_key):
        return ""

    if not detections:
        return ""

    detection_list = "\n".join(
        f"- {d['label']} (confidence {d['confidence']*100:.0f}%)" for d in detections
    )
    prompt = (
        "A DNA image analysis workflow found the following A/T/C/G detections:\n\n"
        f"{detection_list}\n\n"
        "Summarize the likely nucleotide pattern in 1-2 sentences, focusing on whether it looks like a plausible ATCG sequence and a CFTR-related review context."
    )
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        return text
    except Exception:
        return ""


def summarize(detections: List[Dict]) -> dict:
    """Returns {"summary": str, "source": "llm" | "template"}."""
    if not detections:
        return {"summary": _template_summary(detections), "source": "template"}

    llm_text = _call_openai_summary(detections)
    if llm_text:
        return {"summary": llm_text, "source": "llm"}

    llm_text = _call_anthropic_summary(detections)
    if llm_text:
        return {"summary": llm_text, "source": "llm"}

    return {"summary": _template_summary(detections), "source": "template"}
