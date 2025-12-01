import React, { useState, useEffect } from 'react';
import { MindmapListItem } from '../types';
import * as api from '../../../lib/api';

interface SidebarProps {
  currentMindmapId: string | null;
  onSelectMindmap: (id: string) => void;
  onNewMindmap: () => void;
}

export default function Sidebar({ currentMindmapId, onSelectMindmap, onNewMindmap }: SidebarProps) {
  const [mindmaps, setMindmaps] = useState<MindmapListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMindmaps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listMindmaps();
      setMindmaps(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load mindmaps');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMindmaps();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this mind map?')) return;

    try {
      await api.deleteMindmap(id);
      await loadMindmaps();
      if (currentMindmapId === id) {
        onNewMindmap();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete mindmap');
    }
  };

  return (
    <div
      style={{
        width: '250px',
        backgroundColor: '#f8f9fa',
        borderRight: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>Mind Maps</h3>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {loading && <div style={{ padding: '16px', textAlign: 'center', color: '#666' }}>Loading...</div>}
        {error && <div style={{ padding: '16px', color: '#d32f2f' }}>{error}</div>}

        {!loading && !error && mindmaps.length === 0 && (
          <div style={{ padding: '16px', textAlign: 'center', color: '#666' }}>
            No mind maps yet. Create one to get started!
          </div>
        )}

        {mindmaps.map((mindmap) => (
          <div
            key={mindmap.id}
            onClick={() => onSelectMindmap(mindmap.id)}
            style={{
              padding: '12px',
              marginBottom: '8px',
              backgroundColor: currentMindmapId === mindmap.id ? '#e3f2fd' : '#fff',
              border: currentMindmapId === mindmap.id ? '2px solid #4facfe' : '1px solid #e0e0e0',
              borderRadius: '6px',
              cursor: 'pointer',
              position: 'relative',
            }}
            onMouseEnter={(e) => {
              if (currentMindmapId !== mindmap.id) {
                (e.currentTarget as HTMLElement).style.backgroundColor = '#f5f5f5';
              }
            }}
            onMouseLeave={(e) => {
              if (currentMindmapId !== mindmap.id) {
                (e.currentTarget as HTMLElement).style.backgroundColor = '#fff';
              }
            }}
          >
            <div style={{ fontWeight: '500', marginBottom: '4px' }}>{mindmap.title}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {mindmap.node_count} nodes • {new Date(mindmap.updated_at).toLocaleDateString()}
            </div>
            <button
              onClick={(e) => handleDelete(mindmap.id, e)}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                padding: '4px 8px',
                backgroundColor: '#ff5252',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                opacity: 0.7,
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.opacity = '1';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.opacity = '0.7';
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid #e0e0e0' }}>
        <button
          onClick={onNewMindmap}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: '#4facfe',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
          }}
        >
          + New Mind Map
        </button>
      </div>
    </div>
  );
}

