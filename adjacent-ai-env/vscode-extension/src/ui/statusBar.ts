import * as vscode from 'vscode';
import { McpClient } from '../clients/mcpClient';
import { CwsClient } from '../clients/cwsClient';

export function createStatusBar(mcpClient: McpClient | undefined, cwsClient: CwsClient | undefined): vscode.Disposable {
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'cws.status';
    statusBarItem.text = '$(server) MCP+CWS';
    statusBarItem.tooltip = 'Assistant AI Coding Environment';
    statusBarItem.show();

    // Update status periodically
    const interval = setInterval(async () => {
        const status = [];
        if (mcpClient) {
            try {
                await mcpClient.request('tools/list', {});
                status.push('MCP: ✓');
            } catch {
                status.push('MCP: ✗');
            }
        }
        if (cwsClient) {
            try {
                await cwsClient.request('capabilities', {});
                status.push('CWS: ✓');
            } catch {
                status.push('CWS: ✗');
            }
        }
        statusBarItem.text = `$(server) ${status.join(' ')}`;
    }, 5000);

    return {
        dispose: () => {
            clearInterval(interval);
            statusBarItem.dispose();
        }
    };
}

