"""
Local hash-chain audit ledger — real SHA-256, chained the same way the
frontend does it, so both sides of the architecture use identical logic.
This is a LOCAL simulation of the tamper-evidence idea behind a distributed
ledger. It is not, by itself, a connection to Hedera — see hedera_service.py
for that (optional, credential-gated) piece.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional


class Ledger:
    def __init__(self):
        self.chain: List[dict] = []

    def append(self, action: str, data: dict) -> dict:
        prev_hash = self.chain[-1]["hash"] if self.chain else "0" * 64
        timestamp = datetime.now(timezone.utc).isoformat()
        index = len(self.chain)
        payload = json.dumps({
            "index": index, "timestamp": timestamp, "action": action,
            "data": data, "prevHash": prev_hash,
        }, sort_keys=True)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        block = {
            "index": index, "timestamp": timestamp, "action": action,
            "data": data, "prevHash": prev_hash, "hash": digest,
        }
        self.chain.append(block)
        return block

    def verify(self) -> dict:
        for i, block in enumerate(self.chain):
            payload = json.dumps({
                "index": block["index"], "timestamp": block["timestamp"],
                "action": block["action"], "data": block["data"],
                "prevHash": block["prevHash"],
            }, sort_keys=True)
            recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if recomputed != block["hash"]:
                return {"ok": False, "reason": f"hash mismatch at block {i}"}
            expected_prev = self.chain[i - 1]["hash"] if i > 0 else "0" * 64
            if block["prevHash"] != expected_prev:
                return {"ok": False, "reason": f"chain broken at block {i}"}
        return {"ok": True, "blocks": len(self.chain)}


# module-level singleton so the FastAPI app shares one ledger across requests
ledger = Ledger()
