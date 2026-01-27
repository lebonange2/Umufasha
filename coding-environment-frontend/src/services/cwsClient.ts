/** CWS (Coding Workspace Service) client. */
import { WebSocketClient } from './websocket';

export interface FileInfo {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

export interface SearchResult {
  path: string;
  matches: Array<{
    line: number;
    column: number;
    text: string;
  }>;
}

export class CWSClient {
  private ws: WebSocketClient;

  constructor() {
    this.ws = new WebSocketClient('/ws/cws');
  }

  async connect(): Promise<void> {
    await this.ws.connect();
  }

  disconnect(): void {
    this.ws.disconnect();
  }

  isConnected(): boolean {
    return this.ws.isConnected();
  }

  // File operations
  async readFile(path: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const requestId = Date.now().toString();
      
      const handler = (data: any) => {
        if (data.id === requestId) {
          this.ws.off('message', handler);
          if (data.error) {
            reject(new Error(data.error.message || 'Failed to read file'));
          } else {
            resolve(data.result?.content || '');
          }
        }
      };

      this.ws.on('message', handler);

      this.ws.send({
        jsonrpc: '2.0',
        id: requestId,
        method: 'fs.read',
        params: { path }
      });

      // Timeout after 10 seconds
      setTimeout(() => {
        this.ws.off('message', handler);
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  async writeFile(path: string, content: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const requestId = Date.now().toString();
      
      const handler = (data: any) => {
        if (data.id === requestId) {
          this.ws.off('message', handler);
          if (data.error) {
            reject(new Error(data.error.message || 'Failed to write file'));
          } else {
            resolve();
          }
        }
      };

      this.ws.on('message', handler);

      this.ws.send({
        jsonrpc: '2.0',
        id: requestId,
        method: 'fs.write',
        params: { path, content }
      });

      setTimeout(() => {
        this.ws.off('message', handler);
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  async listFiles(path: string): Promise<FileInfo[]> {
    return new Promise((resolve, reject) => {
      const requestId = Date.now().toString();
      
      const handler = (data: any) => {
        if (data.id === requestId) {
          this.ws.off('message', handler);
          if (data.error) {
            reject(new Error(data.error.message || 'Failed to list files'));
          } else {
            resolve(data.result?.files || []);
          }
        }
      };

      this.ws.on('message', handler);

      this.ws.send({
        jsonrpc: '2.0',
        id: requestId,
        method: 'fs.list',
        params: { path }
      });

      setTimeout(() => {
        this.ws.off('message', handler);
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  async searchFiles(query: string, path?: string): Promise<SearchResult[]> {
    return new Promise((resolve, reject) => {
      const requestId = Date.now().toString();
      
      const handler = (data: any) => {
        if (data.id === requestId) {
          this.ws.off('message', handler);
          if (data.error) {
            reject(new Error(data.error.message || 'Failed to search files'));
          } else {
            resolve(data.result?.results || []);
          }
        }
      };

      this.ws.on('message', handler);

      this.ws.send({
        jsonrpc: '2.0',
        id: requestId,
        method: 'search.find',
        params: { query, path: path || '.' }
      });

      setTimeout(() => {
        this.ws.off('message', handler);
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  async runCommand(command: string, args: string[] = []): Promise<string> {
    return new Promise((resolve, reject) => {
      const requestId = Date.now().toString();
      
      const handler = (data: any) => {
        if (data.id === requestId) {
          this.ws.off('message', handler);
          if (data.error) {
            reject(new Error(data.error.message || 'Command failed'));
          } else {
            resolve(data.result?.output || '');
          }
        }
      };

      this.ws.on('message', handler);

      this.ws.send({
        jsonrpc: '2.0',
        id: requestId,
        method: 'tasks.run',
        params: {
          command,
          args,
          options: { confirmed: true }
        }
      });

      setTimeout(() => {
        this.ws.off('message', handler);
        reject(new Error('Request timeout'));
      }, 30000);
    });
  }
}
