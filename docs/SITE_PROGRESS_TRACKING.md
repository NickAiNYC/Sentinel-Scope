# Site Progress Tracking

## Overview

The Progress Tracker AI (`core/progress_tracker_ai.py`) automates
construction milestone verification using image-based evidence
from Sentinel-Scope's VisionAgent.

## Milestones Tracked

| Key              | Milestone Name                   |
|------------------|----------------------------------|
| EXCAVATION       | Foundation & Earthwork           |
| SUPERSTRUCTURE   | Structural Frame / Superstructure|
| MEP_ROUGH_IN     | MEP Rough-in                     |
| ENCLOSURE        | Building Envelope & Glazing      |
| INTERIOR_FINISH  | Drywall & Interior Finishes      |
| TOP_OUT          | Roofing & Mechanical Bulkhead    |

## Usage

```python
from core.progress_tracker_ai import ProgressTrackerAI

tracker = ProgressTrackerAI()
report = tracker.analyze_progress(
    bbl="1012650001",
    image_findings=[
        {"milestone": "EXCAVATION", "confidence": 1.0},
        {"milestone": "SUPERSTRUCTURE", "confidence": 0.30},
    ],
    scheduled={"EXCAVATION": 100.0, "SUPERSTRUCTURE": 50.0},
    change_orders=[
        {"id": "CO-1", "amount": 15000, "reason": "Unforeseen rock"},
    ],
)
print(report.summary)
# Overall: 21.7% complete. Foundation & Earthwork 100.0% complete. ...
```

## Features

- **Milestone Verification**: Marks milestones as verified when
  actual completion reaches ≥95% based on VisionAgent confidence
- **Schedule Variance**: Calculates weeks ahead/behind schedule
- **Change Order Tracking**: Stores change order evidence for audits
- **Lien Waiver Milestones**: Lists milestones at 100% completion
  suitable for lien waiver release
- **Summary Generation**: Human-readable progress summary
