import { useMemo, useState, useEffect } from 'react';
import { CWSClient, FileInfo } from '../services/cwsClient';
import './FileBrowser.css';

interface FileBrowserProps {
  cwsClient: CWSClient | null;
  workspacePath: string;
  onFileSelect: (path: string) => void;
  currentFile: string | null;
  refreshToken?: number;
}

type NodeChildren = Record<string, FileInfo[]>;

export default function FileBrowser({ cwsClient, workspacePath, onFileSelect, currentFile, refreshToken = 0 }: FileBrowserProps) {
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(['.']));
  const [children, setChildren] = useState<NodeChildren>({});
  const [loadingDirs, setLoadingDirs] = useState<Set<string>>(() => new Set());
  const [selectedDir, setSelectedDir] = useState<string>('.');

  useEffect(() => {
    if (!cwsClient?.isConnected()) return;
    // Initial load / refresh: load root and expanded dirs
    void refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cwsClient, refreshToken]);

  const sorted = (list: FileInfo[]) =>
    [...list].sort((a, b) => {
      if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

  const loadDir = async (path: string) => {
    if (!cwsClient?.isConnected()) return;
    setLoadingDirs((prev) => new Set(prev).add(path));
    try {
      const fileList = await cwsClient.listFiles(path);
      setChildren((prev) => ({ ...prev, [path]: sorted(fileList) }));
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setLoadingDirs((prev) => {
        const next = new Set(prev);
        next.delete(path);
        return next;
      });
    }
  };

  const refreshAll = async () => {
    // Always ensure root loaded
    await loadDir('.');
    // Reload expanded dirs (best-effort)
    for (const dir of expanded) {
      if (dir !== '.') await loadDir(dir);
    }
  };

  const toggleDir = async (dirPath: string) => {
    setSelectedDir(dirPath);
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(dirPath)) next.delete(dirPath);
      else next.add(dirPath);
      return next;
    });
    if (!children[dirPath]) await loadDir(dirPath);
  };

  const createNewFile = async () => {
    if (!cwsClient?.isConnected()) return;
    const name = window.prompt('New file name (relative to selected folder):');
    if (!name) return;
    const target = selectedDir === '.' ? name : `${selectedDir}/${name}`;
    try {
      await cwsClient.createFile(target);
      await cwsClient.writeFile(target, '');
      await refreshAll();
      onFileSelect(target);
    } catch (e: any) {
      alert(`Failed to create file: ${e?.message || 'Unknown error'}`);
    }
  };

  const createNewFolder = async () => {
    if (!cwsClient?.isConnected()) return;
    const name = window.prompt('New folder name (relative to selected folder):');
    if (!name) return;
    const target = selectedDir === '.' ? name : `${selectedDir}/${name}`;
    try {
      await cwsClient.createFolder(target);
      // Expand and refresh
      setExpanded((prev) => new Set(prev).add(target));
      await refreshAll();
    } catch (e: any) {
      alert(`Failed to create folder: ${e?.message || 'Unknown error'}`);
    }
  };

  const rootLabel = useMemo(() => workspacePath === '.' ? 'Workspace' : workspacePath, [workspacePath]);

  const renderTree = (dirPath: string, depth: number) => {
    const list = children[dirPath] || [];
    if (!expanded.has(dirPath)) return null;
    return list.map((entry) => {
      const isDir = entry.type === 'directory';
      const isOpen = expanded.has(entry.path);
      const isLoading = loadingDirs.has(entry.path);
      return (
        <div key={entry.path}>
          <div
            className={`tree-item ${isDir ? 'directory' : 'file'} ${currentFile === entry.path ? 'selected' : ''} ${selectedDir === entry.path ? 'active-dir' : ''}`}
            style={{ paddingLeft: `${8 + depth * 14}px` }}
            onClick={() => {
              if (isDir) void toggleDir(entry.path);
              else onFileSelect(entry.path);
            }}
          >
            <span className="tree-twisty">{isDir ? (isOpen ? '▾' : '▸') : ''}</span>
            <span className="file-icon">{isDir ? '📁' : '📄'}</span>
            <span className="file-name">{entry.name}</span>
            {isDir && isLoading && <span className="tree-loading">…</span>}
          </div>
          {isDir && renderTree(entry.path, depth + 1)}
        </div>
      );
    });
  };

  return (
    <div className="file-browser">
      <div className="file-browser-header">
        <div className="file-browser-toolbar">
          <div className="file-browser-title">{rootLabel}</div>
          <div className="file-browser-actions">
            <button className="fb-btn" onClick={() => void refreshAll()} disabled={!cwsClient?.isConnected()}>
              Refresh
            </button>
            <button className="fb-btn" onClick={() => void createNewFile()} disabled={!cwsClient?.isConnected()}>
              New File
            </button>
            <button className="fb-btn" onClick={() => void createNewFolder()} disabled={!cwsClient?.isConnected()}>
              New Folder
            </button>
          </div>
        </div>
      </div>
      
      <div className="file-list">
        {!cwsClient?.isConnected() ? (
          <div className="empty">CWS not connected</div>
        ) : (children['.'] || []).length === 0 && loadingDirs.has('.') ? (
          <div className="loading">Loading...</div>
        ) : (children['.'] || []).length === 0 ? (
          <div className="empty">No files</div>
        ) : (
          <div>
            <div
              className={`tree-item directory root ${selectedDir === '.' ? 'active-dir' : ''}`}
              style={{ paddingLeft: '8px' }}
              onClick={() => void toggleDir('.')}
            >
              <span className="tree-twisty">{expanded.has('.') ? '▾' : '▸'}</span>
              <span className="file-icon">📁</span>
              <span className="file-name">.</span>
              {loadingDirs.has('.') && <span className="tree-loading">…</span>}
            </div>
            {renderTree('.', 1)}
          </div>
        )
        }
      </div>
    </div>
  );
}
