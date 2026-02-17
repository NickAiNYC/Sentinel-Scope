"""
VisualScoutAgent: DeepSeek-V3 Vision Analysis for NYC Construction Sites

Integrated from 'Scope' into SiteSentinel-AI's Agent Theater.
Analyzes site imagery for progress milestones and Chapter 33 safety violations.

Position in workflow: VISUAL_SCOUT → guard → fixer → proof
"""

import os
from typing import Any, Dict, Optional

import httpx

from .base_agent import BaseAgent


class VisualScoutAgent(BaseAgent):
    """
    The 'Eyes' of SiteSentinel-AI.
    
    Responsibilities:
    - Analyze construction site photos using DeepSeek-V3 Vision
    - Identify active construction milestones (e.g., Foundation, MEP)
    - Flag NYC Building Code Chapter 33 safety violations
    - Pass structured findings to GuardAgent for legal verification
    
    Economics: $0.0012/image vs $500-2000 manual site audit
    """
    
    def __init__(self):
        """Initialize VisualScoutAgent with DeepSeek credentials."""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        self.endpoint = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"  # DeepSeek-V3 with vision capabilities
        self.timeout = 30.0
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute vision analysis on site imagery.
        
        Args:
            state: LangGraph state containing:
                - image_url (Optional[str]): URL or base64 data URL
                - site_id (Optional[str]): Site UUID
                - org_id (Optional[str]): Organization UUID
        
        Returns:
            State update with:
                - visual_findings (str): Structured analysis results
                - agent_source (str): "VisualScout"
                - requires_legal_verification (bool): True
                - confidence_score (float): 0.0-1.0
        
        Graceful Degradation:
            If no image_url provided, passes state forward without error.
        """
        image_url = state.get("image_url")
        
        # SAFETY CHECK: Graceful degradation if no image provided
        if not image_url:
            return {
                "visual_findings": None,
                "agent_source": "VisualScout",
                "skipped_reason": "No site imagery provided",
                "requires_legal_verification": False
            }
        
        # Build NYC BC Chapter 33 compliance prompt
        prompt = self._build_chapter_33_prompt()
        
        # Call DeepSeek-V3 Vision API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": image_url}
                                    }
                                ]
                            }
                        ],
                        "temperature": 0.1,  # Low temp for forensic consistency
                        "max_tokens": 1500
                    },
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract vision analysis
                analysis = result['choices'][0]['message']['content']
                
                # Parse structured data from response
                findings = self._parse_findings(analysis)
                
                return {
                    "visual_findings": findings["text"],
                    "milestones_detected": findings.get("milestones", []),
                    "violations_detected": findings.get("violations", []),
                    "confidence_score": findings.get("confidence", 0.7),
                    "agent_source": "VisualScout",
                    "requires_legal_verification": True,
                    "vision_model": self.model
                }
        
        except httpx.TimeoutException:
            return {
                "visual_findings": f"Vision API timeout after {self.timeout}s",
                "agent_source": "VisualScout",
                "error": "timeout",
                "requires_legal_verification": False
            }
        
        except httpx.HTTPStatusError as e:
            return {
                "visual_findings": f"Vision API error: {e.response.status_code}",
                "agent_source": "VisualScout",
                "error": f"http_{e.response.status_code}",
                "requires_legal_verification": False
            }
        
        except Exception as e:
            return {
                "visual_findings": f"Vision analysis failed: {str(e)}",
                "agent_source": "VisualScout",
                "error": "unexpected",
                "requires_legal_verification": False
            }
    
    def _build_chapter_33_prompt(self) -> str:
        """
        Build NYC Building Code Chapter 33 focused prompt.
        
        Chapter 33 covers construction site safety, which is critical
        for DOB compliance and insurance verification.
        """
        return """ACT AS: Senior NYC Department of Buildings Inspector

TASK: Analyze this construction site photo for compliance verification.

ANALYSIS REQUIREMENTS:

1. PROGRESS MILESTONES (NYC BC 2022 Chapter 33)
   Identify visible construction phases:
   - Excavation & Foundation (BC §3304)
   - Superstructure (BC §3308)
   - MEP Rough-in (BC Chapter 28)
   - Facade/Envelope (BC Chapter 14)
   - Interior Finishes
   
2. CHAPTER 33 SAFETY VIOLATIONS
   Flag any visible violations:
   - Fall Protection (BC §3314.1): Guardrails, safety nets, personal fall arrest
   - Scaffold Safety (BC §3314.9): Proper construction, tie-ins, platforms
   - Material Storage (BC §3303): Proper stacking, load limits, access
   - Fire Safety (BC §3308): Combustible storage, access, sprinklers
   - Site Access Control (BC §3301): Perimeter fencing, signage

3. EVIDENCE QUALITY
   - Floor level visible? (Required for milestone mapping)
   - Safety equipment status?
   - Photo clarity/completeness?

OUTPUT FORMAT (JSON-like):
```
MILESTONE: [Primary phase observed]
FLOOR: [Visible floor level or "Unknown"]
SAFETY_STATUS: [Compliant | Warning | Violation]
VIOLATIONS: [List specific BC sections if any]
CONFIDENCE: [0.0 to 1.0]
NOTES: [Context for Guard agent verification]
```

Be specific with Building Code section references."""
    
    def _parse_findings(self, analysis: str) -> Dict[str, Any]:
        """
        Parse structured data from vision analysis.
        
        Extracts:
        - Milestones detected
        - Violations (if any)
        - Confidence score
        """
        import re
        
        findings = {
            "text": analysis,
            "milestones": [],
            "violations": [],
            "confidence": 0.7
        }
        
        # Extract milestone
        milestone_match = re.search(r'MILESTONE:\s*(.+?)(?:\n|$)', analysis, re.IGNORECASE)
        if milestone_match:
            findings["milestones"] = [milestone_match.group(1).strip()]
        
        # Extract violations
        violations_match = re.search(
            r'VIOLATIONS:\s*(.+?)(?:\n\n|\nCONFIDENCE|$)',
            analysis,
            re.IGNORECASE | re.DOTALL
        )
        if violations_match:
            violations_text = violations_match.group(1).strip()
            if violations_text.lower() not in ["none", "n/a", "[]"]:
                # Split by common delimiters
                violations = [v.strip() for v in re.split(r'[,;\n-]', violations_text) if v.strip()]
                findings["violations"] = violations
        
        # Extract confidence
        confidence_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', analysis, re.IGNORECASE)
        if confidence_match:
            try:
                findings["confidence"] = float(confidence_match.group(1))
            except ValueError:
                pass
        
        return findings
