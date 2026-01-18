import base64
import concurrent.futures
from typing import Any

import instructor  # Optimized for DeepSeek-V3.2 structured outputs

from core.gap_detector import ComplianceGapEngine
from core.models import CaptureClassification, GapAnalysisResponse


class SentinelBatchProcessor:
    """
    Forensic Vision Engine: Uses DeepSeek-V3.2 (Dec 2025) to analyze site imagery 
    against NYC Building Code 2022 standards using agentic reasoning.
    """
    
    def __init__(self, engine: ComplianceGapEngine, api_key: str, max_workers: int = 5):
        self.engine = engine
        self.max_workers = max_workers
        
        # Initialize the 'instructor' patched client for strict Pydantic enforcement
        self.client = instructor.from_provider(
            provider="deepseek-chat",
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        
        self.system_prompt = """
        ACT AS: A Senior NYC DOB Forensic Inspector.
        TASK: Conduct a visual milestone audit using NYC BC 2022 guidelines.
        
        REASONING PROTOCOL:
        1. Identify the primary structural or MEP system.
        2. Verify floor height using visual context (e.g., street level, mechanical headers).
        3. Match against NYC Class A/B/C hazard definitions.
        
        Valid Floor Codes: ^[0-9RCBLMPHSC]+$ (Use PH for Penthouse, SC for Sub-Cellar).
        """

    def _prepare_base64(self, file_source: str | Any) -> str:
        """Handles encoding for local paths and Streamlit UploadedFile objects."""
        try:
            if hasattr(file_source, 'read'):
                file_source.seek(0)
                return base64.b64encode(file_source.read()).decode('utf-8')
            with open(file_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise OSError(f"Image Encoding Error: {str(e)}")

    def _process_single_image(self, file_source: str | Any) -> CaptureClassification:
        """Sends image to DeepSeek-V3.2 with 'Thinking Mode' for forensic validation."""
        try:
            base64_image = self._prepare_base64(file_source)
            
            # Use instructor's .create() to directly return a validated Pydantic model
            return self.client.chat.completions.create(
                model="deepseek-chat", # Points to V3.2 as of Dec 2025
                response_model=CaptureClassification,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Forensic audit: Classify this NYC construction capture."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ],
                    }
                ],
                temperature=0.1,
                max_retries=2 # Auto-retry if AI halluncinates a non-regex floor code
            )
        
        except Exception as e:
            return CaptureClassification(
                milestone="Processing Error",
                mep_system=None,
                floor="0",
                zone="Audit_Failed",
                confidence=0.0,
                compliance_relevance=1,
                evidence_notes=f"System Error: {str(e)}"
            )

    def run_audit(self, file_sources: list[str | Any]) -> list[CaptureClassification]:
        """Processes site captures in parallel using a ThreadPool."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(self._process_single_image, file_sources))

    def finalize_gap_analysis(self, findings: list[CaptureClassification]) -> GapAnalysisResponse:
        """Finalizes the remediation roadmap."""
        return self.engine.detect_gaps(findings, self.client)
