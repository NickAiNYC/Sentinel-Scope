# Vision Agent API Reference

## Base URL

```
https://api.concomply.ai/v1/vision
```

## Authentication

All endpoints require a Bearer token:

```
Authorization: Bearer <API_KEY>
```

---

## Endpoints

### POST `/api/v1/vision/analyze`

Analyze a single site photo through the 5-agent pipeline
(Vision → Permit → Synthesis → RedTeam → Risk → DecisionProof).

**Request Body**

| Field             | Type     | Required | Description                       |
|-------------------|----------|----------|-----------------------------------|
| `bbl`             | string   | ✅       | NYC BBL identifier                |
| `address`         | string   | ❌       | Human-readable address            |
| `image_url`       | string   | ❌       | URL or base64-encoded image data  |
| `findings`        | array    | ❌       | Pre-processed vision findings     |
| `violations`      | array    | ❌       | Known violations                  |
| `compliance_score`| float    | ❌       | Compliance score 0–100            |
| `risk_score`      | float    | ❌       | Risk score 0–100                  |

**Response**

```json
{
  "analysis_id": "uuid",
  "bbl": "1012650001",
  "proof_id": "uuid",
  "sha256_hash": "a3f2...c9e1",
  "compliance_score": 85.0,
  "risk_score": 20.0,
  "summary": "Site 1012650001: 1 images, 2 findings, 0 violations."
}
```

---

### POST `/api/v1/vision/batch`

Batch-process multiple site photos through the 5-agent pipeline.

**Request Body**

| Field              | Type     | Required | Description                    |
|--------------------|----------|----------|--------------------------------|
| `bbl`              | string   | ✅       | NYC BBL identifier             |
| `address`          | string   | ❌       | Human-readable address         |
| `images`           | string[] | ❌       | List of image URLs/paths       |
| `findings`         | array    | ❌       | Pre-processed vision findings  |
| `violations`       | array    | ❌       | Known violations               |
| `dob_violations`   | array    | ❌       | Live DOB violation records     |
| `compliance_score` | float    | ❌       | Compliance score 0–100         |
| `risk_score`       | float    | ❌       | Risk score 0–100               |

**Response** — Same schema as `/analyze`.

---

### GET `/api/v1/vision/compliance/{bbl}`

Return aggregated compliance summary for a BBL.

**Path Parameters**

| Parameter | Type   | Description          |
|-----------|--------|----------------------|
| `bbl`     | string | NYC BBL identifier   |

**Response**

```json
{
  "bbl": "1012650001",
  "status": "active",
  "analyses": 3,
  "proofs": 3,
  "latest_compliance_score": 90.0,
  "latest_risk_score": 10.0,
  "total_images": 15,
  "total_findings": 8,
  "total_violations": 2,
  "cost_usd": 0.0015
}
```

---

## Construction Intelligence Endpoints

### GET `/api/v1/intel/opportunities`

Return available SCA/DDC/EDA project opportunities.

### POST `/api/v1/intel/bid-analysis`

Evaluate whether to bid on a project.

**Request Body**

| Field                | Type     | Required | Description                  |
|----------------------|----------|----------|------------------------------|
| `project_id`         | string   | ✅       | Project identifier           |
| `agency`             | string   | ❌       | Agency code (SCA, DDC, etc.) |
| `contractor_trades`  | string[] | ❌       | Contractor trade list        |
| `contractor_capacity`| float    | ❌       | Available capacity 0–1       |

### GET `/api/v1/intel/competitor/{bbl}`

Return competitor activity intelligence for a BBL.

---

## 5-Agent Pipeline

Every request flows through the ConComplyAi 5-agent architecture:

```
VisionAgent → PermitAgent → SynthesisAgent → RedTeamAgent → RiskScorer
```

1. **VisionAgent** — Processes site photos with DeepSeek-V3
2. **PermitAgent** — Cross-references with NYC DOB permit database
3. **SynthesisAgent** — Merges findings and violations
4. **RedTeamAgent** — Adversarial validation (reduces FP by 15%)
5. **RiskScorer** — Final scoring + SHA-256 DecisionProof

## Cost

| Resource     | Cost per unit |
|--------------|---------------|
| Image        | $0.0001       |
| Document     | $0.0007       |

## DecisionProof

Every audit generates an immutable SHA-256 hash of the analysis
payload for tamper-proof audit trails. The hash covers:

- `analysis_id`, `bbl`, `images_processed`
- `compliance_score`, `risk_score`
- `findings_count`, `violations_count`
- `timestamp`
