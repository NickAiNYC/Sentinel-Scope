"""
SentinelScope Gap Detection Engine
Identifies missing milestones and compliance gaps using fuzzy matching.
"""

import json
from dataclasses import dataclass

from openai import OpenAI
from rapidfuzz import fuzz


@dataclass
class MilestoneGap:
    """Represents a missing compliance milestone."""

    milestone: str
    dob_code: str
    risk_level: str
    dob_class: str
    deadline: str
    recommendation: str


@dataclass
class GapAnalysisResponse:
    """Complete gap analysis result."""

    compliance_score: int
    risk_score: int
    total_found: int
    gap_count: int
    next_priority: str
    missing_milestones: list[MilestoneGap]


class ComplianceGapEngine:
    """Detects compliance gaps using fuzzy matching and AI analysis."""

    # NYC Building Code 2022 Required Milestones by Project Type
    REQUIRED_MILESTONES = {
        "structural": [
            "Foundation Inspection",
            "Structural Frame Inspection",
            "Fireproofing Application",
            "Concrete Pour Inspection",
            "Rebar Inspection",
        ],
        "mep": [
            "Rough-in Inspection",
            "Final MEP Inspection",
            "HVAC Installation",
            "Electrical Rough-in",
            "Plumbing Rough-in",
        ],
        "fireproofing": [
            "Fireproofing Application",
            "Fire-rated Assembly Inspection",
            "Spray Fireproofing Documentation",
        ],
        "foundation": [
            "Foundation Inspection",
            "Excavation Safety Inspection",
            "Waterproofing Installation",
            "Foundation Pour",
        ],
    }

    def __init__(self, project_type: str = "structural", fuzzy_threshold: int = 85):
        """
        Initialize gap detector.

        Args:
            project_type: Type of project (structural, mep, fireproofing, foundation)
            fuzzy_threshold: Minimum similarity score for matching (0-100)
        """
        self.project_type = project_type.lower()
        self.fuzzy_threshold = fuzzy_threshold
        self.required_milestones = self.REQUIRED_MILESTONES.get(
            self.project_type, self.REQUIRED_MILESTONES["structural"]
        )
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost_usd": 0,
            "model": "deepseek-chat",
        }

    def detect_gaps(
        self,
        findings: list,
        api_key: str,
        use_batch_processing: bool = True,
    ) -> GapAnalysisResponse:
        """
        Detect compliance gaps by comparing findings to requirements.

        Args:
            findings: List of CaptureClassification objects
            api_key: DeepSeek API key
            use_batch_processing: Whether to batch API calls

        Returns:
            GapAnalysisResponse with analysis results
        """
        # Extract found milestones
        found_milestones = [f.milestone for f in findings if f.confidence > 0.5]

        # Find missing milestones using fuzzy matching
        missing = []
        for required in self.required_milestones:
            if not self._is_milestone_found(required, found_milestones):
                missing.append(required)

        # Generate gap analysis with AI
        if missing and api_key:
            gap_details = self._generate_gap_analysis(
                missing, api_key, use_batch_processing
            )
        else:
            gap_details = []

        # Calculate metrics
        total_found = len(found_milestones)
        gap_count = len(missing)
        total_required = len(self.required_milestones)

        compliance_score = int(
            (total_found / total_required * 100) if total_required > 0 else 100
        )

        # Risk scoring
        risk_score = self._calculate_risk_score(gap_details)

        # Priority determination
        next_priority = self._determine_priority(compliance_score, risk_score)

        return GapAnalysisResponse(
            compliance_score=compliance_score,
            risk_score=risk_score,
            total_found=total_found,
            gap_count=gap_count,
            next_priority=next_priority,
            missing_milestones=gap_details,
        )

    def _is_milestone_found(
        self, required_milestone: str, found_milestones: list[str]
    ) -> bool:
        """
        Check if required milestone is found using fuzzy matching.

        Args:
            required_milestone: Required milestone name
            found_milestones: List of found milestone names

        Returns:
            True if milestone found with sufficient similarity
        """
        for found in found_milestones:
            similarity = fuzz.ratio(required_milestone.lower(), found.lower())
            if similarity >= self.fuzzy_threshold:
                return True
        return False

    def _generate_gap_analysis(
        self, missing_milestones: list[str], api_key: str, use_batch: bool
    ) -> list[MilestoneGap]:
        """
        Generate detailed gap analysis using AI.

        Args:
            missing_milestones: List of missing milestone names
            api_key: DeepSeek API key
            use_batch: Whether to batch all gaps in one call

        Returns:
            List of MilestoneGap objects
        """
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        gap_results = []

        if use_batch:
            # Batch processing - all gaps in one call
            prompt = f"""For each missing construction milestone, \
provide compliance details.

Missing milestones: {', '.join(missing_milestones)}

Respond ONLY with valid JSON array in this exact format:
[
  {{
    "milestone": "milestone name",
    "dob_code": "NYC BC code (e.g., BC 3301.1)",
    "risk_level": "Critical|High|Medium|Low",
    "dob_class": "Class 1|2|3",
    "deadline": "timeline (e.g., '7 days', '30 days')",
    "recommendation": "specific remediation steps"
  }}
]"""

            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.3,
                )

                # Update usage stats
                usage = response.usage
                self.usage_stats["total_tokens"] += usage.total_tokens
                self.usage_stats["total_cost_usd"] += (
                    usage.total_tokens * 0.00000014
                )  # DeepSeek pricing

                # Parse response
                content = response.choices[0].message.content
                json_start = content.find("[")
                json_end = content.rfind("]") + 1
                json_str = content[json_start:json_end]

                gaps_data = json.loads(json_str)

                for gap_data in gaps_data:
                    gap_results.append(
                        MilestoneGap(
                            milestone=gap_data.get("milestone", "Unknown"),
                            dob_code=gap_data.get("dob_code", "N/A"),
                            risk_level=gap_data.get("risk_level", "Medium"),
                            dob_class=gap_data.get("dob_class", "Class 2"),
                            deadline=gap_data.get("deadline", "30 days"),
                            recommendation=gap_data.get(
                                "recommendation", "Consult with inspector"
                            ),
                        )
                    )

            except Exception:
                # Fallback to default gaps
                for milestone in missing_milestones:
                    gap_results.append(self._create_default_gap(milestone))

        else:
            # Individual processing - one call per gap
            for milestone in missing_milestones:
                try:
                    prompt = f"""Provide NYC Building Code compliance details \
for missing milestone: {milestone}

Respond ONLY with valid JSON in this exact format:
{{
  "milestone": "{milestone}",
  "dob_code": "NYC BC code",
  "risk_level": "Critical|High|Medium|Low",
  "dob_class": "Class 1|2|3",
  "deadline": "timeline",
  "recommendation": "remediation steps"
}}"""

                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500,
                        temperature=0.3,
                    )

                    # Update usage stats
                    usage = response.usage
                    self.usage_stats["total_tokens"] += usage.total_tokens
                    self.usage_stats["total_cost_usd"] += (
                        usage.total_tokens * 0.00000014
                    )

                    # Parse response
                    content = response.choices[0].message.content
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_str = content[json_start:json_end]

                    gap_data = json.loads(json_str)

                    gap_results.append(
                        MilestoneGap(
                            milestone=gap_data.get("milestone", milestone),
                            dob_code=gap_data.get("dob_code", "N/A"),
                            risk_level=gap_data.get("risk_level", "Medium"),
                            dob_class=gap_data.get("dob_class", "Class 2"),
                            deadline=gap_data.get("deadline", "30 days"),
                            recommendation=gap_data.get(
                                "recommendation", "Consult with inspector"
                            ),
                        )
                    )

                except Exception:
                    gap_results.append(self._create_default_gap(milestone))

        return gap_results

    def _create_default_gap(self, milestone: str) -> MilestoneGap:
        """
        Create default gap when AI analysis fails.

        Args:
            milestone: Milestone name

        Returns:
            MilestoneGap with default values
        """
        return MilestoneGap(
            milestone=milestone,
            dob_code="TBD",
            risk_level="Medium",
            dob_class="Class 2",
            deadline="30 days",
            recommendation="Schedule inspection with NYC DOB inspector",
        )

    def _calculate_risk_score(self, gaps: list[MilestoneGap]) -> int:
        """
        Calculate overall risk score based on gaps.

        Args:
            gaps: List of MilestoneGap objects

        Returns:
            Risk score (0-100, higher is worse)
        """
        if not gaps:
            return 0

        risk_weights = {"Critical": 100, "High": 75, "Medium": 50, "Low": 25}

        total_risk = sum(risk_weights.get(g.risk_level, 50) for g in gaps)
        max_risk = len(gaps) * 100

        return int((total_risk / max_risk * 100) if max_risk > 0 else 0)

    def _determine_priority(self, compliance_score: int, risk_score: int) -> str:
        """
        Determine priority status based on scores.

        Args:
            compliance_score: Compliance percentage
            risk_score: Risk score (0-100)

        Returns:
            Priority status string
        """
        if compliance_score >= 90 and risk_score < 30:
            return "✅ EXCELLENT - All systems compliant"
        if compliance_score >= 75 and risk_score < 50:
            return "👍 ACCEPTABLE - Minor gaps detected"
        if compliance_score >= 60 or risk_score < 70:
            return "⚠️ CAUTION - Immediate action required"
        return "🚨 CRITICAL - Major compliance failures"

    def get_usage_summary(self) -> dict[str, int | float | str]:
        """
        Get API usage statistics.

        Returns:
            Dictionary with usage metrics
        """
        return {
            "total_tokens": self.usage_stats["total_tokens"],
            "total_cost_usd": self.usage_stats["total_cost_usd"],
            "model": self.usage_stats["model"],
            "cost_per_token": 0.00000014,  # DeepSeek pricing
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost_usd": 0,
            "model": "deepseek-chat",
        }
