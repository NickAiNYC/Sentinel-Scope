/**
 * VisionAuditView – ConComplyAi Veteran View integration.
 *
 * Renders side-by-side site photo → compliance findings with
 * violation overlay bounding boxes, confidence scores, and
 * one-click DecisionProof receipt generation.
 */

import React, { useState } from "react";

/* ---------- Types ---------- */

export interface Finding {
  id: string;
  label: string;
  confidence: number; // 0–100
  severity: "Critical" | "High" | "Medium" | "Low";
  bbox?: { x: number; y: number; w: number; h: number };
}

export interface DecisionProof {
  proofId: string;
  sha256Hash: string;
  complianceScore: number;
  riskScore: number;
  agentChain: string[];
  timestamp: string;
  summary: string;
}

export interface VisionAuditViewProps {
  imageUrl: string;
  findings: Finding[];
  decisionProof: DecisionProof | null;
  bbl: string;
  onGenerateProof?: () => void;
}

/* ---------- Helpers ---------- */

const severityColor: Record<string, string> = {
  Critical: "#8B0000",
  High: "#E25822",
  Medium: "#FFBF00",
  Low: "#4F7942",
};

/* ---------- Component ---------- */

const VisionAuditView: React.FC<VisionAuditViewProps> = ({
  imageUrl,
  findings,
  decisionProof,
  bbl,
  onGenerateProof,
}) => {
  const [selectedFinding, setSelectedFinding] = useState<string | null>(null);

  return (
    <div style={{ display: "flex", gap: 24, fontFamily: "sans-serif" }}>
      {/* Left: Site Photo with Overlays */}
      <div style={{ position: "relative", flex: 1 }}>
        <h3>Site Photo – BBL {bbl}</h3>
        <div style={{ position: "relative", display: "inline-block" }}>
          <img
            src={imageUrl}
            alt={`Site ${bbl}`}
            style={{ maxWidth: "100%", borderRadius: 4 }}
          />
          {findings
            .filter((f) => f.bbox)
            .map((f) => (
              <div
                key={f.id}
                onClick={() => setSelectedFinding(f.id)}
                style={{
                  position: "absolute",
                  left: `${f.bbox!.x}%`,
                  top: `${f.bbox!.y}%`,
                  width: `${f.bbox!.w}%`,
                  height: `${f.bbox!.h}%`,
                  border: `2px solid ${severityColor[f.severity] || "#ccc"}`,
                  cursor: "pointer",
                  boxSizing: "border-box",
                }}
                title={`${f.label} (${f.confidence}%)`}
              />
            ))}
        </div>
      </div>

      {/* Right: Findings + Proof */}
      <div style={{ flex: 1 }}>
        <h3>Compliance Findings</h3>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {findings.map((f) => (
            <li
              key={f.id}
              onClick={() => setSelectedFinding(f.id)}
              style={{
                padding: 8,
                marginBottom: 4,
                borderLeft: `4px solid ${severityColor[f.severity]}`,
                background:
                  selectedFinding === f.id ? "#f0f0f0" : "transparent",
                cursor: "pointer",
              }}
            >
              <strong>{f.label}</strong> – {f.severity} –{" "}
              <span>{f.confidence}%</span>
            </li>
          ))}
        </ul>

        {/* DecisionProof receipt */}
        {decisionProof && (
          <div
            style={{
              marginTop: 16,
              padding: 12,
              border: "1px solid #ccc",
              borderRadius: 4,
            }}
          >
            <h4>DecisionProof Receipt</h4>
            <p>
              <strong>SHA-256:</strong>{" "}
              <code>{decisionProof.sha256Hash}</code>
            </p>
            <p>
              Compliance: {decisionProof.complianceScore}% | Risk:{" "}
              {decisionProof.riskScore}%
            </p>
            <p>
              Agents: {decisionProof.agentChain.join(" → ")}
            </p>
            <small>{decisionProof.timestamp}</small>
          </div>
        )}

        {!decisionProof && onGenerateProof && (
          <button
            onClick={onGenerateProof}
            style={{
              marginTop: 16,
              padding: "8px 16px",
              background: "#5C4033",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            Generate DecisionProof
          </button>
        )}
      </div>
    </div>
  );
};

export default VisionAuditView;
