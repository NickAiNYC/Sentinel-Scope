/**
 * SafetyHeatMap – Live safety violation risk display by site zone.
 *
 * Displays:
 *   - Grid of site zones colored by risk level
 *   - OSHA violation history overlay
 *   - Inspector visit probability
 *   - "Red zone" flagging for immediate action
 */

import React from "react";

/* ---------- Types ---------- */

export interface ZoneRisk {
  zoneId: string;
  zoneName: string;
  riskLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  violationCount: number;
  inspectorProbability: number; // 0-100
  topViolation?: string;
}

export interface SafetyHeatMapProps {
  bbl: string;
  zones: ZoneRisk[];
  overallRisk: string;
}

/* ---------- Helpers ---------- */

const riskColors: Record<string, string> = {
  CRITICAL: "#8B0000",
  HIGH: "#E25822",
  MEDIUM: "#FFBF00",
  LOW: "#4F7942",
};

/* ---------- Component ---------- */

const SafetyHeatMap: React.FC<SafetyHeatMapProps> = ({
  bbl,
  zones,
  overallRisk,
}) => {
  return (
    <div style={{ fontFamily: "sans-serif" }}>
      <h3>Safety Heat Map – BBL {bbl}</h3>
      <p>
        Overall Risk:{" "}
        <span
          style={{
            fontWeight: 700,
            color: riskColors[overallRisk] || "#333",
          }}
        >
          {overallRisk}
        </span>
      </p>

      {/* Zone grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: 12,
        }}
      >
        {zones.map((z) => (
          <div
            key={z.zoneId}
            style={{
              border: `2px solid ${riskColors[z.riskLevel]}`,
              borderRadius: 6,
              padding: 12,
              background:
                z.riskLevel === "CRITICAL"
                  ? "rgba(139,0,0,0.08)"
                  : "transparent",
            }}
          >
            <strong>{z.zoneName}</strong>
            <div
              style={{
                marginTop: 4,
                fontSize: 13,
                color: riskColors[z.riskLevel],
                fontWeight: 600,
              }}
            >
              {z.riskLevel}
            </div>
            <div style={{ fontSize: 12, marginTop: 4 }}>
              Violations: {z.violationCount}
            </div>
            <div style={{ fontSize: 12 }}>
              Inspector prob: {z.inspectorProbability}%
            </div>
            {z.topViolation && (
              <div style={{ fontSize: 11, marginTop: 4, fontStyle: "italic" }}>
                {z.topViolation}
              </div>
            )}
            {z.riskLevel === "CRITICAL" && (
              <div
                style={{
                  marginTop: 8,
                  padding: "2px 6px",
                  background: "#8B0000",
                  color: "#fff",
                  borderRadius: 3,
                  fontSize: 11,
                  display: "inline-block",
                }}
              >
                🚨 RED ZONE
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SafetyHeatMap;
