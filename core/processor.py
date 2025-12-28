import concurrent.futures
import base64
import json
from typing import List, Union
from openai import OpenAI
from core.gap_detector import ComplianceGapEngine
from core.models import CaptureClassification, GapAnalysisResponse

class SentinelBatchProcessor:
    def __init__(self, engine: ComplianceGapEngine, api_key: str, max_workers: int = 5):
        self.engine = engine
        self.max_workers = max_workers
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # The "NYC Inspector" System Prompt
        self.system_prompt = """
        ACT AS: A NYC Department of Buildings (DOB) Senior Inspector.
        TASK: Analyze construction site imagery for BC 2022 Compliance.
        
        EXTRACT DATA IN JSON:
        1. milestone: Choose from [Foundation, Structural Steel, Fireproofing, MEP Rough-in, Enclosure].
        2. floor: Numeric string (e.g., "12").
        3. zone: North/South/East/West/Core.
        4. confidence: 0.0 to 1.0.
        5. evidence_notes: Brief technical description of installation quality.
        
        RULES: 
        - If you see orange spray on steel, milestone is "Fireproofing".
        - If you see rebar and formwork, milestone is "Foundation".
        - Be conservative with confidence if the image is blurry.
        """

    def _prepare_base64(self, file_source: Union[str, any]) -> str:
        """
        Works for both local file paths (strings) and Streamlit UploadedFile objects.
        """
        if hasattr(file_source, 'read'):
            # This is a Streamlit UploadedFile (BytesIO)
            file_source.seek(0)
            return base64.b64encode(file_source.read()).decode('utf-8')
        
        # This is a standard local file path
        with open(file_source, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _process_single_image(self, file_source: Union[str, any]) -> CaptureClassification:
        """
        Calls DeepSeek-V3.2-Vision with error resilience.
        """
        try:
            base64_image = self._prepare_base64(file_source)
            
            response = self.client.chat.completions.create(
                model="deepseek-v3.2-vision",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Inspect this site photo for NYC BC 2022 compliance."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                response_format={"type": "json_object"}
            )

            ai_data = json.loads(response.choices[0].message.content)
            return CaptureClassification(**ai_data)
        
        except Exception as e:
            # Fallback for failed images so the whole batch doesn't die
            return CaptureClassification(
                milestone="Unknown",
                floor="?",
                zone="?",
                confidence=0.0,
                evidence_notes=f"Error processing image: {str(e)}"
            )

    def run_audit(self, file_sources: List[Union[str, any]]) -> GapAnalysisResponse:
        """Processes multiple images/uploads in parallel and runs a full gap analysis."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Map now accepts both paths and Streamlit files
            results = list(executor.map(self._process_single_image, file_sources))
            
        # Filter for unique milestones, ignoring "Unknown" failures
        found_milestones = list(set([res.milestone for res in results if res.milestone != "Unknown"]))
        
        return self.engine.detect_gaps(found_milestones)
