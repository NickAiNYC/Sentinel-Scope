"""Service layer wrapping DOB data fetching with forensics archival."""

from __future__ import annotations

from typing import Any

from data_forensics.forensics_engine import ForensicsEngine
from violations.dob.dob_engine import DOBEngine


class DOBSyncService:
    """Wraps DOB data fetching with a forensics layer."""

    def __init__(self, forensics_engine: ForensicsEngine | None = None) -> None:
        self._forensics = forensics_engine or ForensicsEngine()

    def sync_violations(
        self,
        bbl: str,
        project_id: str = "",
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        """Fetch violations from DOBEngine, archive raw response, and return a structured result."""
        raw_violations = DOBEngine.fetch_live_dob_alerts({"bbl": bbl})

        snapshot = self._forensics.archive_ingestion(
            project_id=project_id,
            source="dob_sync",
            raw_payload={"bbl": bbl, "violations": raw_violations},
            tenant_id=tenant_id,
        )

        return {
            "project_id": project_id,
            "bbl": bbl,
            "violation_count": len(raw_violations),
            "violations": raw_violations,
            "snapshot_id": snapshot.snapshot_id,
            "tenant_id": tenant_id,
        }

    def get_sync_history(self, project_id: str) -> list[dict[str, Any]]:
        """Return all archived syncs for a project from the forensics engine."""
        snapshots = self._forensics.get_project_snapshots(project_id)
        return [
            {
                "snapshot_id": s.snapshot_id,
                "timestamp": s.timestamp.isoformat(),
                "data_hash": s.data_hash,
                "violation_count": len(s.raw_payload.get("violations", [])),
            }
            for s in snapshots
            if s.raw_payload.get("_source") == "dob_sync"
        ]
