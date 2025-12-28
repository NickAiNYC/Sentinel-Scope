import concurrent.futures
import base64
import os
from typing import List, Union, Optional
from openai import OpenAI
from pydantic import ValidationError  # Add this if not already imported elsewhere
from core.gap_detector import ComplianceGapEngine
from core.models import CaptureClassification, GapAnalysisResponse


class SentinelBatchProcessor:
    """
    Forensic Vision Engine: Uses DeepSeek-V3.2 (Dec 2025) to analyze site imagery
    against NYC Building Code 2022 standards using agentic reasoning.
    Updated Dec 27, 2025: Removed 'instructor' dependency → uses native OpenAI structured outputs.
    """
   
    def __init__(self, engine: ComplianceGapEngine, api_key: str, max_workers: int = 5):
        self.engine = engine
        self.max_workers = max_workers
       
        # Standard OpenAI-compatible client for DeepSeek
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
       
        self.system_prompt = """
        ACT AS: A Senior NYC DOB Forensic Inspector.
        TASK: Conduct a visual milestone audit using NYC BC 2022 guidelines.
       
        REASONING PROTOCOL:
        1. Identify the primary structural or MEP system.
        2. Verify floor height using visual context (e.g., street level, mechanical headers).
        3. Match against NYC Class A/B/C hazard definitions.
       
        Valid Floor Codes: ^[0-9RCBLMPHSC]+$ (Use PH for Penthouse, SC for Sub-Cellar).
        Output strictly in the requested JSON format — no extra text.
        """

    def _prepare_base64(self, file_source: Union[str, any]) -> str:
        """Handles encoding for local paths and Streamlit UploadedFile objects."""
        try:
            if hasattr(file_source, 'read'):
                file_source.seek(0)
                return base64.b64encode(file_source.read()).decode('utf-8')
            with open(file_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise IOError(f"Image Encoding Error: {str(e)}")

    def _process_single_image(self, file_source: Union[str, any]) -> CaptureClassification:
        """Sends image to DeepSeek-V3.2 with structured JSON output."""
        try:
            base64_image = self._prepare_base64(file_source)
           
            # Use native structured outputs (DeepSeek supports this via OpenAI compat)
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # DeepSeek-V3.2 Vision-capable endpoint
                response_format={ "type": "json_object" },  # Enforces JSON output
                temperature=0.1,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Forensic audit: Classify this NYC construction capture. Respond ONLY with valid JSON matching the schema."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]}
                ]
            )
           
            # Parse JSON and validate with Pydantic model
            json_content = response.choices[0].message.content
            data = json.loads(json_content)  # Add import json if needed
           
            return CaptureClassification.model_validate(data)  # Pydantic v2+ safe validation
       
        except ValidationError as ve:
            # Handle schema mismatch gracefully
            return CaptureClassification(
                milestone="Validation Error",
                mep_system=None,
                floor="0",
                zone="Invalid_Output",
                confidence=0.0,
                compliance_relevance=0,
                evidence_notes=f"Pydantic validation failed: {str(ve)}"
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

    def run_audit(self, file_sources: List[Union[str, any]]) -> List[CaptureClassification]:
        """Processes site captures in parallel using a ThreadPool."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(self._process_single_image, file_sources))

    def finalize_gap_analysis(self, findings: List[CaptureClassification]) -> GapAnalysisResponse:
        """Finalizes the remediation roadmap — pass api_key only if gap_detector needs it."""
        # If your gap_detector no longer needs API (current versions don't), just:
        return self.engine.detect_gaps(findings)
        # Or if it still needs for remediation: return self.engine.detect_gaps(findings, api_key=self.client.api_key)
