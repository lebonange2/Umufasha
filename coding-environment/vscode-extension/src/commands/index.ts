import * as vscode from 'vscode';
import { CwsClient } from '../clients/cwsClient';

export function registerCommands(cwsClient: CwsClient | undefined): void {
    // CWS: Open File
    vscode.commands.registerCommand('cws.openFile', async () => {
        if (!cwsClient) {
            vscode.window.showErrorMessage('CWS client not connected');
            return;
        }

        const path = await vscode.window.showInputBox({
            prompt: 'Enter file path',
            placeHolder: 'e.g., src/main.py'
        });

        if (path) {
            try {
                const result = await cwsClient.readFile(path);
                const doc = await vscode.workspace.openTextDocument({
                    content: result.content,
                    language: getLanguageFromPath(path)
                });
                await vscode.window.showTextDocument(doc);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to open file: ${error.message}`);
            }
        }
    });

    // CWS: Write File
    vscode.commands.registerCommand('cws.writeFile', async () => {
        if (!cwsClient) {
            vscode.window.showErrorMessage('CWS client not connected');
            return;
        }

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const path = editor.document.fileName.replace(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '', '');
        const contents = editor.document.getText();

        try {
            await cwsClient.writeFile(path, contents, { atomic: true });
            vscode.window.showInformationMessage(`File saved via CWS: ${path}`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to write file: ${error.message}`);
        }
    });

    // CWS: Search
    vscode.commands.registerCommand('cws.search', async () => {
        if (!cwsClient) {
            vscode.window.showErrorMessage('CWS client not connected');
            return;
        }

        const query = await vscode.window.showInputBox({
            prompt: 'Enter search query',
            placeHolder: 'e.g., function'
        });

        if (query) {
            try {
                const result = await cwsClient.search(query, { maxResults: 100 });
                vscode.window.showInformationMessage(`Found ${result.count} results`);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Search failed: ${error.message}`);
            }
        }
    });

    // CWS: Run Task
    vscode.commands.registerCommand('cws.runTask', async () => {
        if (!cwsClient) {
            vscode.window.showErrorMessage('CWS client not connected');
            return;
        }

        const command = await vscode.window.showInputBox({
            prompt: 'Enter command',
            placeHolder: 'e.g., python3'
        });

        if (command) {
            const confirmed = await vscode.window.showWarningMessage(
                `Run command: ${command}?`,
                'Yes',
                'No'
            );

            if (confirmed === 'Yes') {
                try {
                    const result = await cwsClient.runTask(command, [], { confirmed: true });
                    vscode.window.showInformationMessage(`Task completed with exit code: ${result.exitCode}`);
                } catch (error: any) {
                    vscode.window.showErrorMessage(`Task failed: ${error.message}`);
                }
            }
        }
    });

    // CWS: Run Tests
    vscode.commands.registerCommand('cws.runTests', async () => {
        if (!cwsClient) {
            vscode.window.showErrorMessage('CWS client not connected');
            return;
        }

        try {
            const result = await cwsClient.runTests();
            vscode.window.showInformationMessage(`Tests completed with exit code: ${result.exitCode}`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Tests failed: ${error.message}`);
        }
    });
}

function getLanguageFromPath(path: string): string {
    const ext = path.split('.').pop()?.toLowerCase();
    const languageMap: { [key: string]: string } = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'json': 'json',
        'md': 'markdown'
    };
    return languageMap[ext || ''] || 'plaintext';
}

