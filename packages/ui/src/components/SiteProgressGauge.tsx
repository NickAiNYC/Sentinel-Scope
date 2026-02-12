/**
 * SiteProgressGauge – Visual construction progress indicator.
 *
 * Displays:
 *   - Overall percent complete gauge
 *   - Schedule variance indicator
 *   - Milestone achievement timeline
 *   - Evidence gallery thumbnails
 */

import React from "react";

/* ---------- Types ---------- */

export interface Milestone {
  key: string;
  name: string;
  scheduledPct: number;
  actualPct: number;
  verified: boolean;
}

export interface EvidenceItem {
  id: string;
  thumbnailUrl: string;
  milestone: string;
  capturedAt: string;
}

export interface SiteProgressGaugeProps {
  bbl: string;
  overallPct: number;
  scheduleVarianceWeeks: number;
  milestones: Milestone[];
  evidence?: EvidenceItem[];
}

/* ---------- Helpers ---------- */

function gaugeColor(pct: number): string {
  if (pct >= 80) return "#4F7942";
  if (pct >= 50) return "#FFBF00";
  return "#8B0000";
}

function varianceLabel(weeks: number): string {
  if (weeks > 0) return `${weeks} wks ahead`;
  if (weeks < 0) return `${Math.abs(weeks)} wks behind`;
  return "On schedule";
}

/* ---------- Component ---------- */

const SiteProgressGauge: React.FC<SiteProgressGaugeProps> = ({
  bbl,
  overallPct,
  scheduleVarianceWeeks,
  milestones,
  evidence = [],
}) => {
  const color = gaugeColor(overallPct);

  return (
    <div style={{ fontFamily: "sans-serif" }}>
      <h3>Site Progress – BBL {bbl}</h3>

      {/* Gauge bar */}
      <div
        style={{
          background: "#eee",
          borderRadius: 8,
          overflow: "hidden",
          height: 28,
          marginBottom: 8,
        }}
      >
        <div
          style={{
            width: `${overallPct}%`,
            background: color,
            height: "100%",
            transition: "width 0.4s ease",
            lineHeight: "28px",
            color: "#fff",
            textAlign: "center",
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {overallPct}%
        </div>
      </div>

      {/* Schedule variance */}
      <p style={{ color: scheduleVarianceWeeks < 0 ? "#8B0000" : "#4F7942" }}>
        {varianceLabel(scheduleVarianceWeeks)}
      </p>

      {/* Milestone timeline */}
      <h4>Milestones</h4>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Milestone</th>
            <th>Scheduled</th>
            <th>Actual</th>
            <th>Verified</th>
          </tr>
        </thead>
        <tbody>
          {milestones.map((m) => (
            <tr key={m.key} style={{ borderBottom: "1px solid #ddd" }}>
              <td>{m.name}</td>
              <td style={{ textAlign: "center" }}>{m.scheduledPct}%</td>
              <td style={{ textAlign: "center" }}>{m.actualPct}%</td>
              <td style={{ textAlign: "center" }}>{m.verified ? "✅" : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Evidence gallery */}
      {evidence.length > 0 && (
        <>
          <h4>Evidence Gallery</h4>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {evidence.map((e) => (
              <div key={e.id} style={{ textAlign: "center" }}>
                <img
                  src={e.thumbnailUrl}
                  alt={e.milestone}
                  style={{ width: 80, height: 80, objectFit: "cover", borderRadius: 4 }}
                />
                <div style={{ fontSize: 11 }}>{e.milestone}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default SiteProgressGauge;
