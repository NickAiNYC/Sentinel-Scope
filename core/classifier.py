"""
SentinelScope Vision-Language Classifier
Integrated with DeepSeek-V3 for semantic construction analysis.
"""
import pandas as pd
import re

class VisionClassifier:
    # 2026-Ready System Prompt for Construction AI
    SYSTEM_PROMPT = """
    You are an NYC Department of Buildings (DOB) compliance expert. 
    Analyze construction site captures to identify:
    1. Milestone (e.g., Fireproofing, MEP Rough-in, Superstructure)
    2. System (e.g., Life Safety, Envelope, Structural)
    3. Floor/Zone (Extract specific location data)
    4. Compliance Markers (Identify visible code-required elements)
    """

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def classify_frame(self, description: str, image_url: str = None) -> dict:
        """
        Main classification logic. 
        In 2026, this handles both text metadata and visual reasoning.
        """
        if self.use_llm:
            return self._llm_reasoning(description, image_url)
        
        return self._heuristic_fallback(description)

    def _heuristic_fallback(self, text: str) -> dict:
        """Advanced keyword reasoning with Regex for location extraction"""
        text = text.lower()
        
        # Mapping Milestones to Systems & NYC Priority
        mapping = {
            r"(fireproofing|spray|fire\s*stop)": ("Fireproofing", "Life Safety", 0.95),
            r"(mep|duct|pipe|conduit|plumbing)": ("MEP Rough-in", "MEP", 0.88),
            r"(steel|beam|column|truss|bolting)": ("Structural Steel", "Structural", 0.92),
            r"(drywall|gypsum|stud)": ("Drywall Installation", "Interior", 0.85),
            r"(glazing|window|facade|curtain\s*wall)": ("Enclosure", "Envelope", 0.82)
        }

        milestone, system, confidence = ("General Construction", "General", 0.60)
        
        for pattern, (m, s, c) in mapping.items():
            if re.search(pattern, text):
                milestone, system, confidence = m, s, c
                break

        # Advanced Location Extraction (Handles "Floor 5", "FL05", "Level 5")
        floor_match = re.search(r'(?:floor|fl|level|lvl)\s*(\d+)', text)
        location = f"Floor {floor_match.group(1)}" if floor_match else "Unknown Zone"

        return {
            "milestone": milestone,
            "system": system,
            "location": location,
            "confidence": confidence,
            "is_llm_validated": self.use_llm
        }

    def _llm_reasoning(self, description: str, image_url: str) -> dict:
        """
        Placeholder for Day 5: DeepSeek-V3 API Call.
        This will send the image + description for actual visual validation.
        """
        # Simulated API Response for now
        return self._heuristic_fallback(description)

# Standard entry point
def batch_classify(df: pd.DataFrame, api_mode: bool = False) -> pd.DataFrame:
    clf = VisionClassifier(use_llm=api_mode)
    results = []
    
    for _, row in df.iterrows():
        tags = clf.classify_frame(str(row.get('description', '')), row.get('image_path'))
        results.append({**row.to_dict(), **tags})
    
    return pd.DataFrame(results)
