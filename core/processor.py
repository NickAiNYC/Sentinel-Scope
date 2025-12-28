import json # Ensure this is at the top of your file

def _process_single_image(self, file_source: Union[str, any]) -> CaptureClassification:
    """Sends image to DeepSeek-V3.2 with strict schema enforcement."""
    try:
        base64_image = self._prepare_base64(file_source)
        
        # PRO TIP: DeepSeek-V3.2 supports 'json_object' but for 
        # complex forensic audits, providing the schema in the prompt helps.
        response = self.client.chat.completions.create(
            model="deepseek-chat", 
            response_format={ "type": "json_object" },
            temperature=0.1,
            max_tokens=800, # Increased for detailed forensic evidence_notes
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Audit this capture. Schema: {CaptureClassification.model_json_schema()}"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]}
            ]
        )
        
        # Extraction logic
        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)
        
        # Pydantic v2 validation (Forensic Standard)
        return CaptureClassification.model_validate(parsed_data)
    
    except ValidationError as ve:
        # Graceful fallback for schema drift
        return CaptureClassification(
            milestone="Validation Error",
            floor="0",
            zone="Forensic_Failure",
            confidence=0.0,
            compliance_relevance=0,
            evidence_notes=f"NYC DOB Schema Mismatch: {str(ve)[:200]}"
        )
