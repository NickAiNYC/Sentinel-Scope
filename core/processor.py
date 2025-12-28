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
        # DeepSeek uses the OpenAI SDK format
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com"
        )
        
        # The "NYC Senior Inspector" System Prompt
        self.system_prompt = """
        ACT AS: A Senior NYC Department of Buildings (DOB) Forensic Inspector.
        TASK: Analyze site imagery for NYC BC 2022 milestone verification.
        
        OUTPUT FORMAT: You must return ONLY a JSON object with these keys:
        1. "milestone": Choose one: [Foundation, Structural Steel, Fireproofing, MEP Rough-in, Enclosure].
        2. "floor": Numeric string (e.g., "15").
        3. "zone": Building sector (North, South, East, West, or Core).
        4. "confidence": Float between 0.0 and 1.0.
        5. "evidence_notes": A technical description of why this meets the milestone criteria.
        
        FORENSIC RULES:
        - Orange/Red spray on steel = Fireproofing.
        - Exposed rebar + formwork = Foundation.
        - Vertical I-beams without decks = Structural Steel.
        - Visible ductwork/piping = MEP Rough-in.
        - Glass/Curtain wall/Masonry = Enclosure.
        """

    def _prepare_base64(self, file_source: Union[str, any]) -> str:
        """
        Handles image encoding for both local paths and Streamlit UploadedFile objects.
        """
        try:
            if hasattr(file_source, 'read'):
                # Streamlit UploadedFile (BytesIO)
                file_source.seek(0)
                return base64.b64encode(file_source.read()).decode('utf-8')
            
            # Standard local file path
            with open(file_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise IOError(f"Failed to encode image: {str(e)}")

    def _process_single_image(self, file_source: Union[str, any]) -> CaptureClassification:
        """
        Sends a single image to DeepSeek-V3 with specialized vision prompts.
        """
        try:
            base64_image = self._prepare_base64(file_source)
            
            # Using deepseek-chat (unified text/vision model)
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
                temperature=0.1 # Low temperature for consistent forensic accuracy
            )

            # Parse JSON content from the AI response
            raw_content = response.choices[0].message.content
            ai_data = json.loads(raw_content)
            
            return CaptureClassification(**ai_data)
        
        except Exception as e:
            # Prevent the entire batch audit from crashing if one image fails
            return CaptureClassification(
                milestone="Unknown",
                floor="?",
                zone="?",
                confidence=0.0,
                evidence_notes=f"Audit Interrupted: {str(e)}"
            )

    def run_audit(self, file_sources: List[Union[str, any]]) -> List[CaptureClassification]:
        """
        Executes parallel processing of multiple site captures.
        Returns a list of individual image classifications.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Map the processing function across all uploaded files
            results = list(executor.map(self._process_single_image, file_sources))
        
        return results

    def finalize_gap_analysis(self, findings: List[CaptureClassification]) -> GapAnalysisResponse:
        """
        Aggregates raw findings and passes them to the Compliance Engine for the final score.
        """
        # Extract unique milestones identified with at least 40% confidence
        found_milestones = list(set([
            res.milestone for res in findings 
            if res.milestone != "Unknown" and res.confidence > 0.4
        ]))
        
        return self.engine.detect_gaps(found_milestones)
