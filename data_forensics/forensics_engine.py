from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.compliance_models import ComplianceSnapshot, RiskAssessment


def _compute_hash(payload: dict) -> str:
    """Compute SHA-256 hex digest of canonical JSON (sorted keys)."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ForensicsEngine:
    """In-memory forensic data store for compliance snapshots."""

    SCHEMA_VERSION = "1.0"

    def __init__(self) -> None:
        self._snapshots: dict[str, ComplianceSnapshot] = {}
        self._project_index: dict[str, list[str]] = {}

    def archive_ingestion(
        self,
        project_id: str,
        source: str,
        raw_payload: dict,
        tenant_id: str = "default",
    ) -> ComplianceSnapshot:
        """Store a raw JSON payload and return a ComplianceSnapshot."""
        enriched_payload = {
            **raw_payload,
            "_source": source,
            "_tenant_id": tenant_id,
        }
        data_hash = _compute_hash(enriched_payload)
        snapshot = ComplianceSnapshot(
            snapshot_id=uuid4().hex,
            project_id=project_id,
            timestamp=datetime.now(timezone.utc),
            data_hash=data_hash,
            raw_payload=enriched_payload,
            version=self.SCHEMA_VERSION,
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        self._project_index.setdefault(project_id, []).append(snapshot.snapshot_id)
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> ComplianceSnapshot | None:
        """Retrieve a specific snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    def get_project_snapshots(self, project_id: str) -> list[ComplianceSnapshot]:
        """Return all snapshots for a project, sorted newest first."""
        ids = self._project_index.get(project_id, [])
        snapshots = [self._snapshots[sid] for sid in ids if sid in self._snapshots]
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)
        return snapshots

    def reconstruct_state_at(
        self, project_id: str, at_time: datetime
    ) -> ComplianceSnapshot | None:
        """Return the latest snapshot with timestamp <= at_time."""
        candidates = [
            s
            for s in self.get_project_snapshots(project_id)
            if s.timestamp <= at_time
        ]
        return candidates[0] if candidates else None

    def replay_risk_score(
        self, snapshot_id: str, risk_engine: Any
    ) -> RiskAssessment | None:
        """Replay risk scoring on historical data using the current engine.

        The *risk_engine* must expose a ``score(features: dict) -> RiskAssessment``
        method.
        """
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            return None
        features = snapshot.raw_payload
        return risk_engine.score(features)

    def verify_integrity(self, snapshot_id: str) -> bool:
        """Recompute SHA-256 hash and verify it matches the stored hash."""
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            return False
        recomputed = _compute_hash(snapshot.raw_payload)
        return recomputed == snapshot.data_hash
