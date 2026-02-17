/**
 * AgentTheater Component for SiteSentinel-AI
 * 
 * Visual orchestration timeline showing agent execution flow.
 * Updated to include VisualScout node from Scope integration.
 * 
 * Flow: VisualScout → Guard → Fixer → Proof
 */

import React, { useState, useEffect } from 'react';
import { ImageUpload } from './ImageUpload';

// ============================================================================
// TYPES
// ============================================================================

interface AgentNode {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed' | 'skipped';
  icon: string;
  description: string;
}

interface VisionFindings {
  milestones: string[];
  violations: string[];
  confidence: number;
  summary: string;
}

interface AgentTheaterProps {
  siteId: string;
  orgId: string;
  onAnalysisComplete?: (result: any) => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export const AgentTheater: React.FC<AgentTheaterProps> = ({
  siteId,
  orgId,
  onAnalysisComplete
}) => {
  const [agents, setAgents] = useState<AgentNode[]>([
    {
      id: 'visual_scout',
      name: 'Visual Scout',
      status: 'pending',
      icon: '👁️',
      description: 'AI Vision Analysis (DeepSeek-V3)'
    },
    {
      id: 'guard',
      name: 'Legal Guard',
      status: 'pending',
      icon: '⚖️',
      description: 'NYC LL149/152 Verification'
    },
    {
      id: 'fixer',
      name: 'Remediation Fixer',
      status: 'pending',
      icon: '🔧',
      description: 'Action Plan Generator'
    },
    {
      id: 'proof',
      name: 'Proof Generator',
      status: 'pending',
      icon: '🔐',
      description: 'SHA-256 Audit Trail'
    }
  ]);

  const [visionFindings, setVisionFindings] = useState<VisionFindings | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // ============================================================================
  // WEBSOCKET CONNECTION
  // ============================================================================

  useEffect(() => {
    // Connect to WebSocket for real-time agent updates
    const websocket = new WebSocket(`ws://localhost:8000/ws/theater/${siteId}`);

    websocket.onopen = () => {
      console.log('Agent Theater connected');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleAgentUpdate(data);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('Agent Theater disconnected');
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [siteId]);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleAgentUpdate = (data: any) => {
    const { agent, status, findings } = data;

    // Update agent status
    setAgents(prev =>
      prev.map(a =>
        a.id === agent
          ? { ...a, status }
          : a
      )
    );

    // Store vision findings for display
    if (agent === 'visual_scout' && findings) {
      setVisionFindings(findings);
    }

    // Notify parent component on completion
    if (agent === 'proof' && status === 'completed') {
      onAnalysisComplete?.(data);
    }
  };

  const handleImageUpload = async (file: File) => {
    // Upload image and trigger pipeline
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Set Visual Scout to active
      setAgents(prev =>
        prev.map(a =>
          a.id === 'visual_scout'
            ? { ...a, status: 'active' }
            : a
        )
      );

      const response = await fetch(`/api/sites/${siteId}/upload-evidence`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      const result = await response.json();

      if (result.analysis_status === 'completed') {
        setImageUrl(result.image_url);
        // WebSocket will handle agent status updates
      } else {
        // Handle failure
        setAgents(prev =>
          prev.map(a =>
            a.id === 'visual_scout'
              ? { ...a, status: 'failed' }
              : a
          )
        );
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setAgents(prev =>
        prev.map(a =>
          a.id === 'visual_scout'
            ? { ...a, status: 'failed' }
            : a
        )
      );
    }
  };

  const handleSkipVision = () => {
    // Graceful degradation: Skip vision analysis if no image
    setAgents(prev =>
      prev.map(a =>
        a.id === 'visual_scout'
          ? { ...a, status: 'skipped' }
          : a.id === 'guard'
          ? { ...a, status: 'active' }
          : a
      )
    );

    // Trigger pipeline without image
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'start_pipeline',
        skip_vision: true
      }));
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="agent-theater">
      {/* Header */}
      <div className="theater-header">
        <h2>🎭 Agent Theater</h2>
        <p>Multi-Agent Compliance Pipeline</p>
      </div>

      {/* Evidence Upload */}
      <div className="evidence-section">
        <ImageUpload
          onUpload={handleImageUpload}
          onSkip={handleSkipVision}
          siteId={siteId}
        />
      </div>

      {/* Agent Timeline */}
      <div className="agent-timeline">
        {agents.map((agent, index) => (
          <div
            key={agent.id}
            className={`agent-node agent-node--${agent.status}`}
          >
            <div className="agent-icon">
              {agent.icon}
            </div>
            <div className="agent-info">
              <h3>{agent.name}</h3>
              <p>{agent.description}</p>
              <span className={`status-badge status-${agent.status}`}>
                {agent.status}
              </span>
            </div>
            {index < agents.length - 1 && (
              <div className="agent-connector" />
            )}
          </div>
        ))}
      </div>

      {/* Vision Findings Display */}
      {visionFindings && (
        <div className="vision-findings">
          <h3>👁️ Visual Scout Findings</h3>
          
          <div className="findings-grid">
            {/* Milestones */}
            {visionFindings.milestones.length > 0 && (
              <div className="findings-card">
                <h4>Construction Milestones</h4>
                <ul>
                  {visionFindings.milestones.map((milestone, i) => (
                    <li key={i}>{milestone}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Violations */}
            {visionFindings.violations.length > 0 && (
              <div className="findings-card findings-card--warning">
                <h4>⚠️ Potential Violations</h4>
                <ul>
                  {visionFindings.violations.map((violation, i) => (
                    <li key={i}>{violation}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Confidence */}
            <div className="findings-card">
              <h4>Analysis Confidence</h4>
              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{ width: `${visionFindings.confidence * 100}%` }}
                />
              </div>
              <span>{(visionFindings.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Summary */}
          <div className="findings-summary">
            <p>{visionFindings.summary}</p>
          </div>
        </div>
      )}

      <style jsx>{`
        .agent-theater {
          background: #1a1a2e;
          color: #eee;
          padding: 2rem;
          border-radius: 12px;
          font-family: 'Inter', sans-serif;
        }

        .theater-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .theater-header h2 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .evidence-section {
          margin-bottom: 2rem;
        }

        .agent-timeline {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin: 2rem 0;
        }

        .agent-node {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.5rem;
          background: #2a2a3e;
          border-radius: 8px;
          border: 2px solid transparent;
          transition: all 0.3s ease;
        }

        .agent-node--pending {
          opacity: 0.5;
        }

        .agent-node--active {
          border-color: #00d9ff;
          box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
          animation: pulse 2s infinite;
        }

        .agent-node--completed {
          border-color: #00ff88;
        }

        .agent-node--failed {
          border-color: #ff4444;
        }

        .agent-node--skipped {
          opacity: 0.3;
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }

        .agent-icon {
          font-size: 3rem;
        }

        .agent-info {
          flex: 1;
        }

        .agent-info h3 {
          margin: 0 0 0.25rem 0;
          font-size: 1.25rem;
        }

        .agent-info p {
          margin: 0 0 0.5rem 0;
          color: #aaa;
          font-size: 0.9rem;
        }

        .status-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        .status-pending { background: #555; }
        .status-active { background: #00d9ff; color: #000; }
        .status-completed { background: #00ff88; color: #000; }
        .status-failed { background: #ff4444; }
        .status-skipped { background: #333; }

        .agent-connector {
          position: absolute;
          left: 50%;
          height: 1rem;
          width: 2px;
          background: #444;
        }

        .vision-findings {
          background: #2a2a3e;
          padding: 1.5rem;
          border-radius: 8px;
          margin-top: 2rem;
        }

        .vision-findings h3 {
          margin-bottom: 1rem;
        }

        .findings-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .findings-card {
          background: #1a1a2e;
          padding: 1rem;
          border-radius: 6px;
          border: 1px solid #444;
        }

        .findings-card--warning {
          border-color: #ff9800;
          background: rgba(255, 152, 0, 0.1);
        }

        .findings-card h4 {
          margin: 0 0 0.75rem 0;
          font-size: 1rem;
        }

        .findings-card ul {
          margin: 0;
          padding-left: 1.25rem;
        }

        .findings-card li {
          margin-bottom: 0.5rem;
        }

        .confidence-bar {
          width: 100%;
          height: 8px;
          background: #333;
          border-radius: 4px;
          overflow: hidden;
          margin: 0.5rem 0;
        }

        .confidence-fill {
          height: 100%;
          background: linear-gradient(90deg, #ff4444, #ffaa00, #00ff88);
          transition: width 0.5s ease;
        }

        .findings-summary {
          padding: 1rem;
          background: #1a1a2e;
          border-left: 3px solid #00d9ff;
          margin-top: 1rem;
        }
      `}</style>
    </div>
  );
};

export default AgentTheater;
