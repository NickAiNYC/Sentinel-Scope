"""VisionAgent: Processes site-cam frames to detect Workers and Equipment."""
import base64
import uuid
from datetime import datetime
from typing import Any, List, Optional

import instructor

from packages.sentinel.models import DetectedEntity


class VisionAgent:
    """
    VisionAgent processes site-cam frames using AI vision models to detect 
    Workers and Equipment on construction sites.
    """

    def __init__(self, api_key: str, model: str = "deepseek/deepseek-chat"):
        """
        Initialize the VisionAgent with AI model configuration.
        
        Args:
            api_key: API key for the vision model provider
            model: Model name in format "provider/model-name" (default: deepseek/deepseek-chat)
        """
        self.api_key = api_key
        self.model = model
        
        # Initialize instructor client for structured outputs
        self.client = instructor.from_provider(
            model=model,
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        
        self.system_prompt = """
        ACT AS: Construction Site Safety & Compliance Inspector
        TASK: Analyze site-cam frames to detect Workers and Equipment
        
        DETECTION PROTOCOL:
        1. Identify all visible workers/personnel on site
        2. Identify all equipment (machinery, vehicles, tools)
        3. Extract any visible identification (badges, equipment numbers, vehicle IDs)
        4. Note the location/zone where detected
        
        For each detection, provide:
        - entity_type: "Worker" or "Equipment"
        - confidence: Detection confidence (0-1)
        - name: Any visible identifier (badge number, equipment ID, or "Unknown")
        - location: Zone/area description
        """

    def _prepare_base64(self, frame_source: str | Any) -> str:
        """
        Encode frame to base64 for AI processing.
        
        Args:
            frame_source: File path or file-like object
            
        Returns:
            Base64 encoded string
        """
        try:
            if hasattr(frame_source, 'read'):
                frame_source.seek(0)
                return base64.b64encode(frame_source.read()).decode('utf-8')
            with open(frame_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise OSError(f"Frame encoding error: {str(e)}")

    def process_frame(self, frame_source: str | Any, location: str = "Unknown") -> list[DetectedEntity]:
        """
        Process a single site-cam frame to detect entities.
        
        Args:
            frame_source: Path to frame image or file-like object
            location: Site location identifier
            
        Returns:
            List of detected entities (Workers/Equipment)
        """
        try:
            base64_frame = self._prepare_base64(frame_source)
            frame_timestamp = datetime.now()
            
            # Define a response model for detection results
            class DetectionResults(instructor.Partial):
                entities: list[dict]
            
            # Call AI vision model
            response = self.client.chat.completions.create(
                model=self.model,
                response_model=DetectionResults,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Detect all Workers and Equipment in this construction site frame."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_frame}"}
                            }
                        ],
                    }
                ],
                temperature=0.1,
                max_retries=2
            )
            
            # Convert response to DetectedEntity objects
            detected_entities = []
            for entity_data in response.entities:
                entity = DetectedEntity(
                    entity_id=str(uuid.uuid4()),
                    entity_type=entity_data.get('entity_type', 'Unknown'),
                    name=entity_data.get('name', 'Unknown'),
                    confidence=entity_data.get('confidence', 0.0),
                    location=location,
                    frame_timestamp=frame_timestamp
                )
                detected_entities.append(entity)
            
            return detected_entities
            
        except Exception as e:
            # Return empty list on error, log could be added here
            return []

    def process_frames_batch(self, frame_sources: list[str | Any], location: str = "Unknown") -> list[DetectedEntity]:
        """
        Process multiple frames in batch.
        
        Args:
            frame_sources: List of frame paths or file-like objects
            location: Site location identifier
            
        Returns:
            Combined list of detected entities from all frames
        """
        all_entities = []
        for frame_source in frame_sources:
            entities = self.process_frame(frame_source, location)
            all_entities.extend(entities)
        return all_entities
