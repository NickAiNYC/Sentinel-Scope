"""
Conservative Opportunity Classifier
Uses skeptical-by-default prompt engineering to avoid false positives.
"""

import json
from typing import Optional

import anthropic

from .models import (
    AgencyType,
    DecisionProof,
    OpportunityClassification,
    OpportunityLevel,
)


class OpportunityClassifier:
    """
    Classifies NYC project opportunities with extreme skepticism.
    Philosophy: Assume CLOSED unless clear evidence proves otherwise.
    """
    
    SKEPTICAL_SYSTEM_PROMPT = """You are a conservative NYC procurement analyst with 20+ years of experience.
Your job is to protect contractors from wasting time on dead-end opportunities.

CLASSIFICATION RULES (Strict Hierarchy):
1. CLOSED: Default assumption. Use unless explicit bidding language exists.
   - Pre-solicitation notices
   - "Planning phase", "Under review", "Upcoming"
   - No bid deadline mentioned
   - Historical project updates
   
2. SOFT_OPEN: Only if some bidding signals exist but critical info is missing
   - Bid deadline mentioned but unclear submission process
   - "May be accepting proposals" (vague language)
   - Missing required insurance amounts or bonding requirements
   
3. CONTESTABLE: Requires ALL of these:
   - Explicit "Request for Proposals/Bids" or "Now Accepting Bids"
   - Clear submission deadline (specific date)
   - Defined scope of work
   - Contact information for bid documents

SKEPTICAL MINDSET:
- If text is ambiguous → classify as CLOSED
- If you're 70% sure it's open → classify as SOFT_OPEN (not CONTESTABLE)
- Only classify as CONTESTABLE if 90%+ certain
- Look for red flags: "pre-solicitation", "planning", "estimated", "tentative"

OUTPUT FORMAT (JSON):
{
  "opportunity_level": "CLOSED|SOFT_OPEN|CONTESTABLE",
  "confidence": 0.0-1.0,
  "reasoning": "Explain your skeptical analysis",
  "text_signals": ["quote key phrases"],
  "red_flags": ["list any warning signs"]
}"""

    def __init__(self, api_key: str):
        """Initialize with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-4-5-opus-20251101"
    
    def classify(
        self,
        project_id: str,
        project_title: str,
        agency_text: str,
        agency: AgencyType = AgencyType.OTHER,
        estimated_value: Optional[float] = None,
        trade_category: Optional[str] = None,
    ) -> OpportunityClassification:
        """
        Classify an opportunity using skeptical prompt analysis.
        
        Args:
            project_id: Unique identifier for the project
            project_title: Project name/title
            agency_text: Raw text from agency website/notification
            agency: NYC agency posting the opportunity
            estimated_value: Project value estimate (if available)
            trade_category: Type of work (e.g., "General Construction")
            
        Returns:
            OpportunityClassification with DecisionProof audit trail
        """
        # Build user prompt with context
        estimated_value_str = f"${estimated_value:,.0f}" if estimated_value else "Unknown"
        user_prompt = f"""Analyze this NYC agency project notification:

AGENCY: {agency.value}
PROJECT: {project_title}
ESTIMATED VALUE: {estimated_value_str}
TRADE: {trade_category or "General Construction"}

RAW TEXT:
{agency_text}

Apply your skeptical analysis and return the classification JSON."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.1,  # Low temp for consistent, conservative decisions
                system=self.SKEPTICAL_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            # Parse Claude's structured response
            content = response.content[0].text
            
            # Extract JSON from response (Claude may wrap in markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            # Create DecisionProof audit trail
            decision_proof = DecisionProof(
                decision=OpportunityLevel(data["opportunity_level"]),
                confidence=float(data["confidence"]),
                reasoning=data["reasoning"],
                text_signals=data.get("text_signals", []),
                red_flags=data.get("red_flags", []),
                ai_model=self.model
            )
            
            # Build complete classification
            return OpportunityClassification(
                project_id=project_id,
                project_title=project_title,
                agency=agency,
                opportunity_level=decision_proof.decision,
                decision_proof=decision_proof,
                raw_text=agency_text,
                estimated_value=estimated_value,
                trade_category=trade_category
            )
            
        except Exception as e:
            # On error, default to CLOSED (skeptical fallback)
            fallback_proof = DecisionProof(
                decision=OpportunityLevel.CLOSED,
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}. Defaulting to CLOSED per skeptical policy.",
                text_signals=[],
                red_flags=[f"ERROR: {str(e)}"],
                ai_model=self.model
            )
            
            return OpportunityClassification(
                project_id=project_id,
                project_title=project_title,
                agency=agency,
                opportunity_level=OpportunityLevel.CLOSED,
                decision_proof=fallback_proof,
                raw_text=agency_text,
                estimated_value=estimated_value,
                trade_category=trade_category
            )
