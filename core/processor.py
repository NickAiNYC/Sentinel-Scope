import concurrent.futures
import base64
import os
import json
from typing import List, Union, Optional, Any
from openai import OpenAI
from pydantic import ValidationError

# Internal SentinelScope Imports
from core.models import CaptureClassification, GapAnalysisResponse
from core.gap_detector import ComplianceGapEngine

class SentinelBatchProcessor:
    """
    Forensic Vision Engine: Uses DeepSeek-V3.2 to analyze site imagery.
    Updated Dec 2025: Uses native OpenAI structured outputs.
    """
    
    def __init__(self, engine: ComplianceGapEngine, api_key: str, max_workers: int = 5):
        self.engine = engine
        self.max_workers = max_workers
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.system_prompt = """
        ACT AS: A Senior NYC DOB Forensic Inspector.
        TASK: Conduct a visual milestone audit using NYC BC 2022/2025 guidelines.
        Output strictly in valid JSON format matching the provided schema.
        """

    def _prepare_base64(self, file_source: Any) -> str:
        """Handles encoding for local paths and Streamlit UploadedFile objects."""
        try:
            if hasattr(file_source, 'read'):
                file_source.seek(0)
                data = file_source.read()
                return base64.b64encode(data).decode('utf-8')
            with open(file_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise IOError(f"Forensic Encoding Error: {str(e)}")

    def _process_single_image(self, file_source: Union[str, Any]) -> CaptureClassification:
        """Sends image to DeepSeek-V3.2 with strict schema enforcement."""
        try:
            base64_image = self._prepare_base64(file_source)
            
            response = self.client.chat.completions.create(
                model="deepseek-chat", 
                response_format={ "type": "json_object" },
                temperature=0.1,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"Audit this capture. Respond strictly using this Pydantic schema: {CaptureClassification.model_json_schema()}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]}
                ]
            )
            
            raw_json = response.choices[0].message.content
            parsed_data = json.loads(raw_json)
            
            return CaptureClassification.model_validate(parsed_data)
        
        except ValidationError as ve:
            return CaptureClassification(
                milestone="Validation Error",
                floor="ERR",
                zone="Forensic_Failure",
                confidence=0.0,
                compliance_relevance=0,
                evidence_notes=f"NYC DOB Schema Mismatch: {str(ve)[:200]}"
            )
        except Exception as e:
            return CaptureClassification(
                milestone="System Error",
                floor="ERR",
                zone="Audit_Failed",
                confidence=0.0,
                compliance_relevance=0,
                evidence_notes=f"API connection failed: {str(e)[:200]}"
            )

    def run_audit(self, file_sources: List[Any]) -> List[CaptureClassification]:
        """Processes site captures in parallel using a ThreadPool."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(self._process_single_image, file_sources))

    def finalize_gap_analysis(self, findings: List[CaptureClassification]) -> GapAnalysisResponse:
        """Finalizes the remediation roadmap."""
        return self.engine.detect_gaps(findings)
