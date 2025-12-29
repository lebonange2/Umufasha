import { useEffect, useRef, useState } from 'react';
// @ts-ignore
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

interface EmbeddedGraphProps {
  projectId: string;
  height?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
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

export default function EmbeddedGraph({ 
  projectId, 
  height = '500px',
  autoRefresh = true,
  refreshInterval = 5000 
}: EmbeddedGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);

  const loadGraph = async () => {
    if (!projectId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/projects/${projectId}/graph?depth=2`);
      
      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = 'Failed to load graph';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      
      // Ensure data has nodes and edges arrays
      const graphData = {
        nodes: data.nodes || [],
        edges: data.edges || []
      };
      
      setGraphData(graphData);
      setNodeCount(graphData.nodes.length);
      setEdgeCount(graphData.edges.length);
      
      if (graphRef.current) {
        graphRef.current.graphData(graphData);
      }
      
      setLoading(false);
      setError(null);
      
      // If graph is empty, try to initialize it
      if (graphData.nodes.length === 0 && graphData.edges.length === 0) {
        // Silently try to initialize - don't show error for empty graph
        try {
          const initResponse = await fetch(`/api/projects/${projectId}/graph/init?title=Project&genre=`, {
            method: 'POST',
          });
          if (initResponse.ok) {
            const initData = await initResponse.json();
            // If Neo4j is unavailable, that's okay - graph will be empty
            if (initData.neo4j_unavailable) {
              console.log('Neo4j is not available - graph will remain empty until Neo4j is started');
            } else {
              // Reload after a short delay if initialization succeeded
              setTimeout(() => {
                loadGraph();
              }, 500);
            }
          }
        } catch (initErr) {
          // Ignore initialization errors - empty graph is acceptable
          console.log('Graph initialization skipped or failed (non-critical):', initErr);
        }
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load graph';
      setError(errorMessage);
      setLoading(false);
      console.error('Failed to load graph:', err);
    }
  };

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
      .linkWidth(1.5)
      .linkDirectionalArrowLength(4)
      .linkDirectionalArrowRelPos(1)
      .linkCurvature(0.2)
      .nodeRelSize(6)
      .enableNodeDrag(true)
      .showNavInfo(false);

    graphRef.current = Graph;

    // Load initial data
    loadGraph();

    // Auto-refresh if enabled
    let intervalId: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      intervalId = setInterval(loadGraph, refreshInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      Graph._destructor();
    };
  }, [projectId, autoRefresh, refreshInterval]);

  // Manual refresh function
  const handleRefresh = () => {
    setError(null);
    setLoading(true);
    loadGraph();
  };

  // Error display is handled in the main return below

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden border-2 border-gray-700 relative" style={{ height }}>
      <div className="bg-gray-800 text-white px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold">📊 Knowledge Graph</h3>
          <div className="text-sm text-gray-400">
            {nodeCount} nodes • {edgeCount} relationships
          </div>
        </div>
        <div className="flex items-center gap-2">
          {loading && (
            <span className="text-xs text-gray-400">Loading...</span>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm disabled:opacity-50"
            title="Refresh graph"
          >
            🔄
          </button>
        </div>
      </div>
      <div ref={containerRef} style={{ width: '100%', height: 'calc(100% - 48px)' }} />
      {loading && graphData.nodes.length === 0 && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75 z-0">
          <div className="text-white">Loading graph...</div>
        </div>
      )}
      {!loading && graphData.nodes.length === 0 && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-0">
          <div className="text-white text-center">
            <p className="mb-2">Graph is empty</p>
            <p className="text-sm text-gray-400">Nodes will appear as the book writing progresses</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 bg-red-50 border-2 border-red-300 rounded-lg flex flex-col items-center justify-center p-4 z-10">
          <p className="text-red-700 font-semibold mb-2">Error loading graph</p>
          <p className="text-red-600 text-sm mb-4 text-center max-w-md">{error}</p>
          <div className="flex gap-2">
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 font-semibold"
            >
              🔄 Retry
            </button>
            <button
              onClick={() => {
                setError(null);
                setLoading(false);
              }}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Dismiss
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-4 text-center max-w-md">
            Note: Graph requires Neo4j to be running. If Neo4j is not available,<br />
            the graph will be empty but the book writing process will continue normally.
          </p>
        </div>
      )}
    </div>
  );
}

