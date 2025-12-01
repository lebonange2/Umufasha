import React, { useRef, useEffect, useState, useCallback } from 'react';
import { MindmapNode, ViewState } from '../types';
import Node from './Node';

interface CanvasProps {
  nodes: MindmapNode[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  onUpdateNode: (nodeId: string, updates: Partial<MindmapNode>) => void;
  onDeleteNode: (nodeId: string) => void;
  onAddNode: (parentId: string | null, x: number, y: number) => void;
  viewState: ViewState;
  onViewStateChange: (viewState: ViewState) => void;
}

export default function Canvas({
  nodes,
  selectedNodeId,
  onSelectNode,
  onUpdateNode,
  onDeleteNode,
  onAddNode,
  viewState,
  onViewStateChange,
}: CanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Handle panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0 && !(e.target as HTMLElement).closest('.mindmap-node')) {
      setIsPanning(true);
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      const dx = (e.clientX - panStart.x) / viewState.zoom;
      const dy = (e.clientY - panStart.y) / viewState.zoom;
      onViewStateChange({
        ...viewState,
        x: viewState.x - dx,
        y: viewState.y - dy,
      });
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  }, [isPanning, panStart, viewState, onViewStateChange]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, []);

  // Handle zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.1, Math.min(3, viewState.zoom * delta));
    onViewStateChange({ ...viewState, zoom: newZoom });
  }, [viewState, onViewStateChange]);

  // Handle double-click to add node
  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.mindmap-node')) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = (e.clientX - rect.left - rect.width / 2) / viewState.zoom - viewState.x;
    const y = (e.clientY - rect.top - rect.height / 2) / viewState.zoom - viewState.y;
    
    onAddNode(selectedNodeId, x, y);
  }, [viewState, selectedNodeId, onAddNode]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNodeId) {
          onDeleteNode(selectedNodeId);
          onSelectNode(null);
        }
      } else if (e.key === 'Tab' && selectedNodeId) {
        e.preventDefault();
        const selectedNode = nodes.find(n => n.id === selectedNodeId);
        if (selectedNode) {
          const x = selectedNode.x + 200;
          const y = selectedNode.y;
          onAddNode(selectedNodeId, x, y);
        }
      } else if (e.key === 'Enter' && selectedNodeId && !e.shiftKey) {
        e.preventDefault();
        const selectedNode = nodes.find(n => n.id === selectedNodeId);
        if (selectedNode) {
          const x = selectedNode.x;
          const y = selectedNode.y + 100;
          onAddNode(selectedNode.parentId, x, y);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNodeId, nodes, onDeleteNode, onAddNode, onSelectNode]);

  // Draw connections
  const drawConnections = () => {
    return nodes.map(node => {
      if (!node.parentId) return null;
      
      const parent = nodes.find(n => n.id === node.parentId);
      if (!parent) return null;

      const parentX = (parent.x + viewState.x) * viewState.zoom;
      const parentY = (parent.y + viewState.y) * viewState.zoom;
      const parentW = (parent.width || 100) * viewState.zoom;
      const parentH = (parent.height || 40) * viewState.zoom;
      
      const nodeX = (node.x + viewState.x) * viewState.zoom;
      const nodeY = (node.y + viewState.y) * viewState.zoom;
      const nodeW = (node.width || 100) * viewState.zoom;
      const nodeH = (node.height || 40) * viewState.zoom;

      const canvas = canvasRef.current;
      if (!canvas) return null;

      const rect = canvas.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const x1 = centerX + parentX;
      const y1 = centerY + parentY;
      const x2 = centerX + nodeX;
      const y2 = centerY + nodeY;

      // Calculate connection points
      const dx = x2 - x1;
      const dy = y2 - y1;
      const len = Math.sqrt(dx * dx + dy * dy);
      const unitX = dx / len;
      const unitY = dy / len;

      const startX = x1 + unitX * parentW / 2;
      const startY = y1 + unitY * parentH / 2;
      const endX = x2 - unitX * nodeW / 2;
      const endY = y2 - unitY * nodeH / 2;

      return (
        <line
          key={`connection-${node.id}`}
          x1={startX}
          y1={startY}
          x2={endX}
          y2={endY}
          stroke="#999"
          strokeWidth={2 * viewState.zoom}
          style={{ pointerEvents: 'none' }}
        />
      );
    }).filter(Boolean);
  };

  return (
    <div
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        cursor: isPanning ? 'grabbing' : 'grab',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      onDoubleClick={handleDoubleClick}
    >
      <svg
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
      >
        {drawConnections()}
      </svg>
      {nodes.map(node => (
        <div key={node.id} className="mindmap-node">
          <Node
            node={node}
            selected={node.id === selectedNodeId}
            onSelect={() => onSelectNode(node.id)}
            onUpdate={(updates) => onUpdateNode(node.id, updates)}
            onDelete={() => {
              onDeleteNode(node.id);
              onSelectNode(null);
            }}
            viewX={viewState.x}
            viewY={viewState.y}
            zoom={viewState.zoom}
          />
        </div>
      ))}
    </div>
  );
}

