import base64
import json
from typing import List
from openai import OpenAI
from core.models import CaptureClassification
from core.constants import MILESTONES

class SiteClassifier:
    """Uses DeepSeek-VL to classify construction captures against NYC milestones."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = "deepseek-chat" # Note: Use deepseek-vl for actual vision-enabled endpoints

    def _encode_image(self, image_bytes):
        """Helper to convert raw bytes to base64 for API transmission."""
        return base64.b64encode(image_bytes).decode('utf-8')

    def classify_capture(self, file_content: bytes, project_type: str) -> CaptureClassification:
        """
        Analyzes a single site capture and returns a structured classification.
        """
        base64_image = self._encode_image(file_content)
        
        # We use a structured system prompt to force the AI to behave like a 
        # NYC Site Safety Manager / Forensic Architect.
        system_prompt = f"""
        You are a NYC Construction Audit Specialist. 
        Analyze the provided site capture for a {project_type} project.
        
        Classify the capture into ONE of these milestones: {', '.join(MILESTONES[project_type])}.
        
        Return ONLY a JSON object with these keys:
        - milestone: (The string name of the detected milestone)
        - confidence: (Float 0.0-1.0)
        - visual_evidence: (List of 3 specific architectural markers found)
        - nyc_code_ref: (The relevant NYC Building Code section)
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Identify the milestone in this NYC construction site capture."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1 # Low temperature for high precision/repeatability
            )
            
            # Parse the structured JSON output
            data = json.loads(response.choices[0].message.content)
            return CaptureClassification(**data)
            
        except Exception as e:
            # Fallback for API errors: Return 'Unclassified' to prevent app crash
            return CaptureClassification(
                milestone="Unclassified",
                confidence=0.0,
                visual_evidence=[f"Error: {str(e)}"],
                nyc_code_ref="N/A"
            )

    def batch_classify(self, uploads: List, project_type: str) -> List[CaptureClassification]:
        """Processes multiple images in sequence (can be optimized with async)."""
        results = []
        for upload in uploads:
            file_bytes = upload.read()
            classification = self.classify_capture(file_bytes, project_type)
            results.append(classification)
        return results
