import * as vscode from 'vscode';
import { McpClient } from './clients/mcpClient';
import { CwsClient } from './clients/cwsClient';
import { createStatusBar } from './ui/statusBar';
import { createTreeViews } from './ui/treeViews';
import { registerCommands } from './commands';

let mcpClient: McpClient | undefined;
let cwsClient: CwsClient | undefined;

export async function activate(context: vscode.ExtensionContext) {
    console.log('Assistant AI Coding Environment extension activated');

    // Create clients
    mcpClient = new McpClient();
    cwsClient = new CwsClient();

    // Connect to MCP server
    try {
        await mcpClient.connect();
        console.log('Connected to MCP server');
    } catch (error) {
        console.error('Failed to connect to MCP server:', error);
    }

    // Connect to CWS
    try {
        await cwsClient.connect();
        console.log('Connected to CWS');
    } catch (error) {
        console.error('Failed to connect to CWS:', error);
    }

    // Create UI
    const statusBar = createStatusBar(mcpClient, cwsClient);
    const treeViews = createTreeViews(mcpClient, cwsClient);

    // Register commands
    registerCommands(cwsClient);

    // Add to subscriptions
    context.subscriptions.push(statusBar);
    context.subscriptions.push(...treeViews);
    context.subscriptions.push(mcpClient);
    context.subscriptions.push(cwsClient);

    return {
        mcpClient,
        cwsClient
    };
}

export function deactivate() {
    if (mcpClient) {
        mcpClient.disconnect();
    }
    if (cwsClient) {
        cwsClient.disconnect();
    }
}

