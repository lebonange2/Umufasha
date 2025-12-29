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
  const [neo4jAvailable, setNeo4jAvailable] = useState<boolean | null>(null);

  const checkNeo4jStatus = async () => {
    try {
      const response = await fetch('/api/graph/status');
      if (response.ok) {
        const status = await response.json();
        setNeo4jAvailable(status.neo4j_available);
        return status.neo4j_available;
      }
    } catch (err) {
      console.error('Failed to check Neo4j status:', err);
    }
    return null;
  };

  const loadGraph = async () => {
    if (!projectId) return;
    
    setLoading(true);
    setError(null);
    
    // Check Neo4j status first
    await checkNeo4jStatus();
    
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
      
      console.log('Graph data received:', data);
      
      // Transform data to 3d-force-graph format
      // The library expects 'links' with 'source' and 'target', not 'edges' with 'from' and 'to'
      const graphData = {
        nodes: (data.nodes || []).map((node: any) => ({
          id: node.id,
          labels: node.labels || [],
          properties: node.properties || {},
          ...node  // Include all other properties
        })),
        links: (data.edges || []).map((edge: any) => ({
          source: edge.from,
          target: edge.to,
          type: edge.type,
          properties: edge.properties || {}
        }))
      };
      
      console.log('Transformed graph data:', {
        nodeCount: graphData.nodes.length,
        linkCount: graphData.links.length,
        nodes: graphData.nodes,
        links: graphData.links
      });
      
      // Keep original format in state for display
      setGraphData({ nodes: graphData.nodes, edges: data.edges || [] });
      setNodeCount(graphData.nodes.length);
      setEdgeCount(graphData.links.length);
      
      if (graphRef.current) {
        // Pass transformed data to 3D graph
        console.log('Updating graph with data');
        graphRef.current.graphData(graphData);
      }
      
      setLoading(false);
      setError(null);
      
      // If graph is empty, try to initialize it
      if (graphData.nodes.length === 0 && graphData.links.length === 0) {
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
      .nodeRelSize(8)  // Increased from 6 to 8 for better visibility
      .nodeResolution(16)  // Higher resolution for smoother spheres
      .linkColor(() => 0xaaaaaa)
      .linkWidth(2)  // Increased from 1.5 to 2
      .linkDirectionalArrowLength(6)  // Increased from 4 to 6
      .linkDirectionalArrowRelPos(1)
      .linkCurvature(0.2)
      .linkOpacity(0.6)
      .enableNodeDrag(true)
      .showNavInfo(false)
      .backgroundColor('#1a1a1a')  // Dark background for better contrast
      .d3AlphaDecay(0.01)  // Slower physics decay for smoother settling
      .d3VelocityDecay(0.3);  // Control velocity for better stability

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
          <div className="text-white text-center px-4">
            {neo4jAvailable === false ? (
              <>
                <p className="mb-2 text-yellow-400 font-semibold">⚠️ Neo4j Not Running</p>
                <p className="text-sm text-gray-300 mb-3">
                  The knowledge graph requires Neo4j to be running.
                </p>
                <div className="text-xs text-gray-400 space-y-1">
                  <p>To start Neo4j:</p>
                  <code className="block bg-gray-800 px-3 py-2 rounded mt-2">neo4j start</code>
                  <p className="mt-2">or</p>
                  <code className="block bg-gray-800 px-3 py-2 rounded mt-2">docker-compose up -d neo4j</code>
                </div>
                <p className="text-xs text-gray-500 mt-4">
                  Note: The book writing process works without Neo4j.
                </p>
              </>
            ) : (
              <>
                <p className="mb-2">Graph is empty</p>
                <p className="text-sm text-gray-400">Nodes will appear as the book writing progresses</p>
              </>
            )}
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 bg-red-50 border-2 border-red-300 rounded-lg flex flex-col items-center justify-center p-4 z-10">
          <p className="text-red-700 font-semibold mb-2">
            {neo4jAvailable === false ? '⚠️ Neo4j Not Running' : 'Error loading graph'}
          </p>
          <p className="text-red-600 text-sm mb-4 text-center max-w-md">{error}</p>
          {neo4jAvailable === false && (
            <div className="bg-yellow-50 border border-yellow-300 rounded p-3 mb-4 text-xs text-gray-700 max-w-md">
              <p className="font-semibold mb-2">To start Neo4j:</p>
              <code className="block bg-gray-800 text-white px-2 py-1 rounded mb-1">neo4j start</code>
              <p className="my-1">or if using Docker:</p>
              <code className="block bg-gray-800 text-white px-2 py-1 rounded">docker-compose up -d neo4j</code>
            </div>
          )}
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
            Note: The book writing process works without Neo4j.<br />
            The graph is optional and provides visual knowledge mapping.
          </p>
        </div>
      )}
    </div>
  );
}

