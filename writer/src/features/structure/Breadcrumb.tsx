import { DocumentState } from './types';
import { getNodePath } from './tree';

interface BreadcrumbProps {
  state: DocumentState;
  nodeId: string | null;
  onNavigate: (nodeId: string) => void;
}

export default function Breadcrumb({ state, nodeId, onNavigate }: BreadcrumbProps) {
  if (!nodeId) {
    return null;
  }

  const path = getNodePath(state, nodeId);
  
  if (path.length === 0) {
    return null;
  }

  return (
    <div className="px-4 py-2 border-b bg-gray-50 text-sm flex items-center gap-2 flex-wrap">
      {path.map((node, index) => (
        <span key={node.id} className="flex items-center gap-2">
          {index > 0 && <span className="text-gray-400">›</span>}
          <button
            onClick={() => onNavigate(node.id)}
            className="hover:text-blue-600 hover:underline"
          >
            {node.number && node.numbered !== false ? (
              <span>
                {node.number} {node.title || `Untitled ${node.kind}`}
              </span>
            ) : (
              <span>{node.title || `Untitled ${node.kind}`}</span>
            )}
          </button>
        </span>
      ))}
    </div>
  );
}

