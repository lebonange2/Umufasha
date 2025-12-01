import { useState, useEffect, useRef, useCallback } from 'react';
import { useMindmap } from '../features/mindmapper/hooks/useMindmap';
import { ViewState } from '../features/mindmapper/types';
import Canvas from '../features/mindmapper/components/Canvas';
import Toolbar from '../features/mindmapper/components/Toolbar';
import Sidebar from '../features/mindmapper/components/Sidebar';
import Inspector from '../features/mindmapper/components/Inspector';
import * as api from '../lib/api';
import { downloadJSON, exportAsSVG, exportAsPNG } from '../features/mindmapper/utils/export';
import { calculateRadialLayout } from '../features/mindmapper/utils/layout';

export default function MindmapperPage() {
  const [currentMindmapId, setCurrentMindmapId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [viewState, setViewState] = useState<ViewState>({ x: 0, y: 0, zoom: 1 });
  const [saving, setSaving] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  const {
    mindmap,
    loading,
    error,
    updateNode,
    addNode,
    deleteNode,
    updateTitle,
    saveMindmap,
  } = useMindmap(currentMindmapId);

  // Auto-save when mindmap changes
  useEffect(() => {
    if (mindmap && currentMindmapId) {
      setSaving(true);
      saveMindmap(2000);
      const timeout = setTimeout(() => setSaving(false), 2500);
      return () => clearTimeout(timeout);
    }
  }, [mindmap, currentMindmapId, saveMindmap]);

  // Center view on load
  useEffect(() => {
    if (mindmap && mindmap.nodes.length > 0) {
      const root = mindmap.nodes.find(n => n.parentId === null);
      if (root) {
        setViewState({ x: -root.x, y: -root.y, zoom: 1 });
      }
    }
  }, [mindmap?.id]);

  const handleNewMindmap = useCallback(async () => {
    try {
      const newMindmap = await api.createMindmap('Untitled Mind Map');
      setCurrentMindmapId(newMindmap.id);
      setSelectedNodeId(null);
      setViewState({ x: 0, y: 0, zoom: 1 });
    } catch (err) {
      console.error('Failed to create mindmap:', err);
    }
  }, []);

  // Auto-create a mindmap on first load if none exists
  useEffect(() => {
    if (!currentMindmapId && !loading && !mindmap) {
      handleNewMindmap();
    }
  }, [currentMindmapId, loading, mindmap, handleNewMindmap]);

  const handleSelectMindmap = useCallback((id: string) => {
    setCurrentMindmapId(id);
    setSelectedNodeId(null);
  }, []);

  const handleDuplicate = useCallback(async () => {
    if (!mindmap) return;
    try {
      const duplicated = await api.createMindmap(`${mindmap.title} (Copy)`, mindmap.nodes);
      setCurrentMindmapId(duplicated.id);
      setSelectedNodeId(null);
    } catch (err) {
      console.error('Failed to duplicate mindmap:', err);
    }
  }, [mindmap]);

  const handleExportJSON = useCallback(() => {
    if (!mindmap) return;
    downloadJSON(mindmap);
  }, [mindmap]);

  const handleExportSVG = useCallback(() => {
    if (!mindmap || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    exportAsSVG(mindmap.nodes, rect.width, rect.height, `${mindmap.title}.svg`);
  }, [mindmap]);

  const handleExportPNG = useCallback(() => {
    if (!mindmap || !canvasRef.current) return;
    const canvas = document.createElement('canvas');
    const rect = canvasRef.current.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw background
    ctx.fillStyle = '#f5f7fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw connections
    ctx.strokeStyle = '#999';
    ctx.lineWidth = 2;
    mindmap.nodes.forEach(node => {
      if (node.parentId) {
        const parent = mindmap.nodes.find(n => n.id === node.parentId);
        if (parent) {
          const parentX = (parent.x + viewState.x) * viewState.zoom + rect.width / 2;
          const parentY = (parent.y + viewState.y) * viewState.zoom + rect.height / 2;
          const nodeX = (node.x + viewState.x) * viewState.zoom + rect.width / 2;
          const nodeY = (node.y + viewState.y) * viewState.zoom + rect.height / 2;
          ctx.beginPath();
          ctx.moveTo(parentX, parentY);
          ctx.lineTo(nodeX, nodeY);
          ctx.stroke();
        }
      }
    });

    // Draw nodes
    mindmap.nodes.forEach(node => {
      const w = (node.width || 100) * viewState.zoom;
      const h = (node.height || 40) * viewState.zoom;
      const x = (node.x + viewState.x) * viewState.zoom + rect.width / 2 - w / 2;
      const y = (node.y + viewState.y) * viewState.zoom + rect.height / 2 - h / 2;

      ctx.fillStyle = node.color;
      if (node.shape === 'pill') {
        ctx.beginPath();
        const radius = h / 2;
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + w - radius, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
        ctx.lineTo(x + w, y + h - radius);
        ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
        ctx.lineTo(x + radius, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
        ctx.fill();
      } else {
        ctx.beginPath();
        const radius = 8;
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + w - radius, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
        ctx.lineTo(x + w, y + h - radius);
        ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
        ctx.lineTo(x + radius, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
        ctx.fill();
      }

      ctx.fillStyle = node.textColor;
      ctx.font = `${14 * viewState.zoom}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.text, x + w / 2, y + h / 2);
    });

    exportAsPNG(canvas, `${mindmap.title}.png`);
  }, [mindmap, viewState]);

  const handleAddNode = useCallback(async (parentId: string | null, x: number, y: number) => {
    if (!mindmap) return;
    const newNode = await addNode(parentId, x, y);
    if (newNode) {
      setSelectedNodeId(newNode.id);
    }
  }, [mindmap, addNode]);

  const handleAddChild = useCallback(() => {
    if (!mindmap || !selectedNodeId) return;
    const selectedNode = mindmap.nodes.find(n => n.id === selectedNodeId);
    if (selectedNode) {
      handleAddNode(selectedNodeId, selectedNode.x + 200, selectedNode.y);
    }
  }, [mindmap, selectedNodeId, handleAddNode]);

  const handleAddSibling = useCallback(() => {
    if (!mindmap || !selectedNodeId) return;
    const selectedNode = mindmap.nodes.find(n => n.id === selectedNodeId);
    if (selectedNode) {
      handleAddNode(selectedNode.parentId, selectedNode.x, selectedNode.y + 100);
    }
  }, [mindmap, selectedNodeId, handleAddNode]);

  const handleAutoLayout = useCallback(() => {
    if (!mindmap) return;
    const root = mindmap.nodes.find(n => n.parentId === null);
    if (!root) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const centerX = rect.width / 2 / viewState.zoom - viewState.x;
    const centerY = rect.height / 2 / viewState.zoom - viewState.y;

    const updatedNodes = calculateRadialLayout(mindmap.nodes, centerX, centerY);
    
    // Update all nodes
    updatedNodes.forEach(node => {
      updateNode(node.id, { x: node.x, y: node.y });
    });
  }, [mindmap, viewState, updateNode]);

  const selectedNode = mindmap?.nodes.find(n => n.id === selectedNodeId) || null;

  if (loading && !mindmap) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (error && !mindmap) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: '16px' }}>
        <div style={{ color: '#d32f2f' }}>{error}</div>
        <button onClick={handleNewMindmap} style={{ padding: '8px 16px', backgroundColor: '#4facfe', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          Create New Mind Map
        </button>
      </div>
    );
  }

  if (!mindmap) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: '16px' }}>
        <h2>No mind map selected</h2>
        <button onClick={handleNewMindmap} style={{ padding: '12px 24px', backgroundColor: '#4facfe', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '16px' }}>
          Create New Mind Map
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Toolbar
        mindmap={mindmap}
        onNew={handleNewMindmap}
        onDuplicate={handleDuplicate}
        onExportJSON={handleExportJSON}
        onExportSVG={handleExportSVG}
        onExportPNG={handleExportPNG}
        onTitleChange={updateTitle}
        saving={saving}
      />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar
          currentMindmapId={currentMindmapId}
          onSelectMindmap={handleSelectMindmap}
          onNewMindmap={handleNewMindmap}
        />

        <div ref={canvasRef} style={{ flex: 1, position: 'relative' }}>
          <Canvas
            nodes={mindmap.nodes}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
            onUpdateNode={(nodeId, updates) => updateNode(nodeId, updates)}
            onDeleteNode={(nodeId) => {
              deleteNode(nodeId);
              setSelectedNodeId(null);
            }}
            onAddNode={handleAddNode}
            viewState={viewState}
            onViewStateChange={setViewState}
          />

          <div style={{ position: 'absolute', bottom: '16px', right: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              onClick={() => {
                const root = mindmap.nodes.find(n => n.parentId === null);
                if (root) {
                  setViewState({ x: -root.x, y: -root.y, zoom: 1 });
                }
              }}
              style={{
                padding: '10px',
                backgroundColor: '#fff',
                border: '1px solid #ddd',
                borderRadius: '6px',
                cursor: 'pointer',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
              title="Center view"
            >
              🎯
            </button>
            <button
              onClick={handleAutoLayout}
              style={{
                padding: '10px',
                backgroundColor: '#fff',
                border: '1px solid #ddd',
                borderRadius: '6px',
                cursor: 'pointer',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
              title="Auto layout"
            >
              📐
            </button>
            <div style={{ padding: '8px', backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px', fontSize: '12px', textAlign: 'center' }}>
              {Math.round(viewState.zoom * 100)}%
            </div>
          </div>
        </div>

        <Inspector
          node={selectedNode}
          onUpdate={(updates) => selectedNodeId && updateNode(selectedNodeId, updates)}
          onAddChild={handleAddChild}
          onAddSibling={handleAddSibling}
          onDelete={() => {
            if (selectedNodeId) {
              deleteNode(selectedNodeId);
              setSelectedNodeId(null);
            }
          }}
        />
      </div>
    </div>
  );
}

