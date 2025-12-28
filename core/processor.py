import concurrent.futures
import base64
import json
import os
from typing import List, Union
from openai import OpenAI
from core.gap_detector import ComplianceGapEngine
from core.models import CaptureClassification, GapAnalysisResponse

class SentinelBatchProcessor:
    """
    Forensic Vision Engine: Uses DeepSeek-V3 to analyze construction site imagery 
    against NYC Building Code 2022 standards in parallel threads.
    """
    
    def __init__(self, engine: ComplianceGapEngine, api_key: str, max_workers: int = 5):
        self.engine = engine
        self.max_workers = max_workers
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com"
        )
        
        # Updated System Prompt to match the new CaptureClassification model
        self.system_prompt = """
        ACT AS: A Senior NYC Department of Buildings (DOB) Forensic Inspector.
        TASK: Analyze site imagery for NYC BC 2022 milestone verification.
        
        OUTPUT FORMAT: You must return ONLY a JSON object with these keys:
        1. "milestone": Choose one: [Foundation, Structural Steel, Fireproofing, MEP Rough-in, Enclosure].
        2. "mep_system": If MEP, specify (HVAC, Sprinkler, Plumbing, Electrical). Otherwise, null.
        3. "floor": Numeric string or code (e.g., "15", "R", "B", "L").
        4. "zone": Building sector (North, South, East, West, Core, or Hoist).
        5. "confidence": Float between 0.0 and 1.0.
        6. "compliance_relevance": Integer 1-5 (5 = Critical Life Safety / Fireproofing).
        7. "evidence_notes": A technical description of why this meets milestone criteria.
        
        FORENSIC RULES:
        - Orange/Red spray on steel = Fireproofing (Relevance: 5).
        - Exposed rebar + formwork = Foundation (Relevance: 4).
        - Vertical I-beams without decks = Structural Steel (Relevance: 4).
        - Visible ductwork/piping = MEP Rough-in (Relevance: 3).
        - Glass/Curtain wall/Masonry = Enclosure (Relevance: 3).
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
            raise IOError(f"Failed to encode image: {str(e)}")

    def _process_single_image(self, file_source: Union[str, any]) -> CaptureClassification:
        """Sends image to DeepSeek and validates against CaptureClassification model."""
        try:
            base64_image = self._prepare_base64(file_source)
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Forensic audit: Classify this construction image for NYC compliance."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1 
            )

            ai_data = json.loads(response.choices[0].message.content)
            
            # Map null mep_system if AI sends it as a string "null"
            if ai_data.get("mep_system") == "null":
                ai_data["mep_system"] = None

            return CaptureClassification(**ai_data)
        
        except Exception as e:
            # Fallback to prevent crash, adhering to the regex and constraints of CaptureClassification
            return CaptureClassification(
                milestone="Unknown",
                mep_system=None,
                floor="0",
                zone="Unknown",
                confidence=0.0,
                compliance_relevance=1,
                evidence_notes=f"Audit Interrupted: {str(e)}"
            )

    def run_audit(self, file_sources: List[Union[str, any]]) -> List[CaptureClassification]:
        """Processes multiple site captures in parallel."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self._process_single_image, file_sources))
        return results

    def finalize_gap_analysis(self, findings: List[CaptureClassification]) -> GapAnalysisResponse:
        """Passes findings to the engine for score and gap mapping."""
        return self.engine.detect_gaps(findings)
