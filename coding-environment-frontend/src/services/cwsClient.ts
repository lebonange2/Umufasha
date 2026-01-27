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

type JsonRpcResponse = {
  jsonrpc: '2.0';
  id: string | number;
  result?: any;
  error?: { code: number; message: string; data?: any };
};

export class CWSClient {
  private ws: WebSocketClient;
  private httpFallbackEnabled = false;

  constructor() {
    // Backend mounts websocket routes under /api/coding-environment
    this.ws = new WebSocketClient('/api/coding-environment/ws/cws');
  }

  async connect(): Promise<void> {
    try {
      await this.ws.connect();
      this.httpFallbackEnabled = false;
    } catch (e) {
      // Browser WebSockets can be blocked by some reverse proxies (common on RunPod).
      // Fall back to HTTP JSON-RPC which is proxied via standard HTTP.
      console.warn('CWS websocket connect failed; falling back to HTTP JSON-RPC', e);
      this.httpFallbackEnabled = true;
    }
  }

  disconnect(): void {
    this.ws.disconnect();
    this.httpFallbackEnabled = false;
  }

  isConnected(): boolean {
    return this.ws.isConnected() || this.httpFallbackEnabled;
  }

  private async rpc(method: string, params?: any): Promise<any> {
    const id = Date.now().toString();
    const payload = { jsonrpc: '2.0', id, method, params };

    // Prefer WebSocket when connected
    if (this.ws.isConnected() && !this.httpFallbackEnabled) {
      return new Promise((resolve, reject) => {
        const handler = (data: any) => {
          if (data?.id === id) {
            this.ws.off('message', handler);
            if (data.error) {
              reject(new Error(data.error.message || 'JSON-RPC error'));
            } else {
              resolve(data.result);
            }
          }
        };

        this.ws.on('message', handler);
        this.ws.send(payload);

        setTimeout(() => {
          this.ws.off('message', handler);
          reject(new Error('Request timeout'));
        }, 15000);
      });
    }

    // HTTP fallback
    const resp = await fetch('/api/coding-environment/cws/rpc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP RPC failed (${resp.status}): ${text}`);
    }
    const data = (await resp.json()) as JsonRpcResponse;
    if (data.error) {
      throw new Error(data.error.message || 'JSON-RPC error');
    }
    return data.result;
  }

  // File operations
  async readFile(path: string): Promise<string> {
    const result = await this.rpc('fs.read', { path });
    return result?.content ?? '';
  }

  async writeFile(path: string, content: string): Promise<void> {
    await this.rpc('fs.write', { path, contents: content });
  }

  async listFiles(path: string): Promise<FileInfo[]> {
    const result = await this.rpc('fs.list', { path });
    const entries = result?.entries || [];
    return entries.map((e: any) => ({
      path: e.path,
      name: e.name,
      type: e.type === 'dir' ? 'directory' : 'file',
      size: e.size,
      modified: e.mtime,
    })) as FileInfo[];
  }

  async searchFiles(query: string, path?: string): Promise<SearchResult[]> {
    const globs = path ? [`${path.replace(/\/$/, '')}/**/*`] : ['**/*'];
    const result = await this.rpc('search.find', { query, options: { globs, maxResults: 1000 } });
    const flat = result?.results || [];

    // Group by path to fit the existing UI shape
    const grouped = new Map<string, SearchResult>();
    for (const r of flat) {
      const key = r.path;
      if (!grouped.has(key)) grouped.set(key, { path: key, matches: [] });
      grouped.get(key)!.matches.push({
        line: r.line,
        column: r.column,
        text: r.text,
      });
    }
    return Array.from(grouped.values());
  }

  async runCommand(command: string, args: string[] = []): Promise<string> {
    const result = await this.rpc('task.run', { command, args, options: { confirmed: true } });
    const stdout = result?.stdout ?? '';
    const stderr = result?.stderr ?? '';
    const exitCode = result?.exitCode;
    const exitLine = typeof exitCode === 'number' ? `\n(exit ${exitCode})\n` : '\n';
    return `${stdout}${stderr ? `\n${stderr}` : ''}${exitLine}`.trimEnd();
  }
}
