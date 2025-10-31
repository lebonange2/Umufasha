import * as vscode from 'vscode';
import { McpClient } from '../clients/mcpClient';
import { CwsClient } from '../clients/cwsClient';

export function createTreeViews(mcpClient: McpClient | undefined, cwsClient: CwsClient | undefined): vscode.Disposable[] {
    const disposables: vscode.Disposable[] = [];

    // Workspace tree view
    const workspaceProvider = {
        getChildren: async (element?: any) => {
            if (!cwsClient) {
                return [];
            }
            try {
                const result = await cwsClient.request('fs.list', { path: '.', options: { recursive: false } });
                return result.entries || [];
            } catch (error) {
                return [];
            }
        },
        getTreeItem: (element: any) => {
            const item = new vscode.TreeItem(element.name);
            if (element.type === 'dir') {
                item.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;
                item.iconPath = vscode.ThemeIcon.Folder;
            } else {
                item.collapsibleState = vscode.TreeItemCollapsibleState.None;
                item.iconPath = vscode.ThemeIcon.File;
            }
            return item;
        }
    };

    const workspaceView = vscode.window.createTreeView('cwsWorkspace', {
        treeDataProvider: workspaceProvider
    });
    disposables.push(workspaceView);

    // MCP Tools tree view
    const mcpToolsProvider = {
        getChildren: async () => {
            if (!mcpClient) {
                return [];
            }
            try {
                const tools = await mcpClient.listTools();
                return tools || [];
            } catch (error) {
                return [];
            }
        },
        getTreeItem: (element: any) => {
            const item = new vscode.TreeItem(element.name || element);
            item.description = element.description;
            return item;
        }
    };

    const mcpToolsView = vscode.window.createTreeView('mcpTools', {
        treeDataProvider: mcpToolsProvider
    });
    disposables.push(mcpToolsView);

    return disposables;
}

