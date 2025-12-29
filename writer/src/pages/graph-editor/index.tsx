import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// @ts-ignore - 3d-force-graph doesn't have perfect TypeScript support
import ForceGraph3D from '3d-force-graph';

interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
  x?: number;
  y?: number;
  z?: number;
}

interface GraphEdge {
  id: string;
  type: string;
  from: string;
  to: string;
  properties: Record<string, any>;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const NODE_COLORS: Record<string, number> = {
  Project: 0x888888,
  Character: 0xff6b6b,
  Location: 0x4ecdc4,
  Environment: 0x45b7d1,
  Faction: 0xf9ca24,
  Artifact: 0x6c5ce7,
  Concept: 0xa29bfe,
  Rule: 0xfd79a8,
  Theme: 0xfdcb6e,
  Chapter: 0x00b894,
  Scene: 0x00cec9,
  Event: 0xe17055,
  Issue: 0xd63031,
  Source: 0x74b9ff,
};

export default function GraphEditorPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectMode, setConnectMode] = useState(false);
  const [sourceNode, setSourceNode] = useState<GraphNode | null>(null);
  const [filters, setFilters] = useState({
    labels: [] as string[],
    stage: '',
    chapter: null as number | null,
  });
  const [schema, setSchema] = useState<any>(null);
  const [validationIssues, setValidationIssues] = useState<any[]>([]);
  const [showCreateNode, setShowCreateNode] = useState(false);

  // Initialize graph
  useEffect(() => {
    if (!containerRef.current || !projectId) return;

    // @ts-ignore - 3d-force-graph typing issue
    const Graph = ForceGraph3D()(containerRef.current)
      .nodeLabel((node: any) => {
        const props = node.properties || {};
        return props.name || props.title || node.id;
      })
      .nodeColor((node: any) => {
        const labels = node.labels || [];
        for (const label of labels) {
          if (NODE_COLORS[label]) {
            return NODE_COLORS[label];
          }
        }
        return 0x888888;
      })
      .nodeOpacity(0.9)
      .linkColor(() => 0xaaaaaa)
      .linkWidth(2)
      .linkDirectionalArrowLength(6)
      .linkDirectionalArrowRelPos(1)
      .linkCurvature(0.25)
      .onNodeClick((node: any) => {
        if (connectMode) {
          if (!sourceNode) {
            // First click - set source
            setSourceNode(node);
          } else if (sourceNode.id !== node.id) {
            // Second click - create relationship
            handleCreateRelationship(sourceNode.id, node.id);
            setSourceNode(null);
          } else {
            // Clicked same node - cancel
            setSourceNode(null);
          }
        } else {
          setSelectedNode(node);
        }
      })
      .onNodeDrag((node: any) => {
        // Update node position
        node.fx = node.x;
        node.fy = node.y;
        node.fz = node.z;
      })
      .onNodeDragEnd((node: any) => {
        // Release fixed position
        node.fx = null;
        node.fy = null;
        node.fz = null;
      });

    graphRef.current = Graph;

    // Load initial data
    loadGraph();
    loadSchema();

    return () => {
      Graph._destructor();
    };
  }, [projectId]);

  const loadGraph = async () => {
    if (!projectId) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.stage) params.append('stage', filters.stage);
      if (filters.chapter) params.append('chapter', filters.chapter.toString());
      if (filters.labels.length > 0) params.append('labels', filters.labels.join(','));
      
      const url = `/api/projects/${projectId}/graph?${params.toString()}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Failed to load graph');
      }
      
      const data = await response.json();
      setGraphData(data);
      
      if (graphRef.current) {
        graphRef.current.graphData(data);
      }
    } catch (err: any) {
      setError(err.message);
      console.error('Failed to load graph:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSchema = async () => {
    if (!projectId) return;
    
    try {
      const response = await fetch(`/api/projects/${projectId}/schema`);
      if (response.ok) {
        const data = await response.json();
        setSchema(data);
      }
    } catch (err) {
      console.error('Failed to load schema:', err);
    }
  };

  const handleCreateNode = async (labels: string[], properties: Record<string, any>) => {
    if (!projectId) return;
    
    try {
      const response = await fetch(`/api/projects/${projectId}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ labels, properties }),
      });
      
      if (response.ok) {
        await loadGraph();
      } else {
        throw new Error('Failed to create node');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleUpdateNode = async (nodeId: string, properties: Record<string, any>) => {
    if (!projectId) return;
    
    try {
      const response = await fetch(`/api/projects/${projectId}/nodes/${nodeId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ properties }),
      });
      
      if (response.ok) {
        await loadGraph();
        if (selectedNode?.id === nodeId) {
          // Refresh selected node
          const updated = graphData.nodes.find(n => n.id === nodeId);
          if (updated) setSelectedNode(updated);
        }
      } else {
        throw new Error('Failed to update node');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteNode = async (nodeId: string) => {
    if (!projectId || !confirm('Delete this node?')) return;
    
    try {
      const response = await fetch(`/api/projects/${projectId}/nodes/${nodeId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        await loadGraph();
        if (selectedNode?.id === nodeId) {
          setSelectedNode(null);
        }
      } else {
        throw new Error('Failed to delete node');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const [showRelTypeSelector, setShowRelTypeSelector] = useState(false);
  const [pendingRel, setPendingRel] = useState<{source: string, target: string} | null>(null);

  const handleCreateRelationship = async (sourceId: string, targetId: string, relType?: string) => {
    if (!projectId) return;
    
    if (!relType) {
      // Show relationship type selector
      setPendingRel({ source: sourceId, target: targetId });
      setShowRelTypeSelector(true);
      return;
    }
    
    try {
      const response = await fetch(`/api/projects/${projectId}/relationships`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: sourceId,
          target_id: targetId,
          rel_type: relType,
        }),
      });
      
      if (response.ok) {
        await loadGraph();
        setShowRelTypeSelector(false);
        setPendingRel(null);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create relationship');
      }
    } catch (err: any) {
      setError(err.message);
      setShowRelTypeSelector(false);
      setPendingRel(null);
    }
  };

  const handleValidate = async () => {
    if (!projectId) return;
    
    try {
      const response = await fetch(`/api/projects/${projectId}/validate`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setValidationIssues(data.issues || []);
      }
    } catch (err) {
      console.error('Failed to validate:', err);
    }
  };

  const handleRender = async () => {
    if (!projectId) return;
    
    try {
      const response = await fetch(`/api/projects/${projectId}/render`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        // Download markdown
        const blob = new Blob([data.markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${data.title || 'book'}.md`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to render:', err);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [filters]);

  if (loading && graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading graph...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Toolbar */}
      <div className="bg-gray-800 text-white p-4 flex items-center gap-4">
        <button
          onClick={() => {
            // Navigate back to Book Publishing House page
            // The basename is /writer, so /ferrari-company resolves to /writer/ferrari-company
            navigate('/ferrari-company');
          }}
          className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600 flex items-center gap-2"
          title="Back to Book Publishing House"
        >
          ← Back to Book Publishing House
        </button>
        
        <div className="flex-1" />
        
        <button
          onClick={() => setShowCreateNode(true)}
          className="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
        >
          + Create Node
        </button>
        
        <button
          onClick={() => {
            setConnectMode(!connectMode);
            setSourceNode(null);
          }}
          className={`px-4 py-2 rounded ${connectMode ? 'bg-blue-600' : 'bg-gray-700'} hover:bg-blue-700`}
        >
          {connectMode ? `Cancel Connect${sourceNode ? ' (Source Selected)' : ''}` : 'Connect Mode'}
        </button>
        
        <button
          onClick={handleValidate}
          className="px-4 py-2 bg-yellow-600 rounded hover:bg-yellow-700"
        >
          Validate
        </button>
        
        <button
          onClick={handleRender}
          className="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
        >
          Render Book
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Graph canvas */}
        <div ref={containerRef} className="flex-1" />
        
        {/* Side panel */}
        <div className="w-96 bg-gray-800 text-white overflow-y-auto">
          {showCreateNode ? (
            <NodeCreator
              schema={schema}
              onCreate={(labels, properties) => {
                handleCreateNode(labels, properties);
                setShowCreateNode(false);
              }}
              onCancel={() => {
                setShowCreateNode(false);
              }}
            />
          ) : selectedNode ? (
            <NodeInspector
              node={selectedNode}
              schema={schema}
              onUpdate={handleUpdateNode}
              onDelete={handleDeleteNode}
              onClose={() => setSelectedNode(null)}
            />
          ) : (
            <div className="p-4">
              <h2 className="text-xl font-bold mb-4">Graph Editor</h2>
              <p className="text-gray-400 mb-4">
                Click a node to inspect and edit it.
              </p>
              
              {/* Filters */}
              <div className="mb-4">
                <h3 className="font-semibold mb-2">Filters</h3>
                <div className="space-y-2">
                  <select
                    value={filters.stage}
                    onChange={(e) => setFilters({ ...filters, stage: e.target.value })}
                    className="w-full p-2 bg-gray-700 rounded text-white"
                  >
                    <option value="">All Stages</option>
                    <option value="idea">Idea</option>
                    <option value="outline">Outline</option>
                    <option value="draft">Draft</option>
                    <option value="revise">Revise</option>
                    <option value="final">Final</option>
                  </select>
                </div>
              </div>
              
              {/* Validation Issues */}
              {validationIssues.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-semibold mb-2 text-yellow-400">Issues</h3>
                  <div className="space-y-2">
                    {validationIssues.map((issue, idx) => (
                      <div key={idx} className="p-2 bg-gray-700 rounded text-sm">
                        <div className="font-semibold text-red-400">{issue.severity}: {issue.type}</div>
                        <div className="text-gray-300">{issue.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {error && (
        <div className="bg-red-600 text-white p-4">
          {error}
          <button onClick={() => setError(null)} className="ml-4">×</button>
        </div>
      )}
      
      {showRelTypeSelector && pendingRel && schema && (
        <RelationshipTypeSelector
          schema={schema}
          sourceNode={graphData.nodes.find(n => n.id === pendingRel.source)}
          targetNode={graphData.nodes.find(n => n.id === pendingRel.target)}
          onSelect={(relType) => {
            handleCreateRelationship(pendingRel.source, pendingRel.target, relType);
          }}
          onCancel={() => {
            setShowRelTypeSelector(false);
            setPendingRel(null);
            setConnectMode(false);
            setSourceNode(null);
          }}
        />
      )}
    </div>
  );
}

interface RelationshipTypeSelectorProps {
  schema: any;
  sourceNode?: GraphNode;
  targetNode?: GraphNode;
  onSelect: (relType: string) => void;
  onCancel: () => void;
}

function RelationshipTypeSelector({ schema, sourceNode, targetNode, onSelect, onCancel }: RelationshipTypeSelectorProps) {
  // schema is used in getAllowedTypes function below
  const [selectedType, setSelectedType] = useState('');
  
  // Get allowed relationship types based on source and target labels
  const getAllowedTypes = (): string[] => {
    if (!sourceNode || !targetNode || !schema?.allowed_relationships) {
      return schema?.relationship_types || [];
    }
    
    const sourceLabels = sourceNode.labels || [];
    const targetLabels = targetNode.labels || [];
    
    const allowed: string[] = [];
    for (const sourceLabel of sourceLabels) {
      const rels = schema.allowed_relationships[sourceLabel] || {};
      for (const [relType, targetLabelsList] of Object.entries(rels)) {
        if (Array.isArray(targetLabelsList) && targetLabelsList.some(tl => targetLabels.includes(tl))) {
          if (!allowed.includes(relType)) {
            allowed.push(relType);
          }
        }
      }
    }
    
    return allowed.length > 0 ? allowed : schema.relationship_types || [];
  };
  
  const allowedTypes = getAllowedTypes();
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 text-white p-6 rounded-lg max-w-md w-full">
        <h3 className="text-xl font-bold mb-4">Select Relationship Type</h3>
        <div className="mb-4">
          <div className="text-sm text-gray-400">
            From: <strong>{sourceNode?.properties?.name || sourceNode?.properties?.title || sourceNode?.id}</strong>
          </div>
          <div className="text-sm text-gray-400">
            To: <strong>{targetNode?.properties?.name || targetNode?.properties?.title || targetNode?.id}</strong>
          </div>
        </div>
        <div className="mb-4 max-h-64 overflow-y-auto">
          {allowedTypes.length === 0 ? (
            <p className="text-yellow-400">No allowed relationship types for these node types</p>
          ) : (
            <div className="space-y-2">
              {allowedTypes.map((relType) => (
                <label key={relType} className="flex items-center p-2 hover:bg-gray-700 rounded cursor-pointer">
                  <input
                    type="radio"
                    name="relType"
                    value={relType}
                    checked={selectedType === relType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="mr-2"
                  />
                  <span>{relType}</span>
                </label>
              ))}
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onSelect(selectedType)}
            disabled={!selectedType}
            className="flex-1 px-4 py-2 bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
          >
            Create
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

interface NodeCreatorProps {
  schema: any;
  onCreate: (labels: string[], properties: Record<string, any>) => void;
  onCancel: () => void;
}

function NodeCreator({ schema, onCreate, onCancel }: NodeCreatorProps) {
  const [selectedLabels, setSelectedLabels] = useState<string[]>([]);
  const [properties, setProperties] = useState<Record<string, any>>({
    name: '',
    id: '',
  });

  const handleLabelToggle = (label: string) => {
    if (selectedLabels.includes(label)) {
      setSelectedLabels(selectedLabels.filter(l => l !== label));
    } else {
      setSelectedLabels([...selectedLabels, label]);
    }
  };

  const handleCreate = () => {
    if (selectedLabels.length === 0) {
      alert('Please select at least one label');
      return;
    }
    if (!properties.name && !properties.title) {
      alert('Please provide a name or title');
      return;
    }
    // Generate ID if not provided
    if (!properties.id) {
      properties.id = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    onCreate(selectedLabels, properties);
  };

  const nodeLabels = schema?.node_labels || [];

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Create Node</h2>
        <button onClick={onCancel} className="text-gray-400 hover:text-white">
          ×
        </button>
      </div>
      
      <div className="mb-4">
        <div className="text-sm text-gray-400 mb-2">Labels</div>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {nodeLabels.map((label: string) => (
            <label key={label} className="flex items-center">
              <input
                type="checkbox"
                checked={selectedLabels.includes(label)}
                onChange={() => handleLabelToggle(label)}
                className="mr-2"
              />
              <span className="text-sm">{label}</span>
            </label>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <div className="text-sm text-gray-400 mb-2">Properties</div>
        <div className="space-y-2">
          <div>
            <label className="text-xs text-gray-400">ID (auto-generated if empty)</label>
            <input
              type="text"
              value={properties.id || ''}
              onChange={(e) => setProperties({ ...properties, id: e.target.value })}
              className="w-full p-2 bg-gray-700 rounded text-white text-sm"
              placeholder="Auto-generated"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Name/Title *</label>
            <input
              type="text"
              value={properties.name || properties.title || ''}
              onChange={(e) => {
                const key = selectedLabels.includes('Chapter') || selectedLabels.includes('Scene') ? 'title' : 'name';
                setProperties({ ...properties, [key]: e.target.value });
              }}
              className="w-full p-2 bg-gray-700 rounded text-white text-sm"
              placeholder="Enter name or title"
              required
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Description</label>
            <textarea
              value={properties.description || properties.synopsis || ''}
              onChange={(e) => {
                const key = selectedLabels.includes('Scene') || selectedLabels.includes('Chapter') ? 'synopsis' : 'description';
                setProperties({ ...properties, [key]: e.target.value });
              }}
              className="w-full p-2 bg-gray-700 rounded text-white text-sm"
              rows={3}
              placeholder="Enter description"
            />
          </div>
        </div>
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={handleCreate}
          className="flex-1 px-4 py-2 bg-green-600 rounded hover:bg-green-700"
        >
          Create
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

interface NodeInspectorProps {
  node: GraphNode;
  schema?: any;
  onUpdate: (nodeId: string, properties: Record<string, any>) => void;
  onDelete: (nodeId: string) => void;
  onClose: () => void;
}

function NodeInspector({ node, onUpdate, onDelete, onClose }: NodeInspectorProps) {
  const [editing, setEditing] = useState(false);
  const [properties, setProperties] = useState(node.properties);

  const handleSave = () => {
    onUpdate(node.id, properties);
    setEditing(false);
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Node Inspector</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-white">
          ×
        </button>
      </div>
      
      <div className="mb-4">
        <div className="text-sm text-gray-400">ID</div>
        <div className="text-sm font-mono">{node.id}</div>
      </div>
      
      <div className="mb-4">
        <div className="text-sm text-gray-400">Labels</div>
        <div className="flex gap-2 flex-wrap">
          {node.labels.map((label, idx) => (
            <span key={idx} className="px-2 py-1 bg-blue-600 rounded text-sm">
              {label}
            </span>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <div className="text-sm text-gray-400">Properties</div>
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              Edit
            </button>
          )}
        </div>
        
        {editing ? (
          <div className="space-y-2">
            {Object.entries(properties).map(([key, value]) => (
              <div key={key}>
                <label className="text-xs text-gray-400">{key}</label>
                <input
                  type="text"
                  value={String(value)}
                  onChange={(e) => setProperties({ ...properties, [key]: e.target.value })}
                  className="w-full p-2 bg-gray-700 rounded text-white text-sm"
                />
              </div>
            ))}
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-green-600 rounded hover:bg-green-700 text-sm"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setProperties(node.properties);
                  setEditing(false);
                }}
                className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {Object.entries(properties).map(([key, value]) => (
              <div key={key} className="text-sm">
                <span className="text-gray-400">{key}:</span>{' '}
                <span className="text-white">{String(value)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <button
        onClick={() => onDelete(node.id)}
        className="w-full px-4 py-2 bg-red-600 rounded hover:bg-red-700"
      >
        Delete Node
      </button>
    </div>
  );
}

