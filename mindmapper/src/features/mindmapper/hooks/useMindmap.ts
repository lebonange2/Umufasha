import { useState, useCallback, useEffect, useRef } from 'react';
import { Mindmap, MindmapNode } from '../types';
import * as api from '../../../lib/api';
import { calculateNodeSize } from '../utils/layout';

export function useMindmap(mindmapId: string | null) {
  const [mindmap, setMindmap] = useState<Mindmap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadMindmap = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMindmap(id);
      setMindmap(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load mindmap');
    } finally {
      setLoading(false);
    }
  }, []);

  const saveMindmap = useCallback(async (debounceMs: number = 2000) => {
    if (!mindmap) return;

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    saveTimeoutRef.current = setTimeout(async () => {
      try {
        await api.updateMindmap(mindmap.id, mindmap.title, mindmap.nodes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to save mindmap');
      }
    }, debounceMs);
  }, [mindmap]);

  const updateNode = useCallback((nodeId: string, updates: Partial<MindmapNode>) => {
    if (!mindmap) return;

    setMindmap({
      ...mindmap,
      nodes: mindmap.nodes.map(node => {
        if (node.id === nodeId) {
          const updated = { ...node, ...updates };
          // Recalculate size if text changed
          if (updates.text !== undefined) {
            const size = calculateNodeSize(updated.text);
            updated.width = size.width;
            updated.height = size.height;
          }
          return updated;
        }
        return node;
      }),
    });
  }, [mindmap]);

  const addNode = useCallback(async (parentId: string | null, x: number, y: number) => {
    if (!mindmap) return;

    try {
      const newNode: Partial<MindmapNode> = {
        parentId,
        x,
        y,
        text: 'New Node',
        color: '#ffffff',
        textColor: '#000000',
        shape: 'rect',
      };
      const size = calculateNodeSize(newNode.text || '');
      newNode.width = size.width;
      newNode.height = size.height;

      const created = await api.createNode(mindmap.id, newNode);
      setMindmap({
        ...mindmap,
        nodes: [...mindmap.nodes, created],
      });
      return created;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create node');
      return null;
    }
  }, [mindmap]);

  const deleteNode = useCallback(async (nodeId: string) => {
    if (!mindmap) return;

    try {
      await api.deleteNode(mindmap.id, nodeId);
      // Also delete children
      const children = mindmap.nodes.filter(n => n.parentId === nodeId);
      for (const child of children) {
        await api.deleteNode(mindmap.id, child.id);
      }
      setMindmap({
        ...mindmap,
        nodes: mindmap.nodes.filter(n => n.id !== nodeId && n.parentId !== nodeId),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete node');
    }
  }, [mindmap]);

  const updateTitle = useCallback((title: string) => {
    if (!mindmap) return;
    setMindmap({ ...mindmap, title });
  }, [mindmap]);

  useEffect(() => {
    if (mindmapId) {
      loadMindmap(mindmapId);
    }
  }, [mindmapId, loadMindmap]);

  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  return {
    mindmap,
    loading,
    error,
    updateNode,
    addNode,
    deleteNode,
    updateTitle,
    saveMindmap,
    loadMindmap,
  };
}

