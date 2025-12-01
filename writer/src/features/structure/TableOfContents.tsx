import { DocumentState, DocNode } from './types';
import { getChildren } from './tree';

interface TableOfContentsProps {
  state: DocumentState;
  onNavigate: (nodeId: string) => void;
  maxDepth?: number;
}

export default function TableOfContents({
  state,
  onNavigate,
  maxDepth = 3,
}: TableOfContentsProps) {
  function renderNode(node: DocNode, depth: number = 0): JSX.Element | null {
    // Only show numbered nodes in TOC
    if (node.kind === 'paragraph' || node.kind === 'page' || node.kind === 'toc') {
      return null;
    }

    if (depth > maxDepth) {
      return null;
    }

    const children = getChildren(state, node.id);
    const hasChildren = children.length > 0;

    return (
      <div key={node.id} className="mb-2">
        <button
          onClick={() => onNavigate(node.id)}
          className="text-left hover:text-blue-600 hover:underline text-sm"
        >
          {node.number && node.numbered !== false ? (
            <span>
              {node.number} {node.title || `Untitled ${node.kind}`}
            </span>
          ) : (
            <span>{node.title || `Untitled ${node.kind}`}</span>
          )}
        </button>
        {hasChildren && (
          <div className="ml-4 mt-1">
            {children.map((child) => renderNode(child, depth + 1)).filter(Boolean)}
          </div>
        )}
      </div>
    );
  }

  const rootNodes = getChildren(state, null);
  const contentNodes = rootNodes.filter((n) => n.kind !== 'toc');

  return (
    <div className="p-4">
      <h3 className="font-semibold text-sm mb-4">Table of Contents</h3>
      <div className="space-y-1">
        {contentNodes.map((node) => renderNode(node))}
      </div>
    </div>
  );
}

