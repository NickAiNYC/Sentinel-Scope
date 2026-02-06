"""
Data Simulator for Testing Opportunity Classifier
Generates "ugly" agency text and skewed data to ensure robust classification.
"""

import random
from datetime import datetime, timedelta
from typing import List

from packages.agents.opportunity.models import AgencyType


class OpportunitySimulator:
    """
    Generates realistic but messy NYC agency text samples.
    Mirrors the complexity and ambiguity of real-world procurement notices.
    """
    
    # Real-world ugly patterns from NYC agency sites
    UGLY_TEXT_PATTERNS = {
        "closed": [
            "Project #{proj_id} - {title} - PLANNING PHASE ONLY - contact {agency} for updates estimated {date}",
            "PRE-SOLICITATION NOTICE\n{title}\nEstimated Release: {date}\nThis is not a bid invitation.",
            "{title} - UNDER REVIEW - No bids accepted at this time\nFor information purposes only",
            "UPCOMING: {title} ({proj_id})\nTentative date: {date}\nCheck back later for bid documents",
            "{agency} announces future project: {title}\nNo RFP available yet. Planning stage.",
        ],
        "soft_open": [
            "{title} - MAY BE ACCEPTING PROPOSALS\nContact {agency} @ {phone}\nDeadline TBD",
            "Project {proj_id}: {title}\nBids due approximately {date}\nInsurance requirements: See agency website",
            "{title} - POSSIBLE BID OPPORTUNITY\nSubmit questions to {email}\nFormal RFP pending review",
            "NOTICE: {title}\nInterested contractors should contact {agency}\nBid deadline to be announced",
            "{agency} considering bids for {title}\nMay require bonding - details forthcoming",
        ],
        "contestable": [
            "REQUEST FOR PROPOSALS\n{title}\nProject ID: {proj_id}\nBid Deadline: {date} 2:00 PM\nSubmit to: {email}\nInsurance: GL $5M, WC $5M\nScope: {scope}",
            "NOW ACCEPTING BIDS - {title}\nDue: {date}\nContact: {agency} {phone}\nBond required: {value}\nGet bid docs at: {url}",
            "RFP #{proj_id}: {title}\nSubmission Deadline: {date} 5PM EST\nMandatory pre-bid: {prebid_date}\nDownload: {url}\nInsurance requirements: See section 7",
            "OPEN BID - {title}\n{agency}\nClosing: {date}\nEstimated Value: ${value}\nTrade: {trade}\nContact {email} for specifications",
        ]
    }
    
    AGENCY_CONTACTS = {
        AgencyType.SCA: {
            "phone": "718-472-8000",
            "email": "sca_procurement@schools.nyc.gov",
            "url": "https://www.nycsca.org/bids"
        },
        AgencyType.DDC: {
            "phone": "212-386-0400", 
            "email": "ddc_contracts@ddc.nyc.gov",
            "url": "https://www1.nyc.gov/site/ddc/contracts/contracts.page"
        },
        AgencyType.DOT: {
            "phone": "212-839-6550",
            "email": "dot_procurement@dot.nyc.gov",
            "url": "https://www.nyc.gov/dot/contracts"
        },
    }
    
    PROJECT_TITLES = [
        "PS 123 Roof Replacement and Waterproofing",
        "FDR Drive Bridge Rehabilitation Phase 2",
        "DEP Water Main Replacement - Queens Blvd",
        "NYCHA Elevator Modernization - Multiple Sites",
        "DDC Street Resurfacing - Brooklyn District 4",
        "SCA HVAC System Upgrade - 15 Schools",
        "DOT Traffic Signal Installation - Manhattan",
        "DEP Wastewater Treatment Plant Repairs",
    ]
    
    SCOPES = [
        "General construction including demo, structural work, and finishes",
        "Electrical and mechanical systems installation",
        "Heavy civil construction with concrete and steel work",
        "Envelope restoration and roofing systems",
    ]
    
    TRADES = [
        "General Construction",
        "Electrical",
        "Plumbing",
        "HVAC",
        "Fire Protection",
    ]
    
    def generate_sample(
        self,
        opportunity_type: str = "random",
        agency: AgencyType = AgencyType.SCA,
        include_errors: bool = True
    ) -> dict:
        """
        Generate a single ugly agency text sample.
        
        Args:
            opportunity_type: "closed", "soft_open", "contestable", or "random"
            agency: NYC agency posting the notice
            include_errors: Add typos, formatting issues, etc.
            
        Returns:
            Dict with project_id, title, agency_text, expected_classification
        """
        if opportunity_type == "random":
            opportunity_type = random.choice(["closed", "soft_open", "contestable"])
        
        # Generate fake project data
        proj_id = f"{agency.value}-{random.randint(1000, 9999)}"
        title = random.choice(self.PROJECT_TITLES)
        value = random.randint(500_000, 50_000_000)
        trade = random.choice(self.TRADES)
        scope = random.choice(self.SCOPES)
        
        # Get agency contact info
        contacts = self.AGENCY_CONTACTS.get(agency, {
            "phone": "212-639-9675",
            "email": "procurement@agency.nyc.gov",
            "url": "https://agency.nyc.gov/bids"
        })
        
        # Generate dates
        future_date = datetime.now() + timedelta(days=random.randint(10, 60))
        prebid_date = future_date - timedelta(days=7)
        
        # Select a template
        templates = self.UGLY_TEXT_PATTERNS[opportunity_type]
        template = random.choice(templates)
        
        # Fill in the template
        agency_text = template.format(
            proj_id=proj_id,
            title=title,
            agency=agency.value,
            date=future_date.strftime("%B %d, %Y"),
            prebid_date=prebid_date.strftime("%m/%d/%Y"),
            value=f"{value:,}",
            trade=trade,
            scope=scope,
            phone=contacts["phone"],
            email=contacts["email"],
            url=contacts["url"]
        )
        
        # Add realistic errors/messiness if requested
        if include_errors:
            agency_text = self._add_ugliness(agency_text)
        
        return {
            "project_id": proj_id,
            "title": title,
            "agency": agency,
            "agency_text": agency_text,
            "expected_classification": opportunity_type.upper(),
            "estimated_value": value,
            "trade_category": trade
        }
    
    def generate_batch(
        self,
        count: int = 10,
        distribution: dict = None
    ) -> List[dict]:
        """
        Generate a batch of test samples with controlled distribution.
        
        Args:
            count: Number of samples to generate
            distribution: Optional dict like {"closed": 0.5, "soft_open": 0.3, "contestable": 0.2}
            
        Returns:
            List of sample dicts
        """
        if distribution is None:
            # Default: Skewed toward CLOSED (realistic)
            distribution = {
                "closed": 0.6,      # 60% closed/planning
                "soft_open": 0.25,  # 25% ambiguous
                "contestable": 0.15 # 15% truly open
            }
        
        samples = []
        agencies = list(AgencyType)
        
        for _ in range(count):
            # Pick opportunity type based on distribution
            rand = random.random()
            cumulative = 0
            opp_type = "closed"
            
            for otype, prob in distribution.items():
                cumulative += prob
                if rand < cumulative:
                    opp_type = otype
                    break
            
            agency = random.choice(agencies)
            sample = self.generate_sample(
                opportunity_type=opp_type,
                agency=agency,
                include_errors=True
            )
            samples.append(sample)
        
        return samples
    
    def _add_ugliness(self, text: str) -> str:
        """Add realistic formatting issues and typos."""
        uglifications = [
            # Extra whitespace
            lambda t: t.replace("\n", "\n\n" if random.random() > 0.5 else "\n"),
            # ALL CAPS sections
            lambda t: t.upper() if random.random() > 0.8 else t,
            # Random capitalization
            lambda t: "".join(c.upper() if random.random() > 0.95 else c for c in t),
            # Tab characters
            lambda t: t.replace(" ", "\t" if random.random() > 0.9 else " "),
            # Common typos
            lambda t: t.replace("Deadline", "Deadlien" if random.random() > 0.9 else "Deadline"),
            lambda t: t.replace("contact", "contect" if random.random() > 0.9 else "contact"),
        ]
        
        # Apply 1-2 random uglifications
        num_ugly = random.randint(1, 2)
        for _ in range(num_ugly):
            uglify = random.choice(uglifications)
            text = uglify(text)
        
        return text


# Test function to demonstrate usage
def demo_simulator():
    """Demo the simulator capabilities."""
    simulator = OpportunitySimulator()
    
    print("=" * 80)
    print("OPPORTUNITY SIMULATOR DEMO")
    print("=" * 80)
    
    # Generate one of each type
    for opp_type in ["closed", "soft_open", "contestable"]:
        sample = simulator.generate_sample(
            opportunity_type=opp_type,
            agency=AgencyType.SCA,
            include_errors=True
        )
        
        print(f"\n{opp_type.upper()} Sample:")
        print("-" * 80)
        print(f"Project: {sample['title']}")
        print(f"ID: {sample['project_id']}")
        print(f"\nAgency Text:\n{sample['agency_text']}")
        print()
    
    # Generate a batch with skewed distribution
    print("\n" + "=" * 80)
    print("BATCH GENERATION (10 samples, realistic distribution)")
    print("=" * 80)
    
    batch = simulator.generate_batch(count=10)
    
    from collections import Counter
    distribution = Counter(s['expected_classification'] for s in batch)
    print(f"\nDistribution: {dict(distribution)}")
    

if __name__ == "__main__":
    demo_simulator()
