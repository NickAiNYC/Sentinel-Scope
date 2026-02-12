"""Milestone taxonomy for construction project lifecycle tracking."""

from __future__ import annotations

from enum import StrEnum


class MilestonePhase(StrEnum):
    """High-level construction phases (jurisdiction-agnostic)."""

    PRE_CONSTRUCTION = "pre_construction"
    FOUNDATION = "foundation"
    STRUCTURE = "structure"
    ENCLOSURE = "enclosure"
    MEP_ROUGH_IN = "mep_rough_in"
    INTERIOR = "interior"
    COMMISSIONING = "commissioning"
    CLOSEOUT = "closeout"


class MilestoneTaxonomy:
    """Maps construction phases to typical milestones.

    The milestone lists are industry-standard defaults, portable across
    jurisdictions.  They may be extended per deployment.
    """

    _PHASE_MILESTONES: dict[MilestonePhase, list[str]] = {
        MilestonePhase.PRE_CONSTRUCTION: [
            "Site survey completed",
            "Geotechnical report accepted",
            "Demolition permit obtained",
            "Erosion control installed",
        ],
        MilestonePhase.FOUNDATION: [
            "Excavation completed",
            "Foundation footings poured",
            "Foundation walls completed",
            "Waterproofing applied",
            "Foundation inspection passed",
        ],
        MilestonePhase.STRUCTURE: [
            "Structural steel erected",
            "Concrete floors poured",
            "Shear walls completed",
            "Top-out achieved",
        ],
        MilestonePhase.ENCLOSURE: [
            "Exterior sheathing installed",
            "Window and curtain wall installation",
            "Roofing completed",
            "Building envelope inspection passed",
        ],
        MilestonePhase.MEP_ROUGH_IN: [
            "Mechanical rough-in completed",
            "Electrical rough-in completed",
            "Plumbing rough-in completed",
            "Fire suppression rough-in completed",
            "MEP rough-in inspection passed",
        ],
        MilestonePhase.INTERIOR: [
            "Drywall installed",
            "Interior finishes applied",
            "Flooring installed",
            "Cabinetry and fixtures installed",
        ],
        MilestonePhase.COMMISSIONING: [
            "HVAC commissioning completed",
            "Elevator inspection passed",
            "Fire alarm acceptance test",
            "Energy performance verification",
        ],
        MilestonePhase.CLOSEOUT: [
            "Punch list completed",
            "Certificate of occupancy issued",
            "Final inspection passed",
            "As-built drawings submitted",
        ],
    }

    @classmethod
    def get_phase_milestones(cls, phase: MilestonePhase) -> list[str]:
        """Return the typical milestones for *phase*."""
        return list(cls._PHASE_MILESTONES.get(phase, []))

    @classmethod
    def get_phase_for_milestone(cls, milestone_name: str) -> MilestonePhase | None:
        """Return the phase that contains *milestone_name* (fuzzy match).

        Performs case-insensitive substring matching against known
        milestones.  Returns ``None`` if no match is found.
        """
        needle = milestone_name.lower()
        for phase, milestones in cls._PHASE_MILESTONES.items():
            for ms in milestones:
                if needle in ms.lower() or ms.lower() in needle:
                    return phase
        return None
