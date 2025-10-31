import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as ws from 'ws';

export class McpClient implements vscode.Disposable {
    private process?: child_process.ChildProcess;
    private websocket?: ws.WebSocket;
    private requestId = 0;
    private pendingRequests = new Map<number, { resolve: (value: any) => void; reject: (error: any) => void }>();

    async connect(): Promise<void> {
        // Connect via stdio
        const config = vscode.workspace.getConfiguration('assistantAiCodingEnv');
        const mcpCommand = config.get<string>('mcp.command', 'python3');
        const mcpArgs = config.get<string[]>('mcp.args', ['-m', 'mcp.server', '--transport', 'stdio']);

        this.process = child_process.spawn(mcpCommand, mcpArgs, {
            cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd()
        });

        this.process.stdout?.on('data', (data) => {
            this.handleMessage(data.toString());
        });

        this.process.stderr?.on('data', (data) => {
            console.error('MCP stderr:', data.toString());
        });

        // Initialize
        await this.request('initialize', {
            protocolVersion: '2024-11-05',
            capabilities: {},
            clientInfo: {
                name: 'vscode-extension',
                version: '1.0.0'
            }
        });

        // Send initialized notification
        this.notify('initialized', {});
    }

    async request(method: string, params?: any): Promise<any> {
        const id = ++this.requestId;
        const request = {
            jsonrpc: '2.0',
            id,
            method,
            params: params || {}
        };

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, { resolve, reject });

            if (this.process) {
                this.process.stdin?.write(JSON.stringify(request) + '\n');
            } else {
                reject(new Error('Not connected'));
            }

            // Timeout after 30 seconds
            setTimeout(() => {
                if (this.pendingRequests.has(id)) {
                    this.pendingRequests.delete(id);
                    reject(new Error('Request timeout'));
                }
            }, 30000);
        });
    }

    notify(method: string, params?: any): void {
        const notification = {
            jsonrpc: '2.0',
            method,
            params: params || {}
        };

        if (this.process) {
            this.process.stdin?.write(JSON.stringify(notification) + '\n');
        }
    }

    private handleMessage(data: string): void {
        try {
            const message = JSON.parse(data);
            if (message.id !== undefined) {
                // Response
                const pending = this.pendingRequests.get(message.id);
                if (pending) {
                    this.pendingRequests.delete(message.id);
                    if (message.error) {
                        pending.reject(new Error(message.error.message));
                    } else {
                        pending.resolve(message.result);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }

    async listTools(): Promise<any[]> {
        const response = await this.request('tools/list', {});
        return response.tools || [];
    }

    async listResources(): Promise<any[]> {
        const response = await this.request('resources/list', {});
        return response.resources || [];
    }

    async listPrompts(): Promise<any[]> {
        const response = await this.request('prompts/list', {});
        return response.prompts || [];
    }

    disconnect(): void {
        if (this.process) {
            this.process.kill();
            this.process = undefined;
        }
        if (this.websocket) {
            this.websocket.close();
            this.websocket = undefined;
        }
    }

    dispose(): void {
        this.disconnect();
    }
}

