# 📊 SentinelScope Data Layer

This directory contains the mock datasets and evidence captures used to demonstrate the AI-augmented compliance audit flow.

## 📁 Directory Structure
* `mock_frames.csv`: The primary database of simulated AI detections, linking timestamps and descriptions to specific NYC building milestones.
* `captures/`: (Placeholder) Local directory for site photos; in production, this resolves to an S3/Cloud Storage bucket.

## 🛠️ Schema Definition: `mock_frames.csv`
| Column | Type | Description |
| :--- | :--- | :--- |
| `date` | ISO-8601 | The date the site capture was taken.
| `description` | String | Human-readable site notes or automated OCR text.
| `image_path` | URI | Path to the source evidence file.
| `milestone` | Enum | The NYC BC-2022 milestone (e.g., Foundation, Structural Steel).
| `confidence` | Float (0-1) | The AI model's confidence score for the classification.
| `location_floor` | String | Geospatial floor reference (e.g., B1, L5).

## 🧪 Evaluation Data Context
The entries in this CSV are derived from a benchmark set of **312 labeled site images**. These samples are used to test the **Gap Detector logic** and ensure the UI correctly displays compliance scores and risk alerts.

## 🔄 Updating Data
To test new compliance scenarios (e.g., a "Fireproofing" failure), add a row to `mock_frames.csv` with a `confidence` score below `0.80` or omit a required milestone from a specific floor range.
