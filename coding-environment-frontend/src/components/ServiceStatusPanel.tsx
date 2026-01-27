import { ServiceStatus } from '../services/api';
import './ServiceStatusPanel.css';

interface ServiceStatusPanelProps {
  servicesStatus: { mcp: ServiceStatus; cws: ServiceStatus } | null;
  onStart: (service: 'mcp' | 'cws') => void;
  onStop: (service: 'mcp' | 'cws') => void;
}

export default function ServiceStatusPanel({ servicesStatus, onStart, onStop }: ServiceStatusPanelProps) {
  if (!servicesStatus) {
    return <div className="service-status-panel">Loading...</div>;
  }

  return (
    <div className="service-status-panel">
      <div className="service-item">
        <span className="service-name">MCP Server</span>
        <span className={`status-indicator ${servicesStatus.mcp.running ? 'running' : 'stopped'}`}>
          {servicesStatus.mcp.running ? '●' : '○'}
        </span>
        {servicesStatus.mcp.running ? (
          <button onClick={() => onStop('mcp')} className="control-button stop">
            Stop
          </button>
        ) : (
          <button onClick={() => onStart('mcp')} className="control-button start">
            Start
          </button>
        )}
      </div>
      
      <div className="service-item">
        <span className="service-name">CWS</span>
        <span className={`status-indicator ${servicesStatus.cws.running ? 'running' : 'stopped'}`}>
          {servicesStatus.cws.running ? '●' : '○'}
        </span>
        {servicesStatus.cws.running ? (
          <button onClick={() => onStop('cws')} className="control-button stop">
            Stop
          </button>
        ) : (
          <button onClick={() => onStart('cws')} className="control-button start">
            Start
          </button>
        )}
      </div>
    </div>
  );
}
