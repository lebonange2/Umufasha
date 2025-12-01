import { useState, useMemo, useCallback, useRef } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import {
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { DocumentState, DocNode, NodeKind } from './types';
import { getChildren, getNodePath } from './tree';
import { getTotalWordCount } from './pages';

interface OutlinePanelProps {
  state: DocumentState;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  onMoveNode: (nodeId: string, newParentId: string | null, newOrder: number) => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
}

interface TreeNodeProps {
  node: DocNode;
  state: DocumentState;
  selectedNodeId: string | null;
  onSelect: (nodeId: string) => void;
  depth: number;
  isExpanded: boolean;
  onToggleExpand: (nodeId: string) => void;
  searchQuery?: string;
}

function TreeNodeItem({
  node,
  state,
  selectedNodeId,
  onSelect,
  depth,
  isExpanded,
  onToggleExpand,
  searchQuery,
}: TreeNodeProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: node.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const children = getChildren(state, node.id);
  const hasChildren = children.length > 0;
  const isSelected = selectedNodeId === node.id;
  const wordCount = getTotalWordCount(state, node.id);
  
  const kindIcons: Record<NodeKind, string> = {
    part: '📚',
    chapter: '📖',
    section: '📄',
    subsection: '📝',
    subsubsection: '•',
    paragraph: '¶',
    page: '📃',
    toc: '📑',
  };

  const kindColors: Record<NodeKind, string> = {
    part: 'text-purple-600',
    chapter: 'text-blue-600',
    section: 'text-green-600',
    subsection: 'text-gray-600',
    subsubsection: 'text-gray-500',
    paragraph: 'text-gray-400',
    page: 'text-orange-600',
    toc: 'text-yellow-600',
  };

  // Filter by search query
  const matchesSearch = !searchQuery || 
    (node.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (node.content || '').toLowerCase().includes(searchQuery.toLowerCase());

  if (!matchesSearch && !children.some((c) => 
    (c.title || '').toLowerCase().includes(searchQuery?.toLowerCase() || '') ||
    (c.content || '').toLowerCase().includes(searchQuery?.toLowerCase() || '')
  )) {
    return null;
  }

  // Track mouse down position to distinguish clicks from drags
  const mouseDownPos = useRef<{ x: number; y: number; time: number } | null>(null);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // Only track left mouse button
    if (e.button === 0) {
      mouseDownPos.current = { 
        x: e.clientX, 
        y: e.clientY,
        time: Date.now()
      };
    }
  }, []);

  const handleClick = useCallback((e: React.MouseEvent) => {
    // Don't select if currently dragging
    if (isDragging) {
      return;
    }

    // Don't select if clicking on the expand/collapse button
    const target = e.target as HTMLElement;
    if (target.closest('button[aria-label*="Collapse"], button[aria-label*="Expand"]')) {
      return;
    }

    // Check if this was a drag (mouse moved more than 5px)
    if (mouseDownPos.current) {
      const dx = Math.abs(e.clientX - mouseDownPos.current.x);
      const dy = Math.abs(e.clientY - mouseDownPos.current.y);
      const dt = Date.now() - mouseDownPos.current.time;
      
      // If mouse moved significantly or took too long, it was probably a drag
      if (dx > 5 || dy > 5 || dt > 300) {
        mouseDownPos.current = null;
        return;
      }
    }

    // This is a click - select the node
    e.stopPropagation();
    e.preventDefault();
    
    // Force selection - call immediately
    console.log('Selecting node:', node.id, node.title || 'Untitled');
    onSelect(node.id);
    
    // Also try direct selection as fallback
    setTimeout(() => {
      onSelect(node.id);
    }, 0);
    
    // Reset tracking
    mouseDownPos.current = null;
  }, [isDragging, node.id, node.title, onSelect]);

  // Also handle pointer down for better drag detection
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (e.button === 0) {
      mouseDownPos.current = { 
        x: e.clientX, 
        y: e.clientY,
        time: Date.now()
      };
    }
  }, []);

  return (
    <div
      ref={setNodeRef}
      style={{ ...style, paddingLeft: `${8 + depth * 16}px` }}
      className={`flex items-center gap-1 px-2 py-1 cursor-pointer hover:bg-gray-100 transition-colors ${
        isSelected ? 'bg-blue-50 border-l-2 border-blue-500' : ''
      }`}
      onMouseDown={handleMouseDown}
      onPointerDown={handlePointerDown}
      onClick={handleClick}
    >
      <div
        {...attributes}
        {...listeners}
        data-drag-handle="true"
        className="flex items-center gap-1 flex-1 min-w-0"
        style={{ pointerEvents: 'auto' }}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand(node.id);
            }}
            className="w-4 h-4 flex items-center justify-center text-gray-400 hover:text-gray-600"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        )}
        {!hasChildren && <span className="w-4" />}
        
        <span className={kindColors[node.kind]}>{kindIcons[node.kind]}</span>
        
        {node.number && (
          <span className="text-xs text-gray-500 font-mono">{node.number}</span>
        )}
        
        <span className="truncate flex-1 text-sm">
          {node.title || `Untitled ${node.kind}`}
        </span>
        
        <span className="text-xs text-gray-400">{wordCount}w</span>
      </div>
    </div>
  );
}

