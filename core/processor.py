import concurrent.futures
import base64
from typing import List
from openai import OpenAI  # DeepSeek uses OpenAI-compatible SDK
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

    def _encode_image(self, image_path: str) -> str:
        """Helper to convert local images to Base64 for the Vision API."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _process_single_image(self, image_path: str) -> CaptureClassification:
        """
        Calls DeepSeek-V3.2-Vision to analyze the construction capture.
        """
        base64_image = self._encode_image(image_path)
        
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
            response_format={"type": "json_object"} # Forces valid JSON output
        )

        # Parse the AI response directly into our Pydantic Model
        import json
        ai_data = json.loads(response.choices[0].message.content)
        return CaptureClassification(**ai_data)

    def run_audit(self, image_paths: List[str]) -> GapAnalysisResponse:
        """Processes multiple images in parallel and runs a full gap analysis."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self._process_single_image, image_paths))
            
        found_milestones = list(set([res.milestone for res in results]))
        return self.engine.detect_gaps(found_milestones)
