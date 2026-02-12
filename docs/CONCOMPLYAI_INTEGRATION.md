# ConComplyAi Integration Guide

## Overview

Sentinel-Scope serves as the **Vision & Site Intelligence** layer for
ConComplyAi's 5-agent construction compliance architecture.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Sentinel-Scope  │────▶│  Vision Agent   │────▶│  Synthesis      │
│ Site Photos     │     │  (DeepSeek-V3)  │     │  Agent          │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│ DOB Engine      │────▶│  Permit Agent   │──────────────┘
│ Live Violations │     │  (NYC Codes)    │     ┌────────┴────────┐
└─────────────────┘     └─────────────────┘     │  Red Team       │
                                                 │  Agent          │
┌─────────────────┐     ┌─────────────────┐     └────────┬────────┘
│ Opportunity     │────▶│  Risk Scorer    │──────────────┘
│ Matcher         │     │  (Final Audit)  │     ┌────────┴────────┐
└─────────────────┘     └─────────────────┘     │  DecisionProof  │
                                                 │  SHA-256 Ledger │
                                                 └─────────────────┘
```

## Agent Roles

| Agent           | Module                             | Purpose                         |
|-----------------|------------------------------------|---------------------------------|
| VisionAgent     | `packages/vision_agent_bridge.py`  | Site photo analysis             |
| PermitAgent     | `violations/dob/dob_engine.py`     | Live DOB violation sync         |
| SynthesisAgent  | `packages/vision_agent_bridge.py`  | Merges vision + permit data     |
| RedTeamAgent    | `packages/vision_agent_bridge.py`  | Adversarial validation (−15% FP)|
| RiskScorer      | `packages/vision_agent_bridge.py`  | Final scoring + DecisionProof   |

## Shared Memory

Agents communicate via `SharedMemory`, an in-process state store:

```python
from packages.vision_agent_bridge import VisionAgentBridge

bridge = VisionAgentBridge()
proof = bridge.run_full_pipeline(
    bbl="1012650001",
    images_processed=12,
    findings=[...],
    dob_violations=[...],
    compliance_score=85.0,
    risk_score=20.0,
)
print(proof.sha256_hash)  # Tamper-proof audit hash
```

## Local Law Bridges

| Bridge               | Module                                   | Detection Target                       |
|----------------------|------------------------------------------|----------------------------------------|
| LL149 Inspector      | `packages/ll149_inspector_bridge.py`     | Superintendent presence on site        |
| LL152 Gas Tracker    | `packages/ll152_gas_tracker_bridge.py`   | Gas piping + inspection stickers       |
| LL11 Facade Vision   | `packages/ll11_facade_vision_bridge.py`  | Facade cracks, spalling, bulges        |

## Enhanced Vision Modules

| Module                   | File                                   | Capability                          |
|--------------------------|----------------------------------------|-------------------------------------|
| Safety Violation Detector| `core/safety_violation_detector.py`    | OSHA 1926 (8 violation types)       |
| Progress Tracker AI      | `core/progress_tracker_ai.py`          | Milestone % complete verification   |
| Drone Analytics Bridge   | `core/drone_analytics_bridge.py`       | Aerial volume + timeline analysis   |

## API Endpoints

See [VISION_AGENT_API.md](./VISION_AGENT_API.md) for full reference.

## DecisionProof

Every site audit generates an immutable `DecisionProofRecord`:

- SHA-256 hash of the analysis payload
- Full agent chain: Vision → Permit → Synthesis → RedTeam → Risk
- Compliance and risk scores
- Timestamp for legal/compliance audit trails

## Token Cost Tracking

| Resource | Cost       |
|----------|------------|
| Image    | $0.0001    |
| Document | $0.0007    |

All costs are tracked automatically via `TokenUsage` in shared memory.
