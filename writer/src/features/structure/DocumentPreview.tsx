import { useNavigate } from 'react-router-dom';
import { DocumentState } from './types';
import { getChildren } from './tree';
import { exportToPlainText } from './exporters/plaintext';

interface DocumentPreviewProps {
  state: DocumentState;
  onClose?: () => void;
  onApprove?: (content: string) => void;
}

export default function DocumentPreview({ state, onClose, onApprove }: DocumentPreviewProps) {
  const navigate = useNavigate();

  function renderNode(nodeId: string, depth: number = 0): JSX.Element[] {
    const node = state.nodes[nodeId];
    if (!node) return [];

    const children = getChildren(state, nodeId);
    const elements: JSX.Element[] = [];

    // Skip TOC node in preview
    if (node.kind === 'toc') {
      children.forEach(child => {
        elements.push(...renderNode(child.id, depth));
      });
      return elements;
    }

    // Render the node
    const marginLeft = depth * 24;
    const headingSizes = {
      part: 'text-3xl font-bold',
      chapter: 'text-2xl font-bold',
      section: 'text-xl font-semibold',
      subsection: 'text-lg font-medium',
      subsubsection: 'text-base font-medium',
      paragraph: 'text-base',
      page: 'text-base',
    };

    const headingSize = headingSizes[node.kind] || 'text-base';

    // Title with number
    if (node.kind !== 'paragraph') {
      elements.push(
        <div key={`${nodeId}-title`} style={{ marginLeft: `${marginLeft}px` }} className="mt-4 mb-2">
          <h1 className={headingSize}>
            {node.number && node.numbered !== false && (
              <span className="mr-2">{node.number}</span>
            )}
            {node.title || `Untitled ${node.kind}`}
          </h1>
        </div>
      );
    }

    // Content
    if (node.content) {
      elements.push(
        <div key={`${nodeId}-content`} style={{ marginLeft: `${marginLeft + 8}px` }} className="mb-4">
          <div className="text-base leading-relaxed whitespace-pre-wrap">
            {node.content}
          </div>
        </div>
      );
    }

    // Render children
    children.forEach(child => {
      elements.push(...renderNode(child.id, depth + 1));
    });

    return elements;
  }

  const rootNodes = getChildren(state, null);
  const contentNodes = rootNodes.filter(n => n.kind !== 'toc');

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  const handleApprove = () => {
    // Convert document state to plain text
    const content = exportToPlainText(state);
    
    if (onApprove) {
      onApprove(content);
    } else {
      // Navigate to writer home with content
      navigate('/', {
        state: {
          structureMode: false,
          content: content,
          title: state.nodes[state.rootId]?.title || 'Document',
        },
        replace: false,
      });
    }
    
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-8">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl h-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b p-4 flex items-center justify-between bg-gray-50 rounded-t-lg">
          <h2 className="text-xl font-semibold">Document Preview</h2>
          <div className="flex gap-2">
            <button
              onClick={handleApprove}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              title="Send document to writer home page"
            >
              ✓ Approve
            </button>
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              ✕ Close
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-8 bg-white">
          {contentNodes.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <p>No content to preview. Add chapters and sections to see the document.</p>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto">
              {contentNodes.map(node => (
                <div key={node.id}>
                  {renderNode(node.id, 0)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

