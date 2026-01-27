import { useState, useEffect } from 'react';
import { CodingEnvironmentAPI, ServiceStatus } from '../services/api';
import { CWSClient } from '../services/cwsClient';
import FileBrowser from '../components/FileBrowser';
import CodeEditor from '../components/CodeEditor';
import Terminal from '../components/Terminal';
import ServiceStatusPanel from '../components/ServiceStatusPanel';
import ModelSelector from '../components/ModelSelector';
import './CodingEnvironmentPage.css';

export default function CodingEnvironmentPage() {
  const [servicesStatus, setServicesStatus] = useState<{ mcp: ServiceStatus; cws: ServiceStatus } | null>(null);
  const [cwsClient, setCwsClient] = useState<CWSClient | null>(null);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [workspacePath] = useState<string>('.');
  const [selectedModel, setSelectedModel] = useState<string>('llama3:latest');
  const [cwsAutoStartAttempted, setCwsAutoStartAttempted] = useState(false);

  // Auto-start CWS on page load
  useEffect(() => {
    const autoStartCWS = async () => {
      if (cwsAutoStartAttempted) return;
      
      try {
        const status = await CodingEnvironmentAPI.getStatus();
        setServicesStatus(status);
        
        // Auto-start CWS if not running
        if (!status.cws.running) {
          console.log('Auto-starting CWS...');
          try {
            await CodingEnvironmentAPI.startService('cws');
            // Wait a bit for service to start
            await new Promise(resolve => setTimeout(resolve, 3000));
            // Reload status
            const newStatus = await CodingEnvironmentAPI.getStatus();
            setServicesStatus(newStatus);
            
            // Connect to CWS if it started successfully
            if (newStatus.cws.running) {
              const client = new CWSClient();
              try {
                await client.connect();
                setCwsClient(client);
              } catch (error) {
                console.error('Failed to connect to CWS:', error);
              }
            }
          } catch (error) {
            console.error('Failed to auto-start CWS:', error);
          }
        } else {
          // CWS is already running, connect to it
          const client = new CWSClient();
          try {
            await client.connect();
            setCwsClient(client);
          } catch (error) {
            console.error('Failed to connect to CWS:', error);
          }
        }
      } catch (error) {
        console.error('Failed to load service status:', error);
      } finally {
        setCwsAutoStartAttempted(true);
      }
    };

    autoStartCWS();
  }, [cwsAutoStartAttempted]);

  // Load service status periodically
  useEffect(() => {
    const loadStatus = async () => {
      try {
        const status = await CodingEnvironmentAPI.getStatus();
        setServicesStatus(status);
        
        // Connect to CWS if it's running and we're not connected
        if (status.cws.running && !cwsClient) {
          const client = new CWSClient();
          try {
            await client.connect();
            setCwsClient(client);
          } catch (error) {
            console.error('Failed to connect to CWS:', error);
          }
        }
      } catch (error) {
        console.error('Failed to load service status:', error);
      }
    };

    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, [cwsClient]);

  // Load file content when file is selected
  useEffect(() => {
    if (currentFile && cwsClient?.isConnected()) {
      cwsClient.readFile(currentFile)
        .then(content => setFileContent(content))
        .catch(error => {
          console.error('Failed to read file:', error);
          setFileContent(`Error: ${error.message}`);
        });
    }
  }, [currentFile, cwsClient]);

  const handleStartService = async (serviceName: 'mcp' | 'cws') => {
    try {
      await CodingEnvironmentAPI.startService(serviceName);
      // Reload status
      const status = await CodingEnvironmentAPI.getStatus();
      setServicesStatus(status);
      
      // Connect to CWS if it just started
      if (serviceName === 'cws' && status.cws.running && !cwsClient) {
        const client = new CWSClient();
        await client.connect();
        setCwsClient(client);
      }
    } catch (error) {
      console.error(`Failed to start ${serviceName}:`, error);
      alert(`Failed to start ${serviceName}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleStopService = async (serviceName: 'mcp' | 'cws') => {
    try {
      await CodingEnvironmentAPI.stopService(serviceName);
      // Reload status
      const status = await CodingEnvironmentAPI.getStatus();
      setServicesStatus(status);
      
      // Disconnect from CWS if it stopped
      if (serviceName === 'cws' && !status.cws.running && cwsClient) {
        cwsClient.disconnect();
        setCwsClient(null);
      }
    } catch (error) {
      console.error(`Failed to stop ${serviceName}:`, error);
      alert(`Failed to stop ${serviceName}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleFileSelect = (path: string) => {
    setCurrentFile(path);
  };

  const handleSaveFile = async () => {
    if (!currentFile || !cwsClient?.isConnected()) return;
    
    try {
      await cwsClient.writeFile(currentFile, fileContent);
      alert('File saved successfully');
    } catch (error) {
      console.error('Failed to save file:', error);
      alert(`Failed to save file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="coding-environment">
      <div className="header">
        <h1>Coding Environment</h1>
        <div className="header-controls">
          <ModelSelector
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
          />
          <ServiceStatusPanel
            servicesStatus={servicesStatus}
            onStart={handleStartService}
            onStop={handleStopService}
          />
        </div>
      </div>
      
      <div className="main-content">
        <div className="sidebar">
          <FileBrowser
            cwsClient={cwsClient}
            workspacePath={workspacePath}
            onFileSelect={handleFileSelect}
            currentFile={currentFile}
          />
        </div>
        
        <div className="editor-panel">
          <div className="editor-header">
            <span className="file-name">{currentFile || 'No file selected'}</span>
            {currentFile && cwsClient?.isConnected() && (
              <button onClick={handleSaveFile} className="save-button">
                Save
              </button>
            )}
          </div>
          <CodeEditor
            value={fileContent}
            onChange={setFileContent}
            language={currentFile ? getLanguageFromFile(currentFile) : 'plaintext'}
            readOnly={!cwsClient?.isConnected()}
          />
        </div>
        
        <div className="terminal-panel">
          <Terminal cwsClient={cwsClient} />
        </div>
      </div>
    </div>
  );
}

function getLanguageFromFile(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    'ts': 'typescript',
    'tsx': 'typescript',
    'js': 'javascript',
    'jsx': 'javascript',
    'py': 'python',
    'java': 'java',
    'cpp': 'cpp',
    'c': 'c',
    'cs': 'csharp',
    'go': 'go',
    'rs': 'rust',
    'rb': 'ruby',
    'php': 'php',
    'swift': 'swift',
    'kt': 'kotlin',
    'scala': 'scala',
    'sh': 'shell',
    'bash': 'shell',
    'zsh': 'shell',
    'json': 'json',
    'xml': 'xml',
    'html': 'html',
    'css': 'css',
    'scss': 'scss',
    'md': 'markdown',
    'yaml': 'yaml',
    'yml': 'yaml',
    'toml': 'toml',
    'ini': 'ini',
    'conf': 'ini',
    'sql': 'sql',
    'dockerfile': 'dockerfile',
    'makefile': 'makefile',
  };
  return languageMap[ext || ''] || 'plaintext';
}
