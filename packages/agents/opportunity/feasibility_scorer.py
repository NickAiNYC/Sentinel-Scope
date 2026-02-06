"""
Feasibility Scorer - Cross-references opportunities with internal compliance data.
Checks insurance limits and trade license requirements by agency.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .models import AgencyType, OpportunityClassification, OpportunityLevel


class InsuranceRequirement(BaseModel):
    """Insurance limits required by agency for bidding."""
    general_liability: int = Field(..., description="General liability coverage in dollars")
    workers_comp: int = Field(..., description="Workers compensation coverage")
    umbrella: Optional[int] = Field(None, description="Umbrella policy requirement")
    
    
class UserComplianceProfile(BaseModel):
    """Current compliance status for a contractor/user."""
    user_id: str
    company_name: str
    
    # Insurance coverage
    general_liability_limit: int
    workers_comp_limit: int
    umbrella_limit: Optional[int] = None
    insurance_expiry: datetime
    
    # Trade licenses
    active_licenses: List[str] = Field(
        default_factory=list,
        description="e.g., ['General Contractor', 'Electrical', 'Plumbing']"
    )
    license_expiry: Dict[str, datetime] = Field(default_factory=dict)
    
    # DOB credentials
    has_active_dob_registration: bool = False
    

class FeasibilityScore(BaseModel):
    """
    Results of feasibility check for a specific opportunity.
    """
    opportunity_id: str
    user_id: str
    
    # Overall status
    is_compliant: bool = Field(..., description="Green check indicator for dashboard")
    feasibility_score: float = Field(..., ge=0.0, le=100.0)
    
    # Detailed checks
    insurance_compliant: bool
    insurance_gaps: List[str] = Field(default_factory=list)
    
    license_compliant: bool
    license_gaps: List[str] = Field(default_factory=list)
    
    # Additional barriers
    other_barriers: List[str] = Field(default_factory=list)
    
    # Recommendations
    next_steps: List[str] = Field(default_factory=list)
    
    checked_at: datetime = Field(default_factory=datetime.now)


class FeasibilityScorer:
    """
    Checks if a user/contractor meets the requirements to bid on an opportunity.
    Only runs for CONTESTABLE opportunities (per problem statement).
    """
    
    # NYC Agency-specific insurance requirements (conservative estimates)
    AGENCY_INSURANCE_REQUIREMENTS: Dict[AgencyType, InsuranceRequirement] = {
        AgencyType.SCA: InsuranceRequirement(
            general_liability=5_000_000,
            workers_comp=5_000_000,
            umbrella=10_000_000
        ),
        AgencyType.DDC: InsuranceRequirement(
            general_liability=3_000_000,
            workers_comp=3_000_000,
            umbrella=5_000_000
        ),
        AgencyType.DEP: InsuranceRequirement(
            general_liability=2_000_000,
            workers_comp=2_000_000,
            umbrella=None
        ),
        AgencyType.DOT: InsuranceRequirement(
            general_liability=3_000_000,
            workers_comp=3_000_000,
            umbrella=5_000_000
        ),
        AgencyType.NYCHA: InsuranceRequirement(
            general_liability=2_000_000,
            workers_comp=2_000_000,
            umbrella=None
        ),
        AgencyType.OTHER: InsuranceRequirement(
            general_liability=1_000_000,
            workers_comp=1_000_000,
            umbrella=None
        ),
    }
    
    def check_feasibility(
        self,
        opportunity: OpportunityClassification,
        user_profile: UserComplianceProfile
    ) -> FeasibilityScore:
        """
        Check if user meets requirements to bid on this opportunity.
        
        Per problem statement: Only runs for CONTESTABLE opportunities.
        For CLOSED/SOFT_OPEN, returns a score indicating not ready.
        """
        # Quick exit for non-contestable opportunities
        if opportunity.opportunity_level != OpportunityLevel.CONTESTABLE:
            return FeasibilityScore(
                opportunity_id=opportunity.project_id,
                user_id=user_profile.user_id,
                is_compliant=False,
                feasibility_score=0.0,
                insurance_compliant=False,
                insurance_gaps=["Opportunity not confirmed as CONTESTABLE"],
                license_compliant=False,
                license_gaps=["Opportunity not confirmed as CONTESTABLE"],
                other_barriers=[f"Opportunity status: {opportunity.opportunity_level.value}"],
                next_steps=["Wait for opportunity to be classified as CONTESTABLE"]
            )
        
        # Check insurance requirements
        insurance_compliant, insurance_gaps = self._check_insurance(
            opportunity.agency, user_profile
        )
        
        # Check trade license requirements
        license_compliant, license_gaps = self._check_licenses(
            opportunity.trade_category, user_profile
        )
        
        # Check for other barriers
        other_barriers = self._check_other_barriers(user_profile)
        
        # Calculate overall feasibility score
        # Weight: 40% insurance, 40% license, 20% other factors
        insurance_score = 40.0 if insurance_compliant else 0.0
        license_score = 40.0 if license_compliant else 0.0
        other_score = 20.0 if len(other_barriers) == 0 else 0.0
        
        feasibility_score = insurance_score + license_score + other_score
        is_compliant = feasibility_score >= 80.0  # Need at least 80% to get green check
        
        # Generate next steps
        next_steps = self._generate_next_steps(
            insurance_gaps, license_gaps, other_barriers
        )
        
        return FeasibilityScore(
            opportunity_id=opportunity.project_id,
            user_id=user_profile.user_id,
            is_compliant=is_compliant,
            feasibility_score=feasibility_score,
            insurance_compliant=insurance_compliant,
            insurance_gaps=insurance_gaps,
            license_compliant=license_compliant,
            license_gaps=license_gaps,
            other_barriers=other_barriers,
            next_steps=next_steps
        )
    
    def _check_insurance(
        self, agency: AgencyType, profile: UserComplianceProfile
    ) -> tuple[bool, List[str]]:
        """Check if user's insurance meets agency requirements."""
        requirements = self.AGENCY_INSURANCE_REQUIREMENTS[agency]
        gaps = []
        
        # Check general liability
        if profile.general_liability_limit < requirements.general_liability:
            gaps.append(
                f"General Liability: Need ${requirements.general_liability:,}, "
                f"have ${profile.general_liability_limit:,}"
            )
        
        # Check workers comp
        if profile.workers_comp_limit < requirements.workers_comp:
            gaps.append(
                f"Workers Comp: Need ${requirements.workers_comp:,}, "
                f"have ${profile.workers_comp_limit:,}"
            )
        
        # Check umbrella if required
        if requirements.umbrella:
            if not profile.umbrella_limit or profile.umbrella_limit < requirements.umbrella:
                current = profile.umbrella_limit or 0
                gaps.append(
                    f"Umbrella Policy: Need ${requirements.umbrella:,}, "
                    f"have ${current:,}"
                )
        
        # Check expiry
        if profile.insurance_expiry < datetime.now():
            gaps.append(f"Insurance expired on {profile.insurance_expiry.date()}")
        
        return len(gaps) == 0, gaps
    
    def _check_licenses(
        self, trade_category: Optional[str], profile: UserComplianceProfile
    ) -> tuple[bool, List[str]]:
        """Check if user has active license for the trade."""
        gaps = []
        
        # If no specific trade category, require at least one active license
        if not trade_category:
            if not profile.active_licenses:
                gaps.append("No active trade licenses on file")
            return len(gaps) == 0, gaps
        
        # Map trade category to required license
        trade_to_license = {
            "General Construction": "General Contractor",
            "Electrical": "Electrical",
            "Plumbing": "Plumbing",
            "HVAC": "HVAC",
            "Fire Protection": "Fire Suppression",
        }
        
        required_license = trade_to_license.get(trade_category, "General Contractor")
        
        # Check if user has the required license
        if required_license not in profile.active_licenses:
            gaps.append(f"Missing required license: {required_license} for {trade_category}")
        else:
            # Check if license is expired
            if required_license in profile.license_expiry:
                expiry = profile.license_expiry[required_license]
                if expiry < datetime.now():
                    gaps.append(f"{required_license} license expired on {expiry.date()}")
        
        return len(gaps) == 0, gaps
    
    def _check_other_barriers(self, profile: UserComplianceProfile) -> List[str]:
        """Check for other compliance barriers (DOB registration, etc.)."""
        barriers = []
        
        if not profile.has_active_dob_registration:
            barriers.append("Missing active DOB registration")
        
        return barriers
    
    def _generate_next_steps(
        self,
        insurance_gaps: List[str],
        license_gaps: List[str],
        other_barriers: List[str]
    ) -> List[str]:
        """Generate actionable next steps to close compliance gaps."""
        steps = []
        
        if insurance_gaps:
            steps.append("📋 Update insurance coverage to meet agency requirements")
        
        if license_gaps:
            steps.append("📜 Obtain or renew required trade licenses")
        
        if other_barriers:
            steps.append("🏛️ Complete DOB registration/renewal")
        
        if not steps:
            steps.append("✅ Ready to bid - download bid documents from agency portal")
        
        return steps
