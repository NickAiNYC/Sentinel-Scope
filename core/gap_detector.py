"""
SentinelScope Gap Detector v2.7 (Enhanced - Dec 2025)
Integrates NYC BC 2022/2025 mapping, RapidFuzz Matching, and DeepSeek Reasoning.
Enhanced with: improved error handling, LRU caching, token tracking, and batch processing.
"""
from typing import List, Optional, Dict, Tuple
from rapidfuzz import fuzz, process
from openai import OpenAI
import streamlit as st
from functools import lru_cache
import time
from core.models import GapAnalysisResponse, ComplianceGap, CaptureClassification
from core.constants import NYC_BC_REFS


class ComplianceGapEngine:
    """
    Advanced compliance gap detection engine with AI-powered remediation.
    
    Features:
    - NYC Building Code 2022/2025 compliance mapping
    - RapidFuzz fuzzy matching for milestone detection
    - DeepSeek AI for cost-effective remediation reasoning
    - Token usage tracking and cost estimation
    - LRU caching for repeated analyses
    - Exponential backoff retry logic
    """
    
    # 2025 Enhanced Domain Logic
    TARGET_REQUIREMENTS = {
        "structural": {
            "Foundation": {"code": NYC_BC_REFS["STRUCTURAL"]["FOUNDATIONS"], "criticality": "Critical", "weight": 35},
            "Structural Steel": {"code": NYC_BC_REFS["STRUCTURAL"]["STEEL"], "criticality": "High", "weight": 25},
            "Fireproofing": {"code": NYC_BC_REFS["FIRE_PROTECTION"]["FIRE_RESISTANCE"], "criticality": "Critical", "weight": 20},
            "Cold-Formed Steel": {"code": "BC Section 2210", "criticality": "Medium", "weight": 10},
            "Exterior Walls": {"code": "BC Chapter 14", "criticality": "Medium", "weight": 10}
        },
        "mep": {
            "MEP Rough-in": {"code": NYC_BC_REFS["MEP"]["MECHANICAL"], "criticality": "High", "weight": 25},
            "Fire Protection": {"code": "BC Chapter 9", "criticality": "Critical", "weight": 35},
            "Electrical Distribution": {"code": "NYC Electrical Code (2025)", "criticality": "High", "weight": 25},
            "HVAC Installation": {"code": "MC Chapter 6", "criticality": "Medium", "weight": 15}
        }
    }
    
    # DeepSeek pricing (as of Dec 2025)
    DEEPSEEK_COST_PER_1K_TOKENS = 0.00027

    def __init__(self, project_type: str = "structural", fuzzy_threshold: int = 85):
        """
        Initialize the compliance gap engine.
        
        Args:
            project_type: Project category ('structural' or 'mep')
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching
        """
        self.project_type = project_type.lower()
        self.fuzzy_threshold = fuzzy_threshold
        self.rules = self.TARGET_REQUIREMENTS.get(
            self.project_type,
            self.TARGET_REQUIREMENTS["structural"]
        )
        self.total_tokens_used = 0
        self.total_api_cost = 0.0

    def _get_ai_remediation(
        self, 
        milestone: str, 
        code: str, 
        api_key: str, 
        max_retries: int = 3
    ) -> Tuple[str, Dict[str, float]]:
        """
        Uses DeepSeek (via OpenAI-compatible SDK) for NYC-specific remediation steps.
        
        Args:
            milestone: Missing milestone name
            code: NYC Building Code reference
            api_key: DeepSeek API key
            max_retries: Maximum retry attempts for failed requests
            
        Returns:
            Tuple of (remediation_text, usage_metrics)
        """
        prompt = (
            f"Act as a Senior NYC DOB Auditor. A project site is missing evidence of '{milestone}' "
            f"under {code}. Based on NYC BC 2022 and 2025 updates, provide 2 precise, "
            f"field-actionable remediation steps to clear this gap. Be concise and professional. "
            f"Respond with only the two steps, numbered."
        )
        
        for attempt in range(max_retries):
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                
                response = client.chat.completions.create(
                    model="deepseek-chat",  # DeepSeek-V3
                    max_tokens=200,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Track usage
                tokens_used = response.usage.total_tokens
                cost = tokens_used * self.DEEPSEEK_COST_PER_1K_TOKENS / 1000
                
                self.total_tokens_used += tokens_used
                self.total_api_cost += cost
                
                usage_metrics = {
                    "tokens": tokens_used,
                    "cost": cost
                }
                
                return response.choices[0].message.content.strip(), usage_metrics
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle specific error types
                if "rate_limit" in error_msg or "429" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        st.warning(f"⏸️ Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "⏸️ Rate limit exceeded. Please wait and try again.", {"tokens": 0, "cost": 0.0}
                        
                elif "api_key" in error_msg or "401" in error_msg or "authentication" in error_msg:
                    return "🔑 Invalid API key. Check credentials in Settings.", {"tokens": 0, "cost": 0.0}
                    
                elif "timeout" in error_msg or "connection" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt)
                        st.warning(f"🔌 Connection timeout. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"🔌 Connection failed after {max_retries} attempts.", {"tokens": 0, "cost": 0.0}
                        
                else:
                    st.error(f"⚠️ DeepSeek API error: {str(e)}")
                    return (
                        f"🚨 URGENT: Conduct physical site audit for {milestone}. "
                        f"Verify compliance with {code} immediately.",
                        {"tokens": 0, "cost": 0.0}
                    )
        
        # Fallback if all retries exhausted
        return (
            f"🚨 API unavailable. Manual audit required for {milestone} ({code}).",
            {"tokens": 0, "cost": 0.0}
        )

    @lru_cache(maxsize=100)
    def _get_ai_remediation_cached(
        self, 
        milestone: str, 
        code: str, 
        api_key: str
    ) -> Tuple[str, Dict[str, float]]:
        """
        Cached version of AI remediation to avoid redundant API calls.
        
        Note: LRU cache prevents duplicate calls for identical (milestone, code, api_key) tuples.
        Cache is cleared when the engine is re-instantiated.
        """
        return self._get_ai_remediation(milestone, code, api_key)

    def _get_batch_remediation(
        self, 
        gaps: List[Tuple[str, str]], 
        api_key: str
    ) -> List[Tuple[str, Dict[str, float]]]:
        """
        Process multiple gaps in one API call to reduce latency and cost.
        
        Args:
            gaps: List of (milestone, code) tuples
            api_key: DeepSeek API key
            
        Returns:
            List of (remediation_text, usage_metrics) tuples
        """
        if not gaps:
            return []
        
        # Build batch prompt
        prompt = (
            "Act as a Senior NYC DOB Auditor. The following milestones are missing evidence. "
            "For EACH milestone, provide 2 precise, field-actionable remediation steps based on NYC BC 2022/2025. "
            "Format your response as:\n\n"
            "**[Milestone Name]**\n1. [First step]\n2. [Second step]\n\n"
            "Missing milestones:\n"
        )
        
        for i, (milestone, code) in enumerate(gaps, 1):
            prompt += f"{i}. {milestone} ({code})\n"
        
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=500 + (len(gaps) * 100),  # Scale tokens with gap count
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track usage
            tokens_used = response.usage.total_tokens
            cost = tokens_used * self.DEEPSEEK_COST_PER_1K_TOKENS / 1000
            
            self.total_tokens_used += tokens_used
            self.total_api_cost += cost
            
            # Parse batch response (simplified - you may want more robust parsing)
            full_response = response.choices[0].message.content.strip()
            
            # Split by milestone markers
            sections = full_response.split("**")
            remediations = []
            
            for section in sections:
                if section.strip():
                    # Distribute cost evenly across gaps
                    per_gap_metrics = {
                        "tokens": tokens_used // len(gaps),
                        "cost": cost / len(gaps)
                    }
                    remediations.append((section.strip(), per_gap_metrics))
            
            # Ensure we have one remediation per gap
            while len(remediations) < len(gaps):
                remediations.append((
                    "🚨 URGENT: Conduct physical site audit. Verify compliance immediately.",
                    {"tokens": 0, "cost": 0.0}
                ))
            
            return remediations[:len(gaps)]
            
        except Exception as e:
            st.error(f"Batch remediation failed: {str(e)}")
            # Return fallback for all gaps
            return [(
                f"🚨 URGENT: Conduct physical site audit for {milestone}. Verify compliance with {code}.",
                {"tokens": 0, "cost": 0.0}
            ) for milestone, code in gaps]

    def detect_gaps(
        self, 
        findings: List[CaptureClassification], 
        api_key: Optional[str] = None,
        use_batch_processing: bool = False
    ) -> GapAnalysisResponse:
        """
        Analyzes AI findings against NYC regulatory requirements.
        
        Args:
            findings: List of classified milestones from computer vision
            api_key: DeepSeek API key (optional, for AI remediation)
            use_batch_processing: If True, process all gaps in one API call
            
        Returns:
            GapAnalysisResponse with missing milestones, scores, and recommendations
        """
        # Reset token tracking for this analysis
        self.total_tokens_used = 0
        self.total_api_cost = 0.0
        
        found_names = [f.milestone for f in findings if f.confidence > 0.6]

        missing_milestones = []
        earned_weight = 0
        total_weight = sum(info['weight'] for info in self.rules.values())
        
        # First pass: identify gaps
        gaps_to_process = []
        for req, info in self.rules.items():
            match_result = process.extractOne(req, found_names, scorer=fuzz.WRatio)
            is_present = match_result and match_result[1] >= self.fuzzy_threshold
            
            # Track match confidence
            match_confidence = "Not Found"
            if match_result:
                similarity = match_result[1]
                if similarity >= 95:
                    match_confidence = f"Exact Match ({similarity}%)"
                elif similarity >= self.fuzzy_threshold:
                    match_confidence = f"High Similarity ({similarity}%)"
                elif similarity >= 70:
                    match_confidence = f"Partial Match ({similarity}%)"

            if is_present:
                earned_weight += info['weight']
            else:
                gaps_to_process.append((req, info))

        # Second pass: get AI remediation (batch or individual)
        if api_key and gaps_to_process:
            if use_batch_processing and len(gaps_to_process) > 2:
                # Batch process for efficiency
                gap_tuples = [(req, info['code']) for req, info in gaps_to_process]
                remediations = self._get_batch_remediation(gap_tuples, api_key)
            else:
                # Individual processing with caching
                remediations = [
                    self._get_ai_remediation_cached(req, info['code'], api_key)
                    for req, info in gaps_to_process
                ]
        else:
            # No API key - use fallback
            remediations = [
                (f"Request photo evidence for {req}. Verify compliance with {info['code']}.", {"tokens": 0, "cost": 0.0})
                for req, info in gaps_to_process
            ]

        # Build gap objects
        severity_to_class = {
            "Critical": "Class C", 
            "High": "Class B", 
            "Medium": "Class B", 
            "Low": "Class A"
        }
        
        for (req, info), (remediation, metrics) in zip(gaps_to_process, remediations):
            current_class = severity_to_class.get(info["criticality"], "Class B")
            
            missing_milestones.append(ComplianceGap(
                milestone=req,
                floor_range="Audit Required",
                dob_code=info["code"],
                risk_level=info["criticality"],
                dob_class=current_class,
                deadline="Immediately" if info["criticality"] == "Critical" else "Within 7 Days",
                recommendation=remediation
            ))

        # Calculate scores
        compliance_score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
        risk_score = 100 - compliance_score

        # Determine priority
        critical_count = sum(1 for g in missing_milestones if g.risk_level == "Critical")
        if critical_count > 0:
            priority = f"🚨 {critical_count} CRITICAL GAPS: STOP WORK RISK"
        elif compliance_score < 75:
            priority = "⚠️ CAUTION: Significant Evidence Gaps"
        else:
            priority = "✅ COMPLIANT: Standard Monitoring"

        return GapAnalysisResponse(
            missing_milestones=missing_milestones,
            compliance_score=compliance_score,
            risk_score=risk_score,
            total_found=len(found_names),
            gap_count=len(missing_milestones),
            next_priority=priority
        )
    
    def get_usage_summary(self) -> Dict[str, any]:
        """
        Get summary of API usage and costs for the current session.
        
        Returns:
            Dictionary with tokens used and estimated cost
        """
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost_usd": round(self.total_api_cost, 4),
            "model": "deepseek-chat",
            "cost_per_1k_tokens": self.DEEPSEEK_COST_PER_1K_TOKENS
        }
    
    def reset_usage_tracking(self):
        """Reset token and cost tracking counters."""
        self.total_tokens_used = 0
        self.total_api_cost = 0.0
