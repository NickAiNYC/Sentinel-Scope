"""Service layer for coordinating data ingestion with forensics archival."""

from __future__ import annotations

from typing import Any

from data_forensics.forensics_engine import ForensicsEngine
from violations.dob.dob_engine import DOBEngine


class IngestionService:
    """Coordinates data ingestion with forensics archival."""

    def __init__(self, forensics_engine: ForensicsEngine | None = None) -> None:
        self._forensics = forensics_engine or ForensicsEngine()

    def ingest_dob_violations(
        self,
        project_id: str,
        bbl: str,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        """Fetch live DOB violations and archive the raw response.

        Returns a structured result with violation count and snapshot_id.
        """
        raw_violations = DOBEngine.fetch_live_dob_alerts({"bbl": bbl})

        snapshot = self._forensics.archive_ingestion(
            project_id=project_id,
            source="dob_ecb_violations",
            raw_payload={"bbl": bbl, "violations": raw_violations},
            tenant_id=tenant_id,
        )

        return {
            "project_id": project_id,
            "bbl": bbl,
            "violation_count": len(raw_violations),
            "snapshot_id": snapshot.snapshot_id,
            "tenant_id": tenant_id,
        }

    def ingest_project_data(
        self,
        project_id: str,
        data: dict,
        source: str,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        """Generic ingestion that archives any data payload.

        Returns an ingestion receipt with snapshot_id and data_hash.
        """
        snapshot = self._forensics.archive_ingestion(
            project_id=project_id,
            source=source,
            raw_payload=data,
            tenant_id=tenant_id,
        )

        return {
            "project_id": project_id,
            "source": source,
            "snapshot_id": snapshot.snapshot_id,
            "data_hash": snapshot.data_hash,
            "tenant_id": tenant_id,
        }
