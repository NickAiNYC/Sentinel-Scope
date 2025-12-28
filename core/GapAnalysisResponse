import concurrent.futures
from typing import List
from core.gap_detector import ComplianceGapEngine
from core.models import CaptureClassification, GapAnalysisResponse

class SentinelBatchProcessor:
    def __init__(self, engine: ComplianceGapEngine, max_workers: int = 5):
        self.engine = engine
        self.max_workers = max_workers

    def _process_single_image(self, image_path: str) -> CaptureClassification:
        """
        Placeholder for your Vision AI call (e.g., DeepSeek-V3.2 or Pytorch).
        This would return a validated CaptureClassification object.
        """
        # Logic to call your model (e.g., self.model.predict(image_path))
        # For now, we return a mock validated object:
        return CaptureClassification(
            milestone="Fireproofing",
            floor="12",
            zone="North",
            confidence=0.92,
            compliance_relevance=5,
            evidence_notes="Spray-on fireproofing applied to structural steel."
        )

    def run_audit(self, image_paths: List[str], project_type: str = "structural") -> GapAnalysisResponse:
        """Processes multiple images in parallel and runs a full gap analysis."""
        found_milestones = []
        
        # 1. Parallel Image Classification
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # map() keeps the results in the order of the original paths
            results = list(executor.map(self._process_single_image, image_paths))
            
        # 2. Extract unique milestones found across all images
        found_milestones = list(set([res.milestone for res in results]))
        
        # 3. Final Gap Analysis
        return self.engine.detect_gaps(found_milestones)
