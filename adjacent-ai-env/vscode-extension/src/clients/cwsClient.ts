import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as ws from 'ws';

export class CwsClient implements vscode.Disposable {
    private process?: child_process.ChildProcess;
    private websocket?: ws.WebSocket;
    private requestId = 0;
    private pendingRequests = new Map<number, { resolve: (value: any) => void; reject: (error: any) => void }>();

    async connect(): Promise<void> {
        // Connect via stdio
        const config = vscode.workspace.getConfiguration('assistantAiCodingEnv');
        const cwsCommand = config.get<string>('cws.command', 'python3');
        const cwsArgs = config.get<string[]>('cws.args', ['-m', 'cws.main', '--transport', 'stdio']);
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();

        this.process = child_process.spawn(cwsCommand, [...cwsArgs, '--workspace-root', workspaceRoot], {
            cwd: workspaceRoot
        });

        this.process.stdout?.on('data', (data) => {
            this.handleMessage(data.toString());
        });

        this.process.stderr?.on('data', (data) => {
            console.error('CWS stderr:', data.toString());
        });

        // Initialize
        await this.request('initialize', {
            protocolVersion: '1.0.0',
            capabilities: {},
            clientInfo: {
                name: 'vscode-extension',
                version: '1.0.0'
            }
        });
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

    private handleMessage(data: string): void {
        const lines = data.split('\n').filter(line => line.trim());
        for (const line of lines) {
            try {
                const message = JSON.parse(line);
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
    }

    async readFile(path: string): Promise<any> {
        return this.request('fs.read', { path });
    }

    async writeFile(path: string, contents: string, options?: any): Promise<any> {
        return this.request('fs.write', { path, contents, options });
    }

    async search(query: string, options?: any): Promise<any> {
        return this.request('search.find', { query, options });
    }

    async runTask(command: string, args?: string[], options?: any): Promise<any> {
        return this.request('task.run', { command, args, options });
    }

    async runTests(): Promise<any> {
        return this.request('task.test', {});
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