export default function OutlinePanel({
  state,
  selectedNodeId,
  onSelectNode,
  onMoveNode,
  searchQuery = '',
  onSearchChange,
}: OutlinePanelProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [collapsed, setCollapsed] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Require 8px movement before drag starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const toggleExpand = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  // Flatten tree for rendering
  const flattenedNodes = useMemo(() => {
    const result: DocNode[] = [];
    
    function traverse(parentId: string | null, depth: number = 0): void {
      const children = getChildren(state, parentId);
      children.forEach((child) => {
        result.push(child);
        if (expandedNodes.has(child.id)) {
          traverse(child.id, depth + 1);
        }
      });
    }
    
    traverse(null);
    return result;
  }, [state, expandedNodes]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (!over || active.id === over.id) {
      return;
    }

    const draggedNode = state.nodes[active.id as string];
    const overNode = state.nodes[over.id as string];
    
    if (!draggedNode || !overNode) {
      return;
    }

    // Determine new parent and order
    let newParentId: string | null = null;
    let newOrder = 0;

    // If dropping on a node, make it a sibling
    if (overNode.kind !== 'paragraph') {
      newParentId = overNode.parentId;
      newOrder = overNode.order;
    } else {
      // Drop on paragraph - make it a child of paragraph's parent
      newParentId = overNode.parentId;
      const siblings = getChildren(state, newParentId);
      newOrder = siblings.length;
    }

    onMoveNode(active.id as string, newParentId, newOrder);
  };

  if (collapsed) {
    return (
      <div className="w-8 border-r bg-gray-50 flex items-center justify-center">
        <button
          onClick={() => setCollapsed(false)}
          className="p-2 hover:bg-gray-200 rounded"
          aria-label="Expand outline"
        >
          ▶
        </button>
      </div>
    );
  }

  return (
    <div className="w-64 border-r bg-white flex flex-col h-full">
      <div className="p-2 border-b flex items-center justify-between">
        <h2 className="font-semibold text-sm">Outline & Structure</h2>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1 hover:bg-gray-100 rounded"
          aria-label="Collapse outline"
        >
          ◀
        </button>
      </div>

      {onSearchChange && (
        <div className="p-2 border-b">
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded"
          />
        </div>
      )}

      <div className="flex-1 overflow-auto">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={flattenedNodes.map((n) => n.id)}
            strategy={verticalListSortingStrategy}
          >
            {flattenedNodes.map((node) => (
              <TreeNodeItem
                key={node.id}
                node={node}
                state={state}
                selectedNodeId={selectedNodeId}
                onSelect={onSelectNode}
                depth={getNodePath(state, node.id).length - 1}
                isExpanded={expandedNodes.has(node.id)}
                onToggleExpand={toggleExpand}
                searchQuery={searchQuery}
              />
            ))}
          </SortableContext>
        </DndContext>
      </div>
    </div>
  );
}

