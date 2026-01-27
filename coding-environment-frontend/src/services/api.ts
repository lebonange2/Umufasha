/** API client for coding environment management. */

const API_BASE = '/api/coding-environment';

export interface ServiceStatus {
  name: string;
  running: boolean;
  pid?: number;
  port?: number;
  url?: string;
}

export interface ServicesStatus {
  mcp: ServiceStatus;
  cws: ServiceStatus;
}

export class CodingEnvironmentAPI {
  static async getStatus(): Promise<ServicesStatus> {
    const response = await fetch(`${API_BASE}/status`);
    if (!response.ok) {
      throw new Error('Failed to get service status');
    }
    return response.json();
  }

  static async startService(serviceName: 'mcp' | 'cws'): Promise<void> {
    const response = await fetch(`${API_BASE}/services/${serviceName}/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'start' })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start service');
    }
  }

  static async stopService(serviceName: 'mcp' | 'cws'): Promise<void> {
    const response = await fetch(`${API_BASE}/services/${serviceName}/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'stop' })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to stop service');
    }
  }

  static async getModels(): Promise<{ models: Array<{ value: string; label: string; provider: string }>; provider: string }> {
    const response = await fetch(`${API_BASE}/models`);
    if (!response.ok) {
      throw new Error('Failed to get models');
    }
    return response.json();
  }
}
