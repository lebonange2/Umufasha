import { useState, useEffect } from 'react';
import { CWSClient, FileInfo } from '../services/cwsClient';
import './FileBrowser.css';

interface FileBrowserProps {
  cwsClient: CWSClient | null;
  workspacePath: string;
  onFileSelect: (path: string) => void;
  currentFile: string | null;
}

export default function FileBrowser({ cwsClient, workspacePath, onFileSelect, currentFile }: FileBrowserProps) {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [currentPath, setCurrentPath] = useState<string>(workspacePath);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (cwsClient?.isConnected()) {
      loadFiles(currentPath);
    }
  }, [cwsClient, currentPath]);

  const loadFiles = async (path: string) => {
    if (!cwsClient?.isConnected()) return;
    
    setLoading(true);
    try {
      const fileList = await cwsClient.listFiles(path);
      setFiles(fileList);
    } catch (error) {
      console.error('Failed to load files:', error);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = (file: FileInfo) => {
    if (file.type === 'directory') {
      const newPath = file.path;
      setCurrentPath(newPath);
    } else {
      onFileSelect(file.path);
    }
  };

  const handlePathClick = (path: string) => {
    setCurrentPath(path);
  };

  const getPathParts = () => {
    const parts = currentPath.split('/').filter(Boolean);
    return parts.length > 0 ? parts : ['.'];
  };

  return (
    <div className="file-browser">
      <div className="file-browser-header">
        <div className="path-breadcrumb">
          {getPathParts().map((part, index) => {
            const path = '/' + getPathParts().slice(0, index + 1).join('/');
            return (
              <span key={index}>
                <button onClick={() => handlePathClick(path)} className="path-button">
                  {part}
                </button>
                {index < getPathParts().length - 1 && <span className="path-separator">/</span>}
              </span>
            );
          })}
        </div>
      </div>
      
      <div className="file-list">
        {loading ? (
          <div className="loading">Loading...</div>
        ) : files.length === 0 ? (
          <div className="empty">No files</div>
        ) : (
          files.map((file) => (
            <div
              key={file.path}
              className={`file-item ${file.type} ${currentFile === file.path ? 'selected' : ''}`}
              onClick={() => handleFileClick(file)}
            >
              <span className="file-icon">
                {file.type === 'directory' ? '📁' : '📄'}
              </span>
              <span className="file-name">{file.name}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
