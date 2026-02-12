# Drone Analytics

## Overview

The Drone Analytics Bridge (`core/drone_analytics_bridge.py`) processes
drone flight metadata, estimates material volumes, and builds 4D
construction timelines.

## Capabilities

| Feature              | Description                                  |
|----------------------|----------------------------------------------|
| Capture Ingestion    | Parse flight metadata (area, altitude, GPS)  |
| Volume Estimation    | Excavation, concrete, fill volumes in CY     |
| 4D Timeline          | Date-stamped milestone progress entries      |
| Processing Estimate  | Target: < 5 min per acre                     |

## Usage

```python
from core.drone_analytics_bridge import DroneAnalyticsBridge

drone = DroneAnalyticsBridge()
result = drone.analyze(
    bbl="1012650001",
    captures=[
        {"area_acres": 2.0, "altitude_ft": 250, "image_count": 200},
    ],
    image_findings=[
        {"name": "excavation complete", "volume_cy": 2340, "confidence": 0.90},
    ],
    timeline_entries=[
        {
            "date": "2026-01-15T10:00:00",
            "milestone": "EXCAVATION",
            "progress_pct": 87,
        },
    ],
)
print(result.summary)
# Drone survey complete: 200 images over 2.0 acres.
# 2,340 CY excavation. 87% of planned progress.
```

## Volume Materials

The bridge recognizes three material categories from image findings:

- **Excavation**: Keywords — excavation, excavated, trench, dig
- **Concrete**: Keywords — concrete, pour, slab, footing
- **Fill**: Keywords — fill, backfill, grading

## Processing Performance

Target processing time is **< 5 minutes per acre** (300 seconds).
The simulated estimate uses 50% of the maximum budget per acre.
