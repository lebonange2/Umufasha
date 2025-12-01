import { DocumentState } from './types';
import { setLabel } from './references';
import { toggleNodeNumbering } from './numbering';

interface NodePropertiesProps {
  state: DocumentState;
  nodeId: string | null;
  onStateChange: (state: DocumentState) => void;
}

export default function NodeProperties({
  state,
  nodeId,
  onStateChange,
}: NodePropertiesProps) {
  const node = nodeId ? state.nodes[nodeId] : null;
  
  if (!node) {
    return (
      <div className="w-64 border-l bg-white p-4">
        <p className="text-sm text-gray-500">No node selected</p>
      </div>
    );
  }

  const handleTitleChange = (title: string) => {
    const newNodes = { ...state.nodes };
    newNodes[node.id] = { ...node, title };
    onStateChange({ ...state, nodes: newNodes });
  };

  const handleLabelChange = (label: string) => {
    try {
      const newState = setLabel(state, node.id, label || null);
      onStateChange(newState);
    } catch (error: any) {
      alert(error.message);
    }
  };

  const handleNumberedToggle = (numbered: boolean) => {
    const newState = toggleNodeNumbering(state, node.id, numbered);
    onStateChange(newState);
  };

  return (
    <div className="w-64 border-l bg-white p-4 overflow-y-auto">
      <h3 className="font-semibold text-sm mb-4">Properties</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            value={node.title || ''}
            onChange={(e) => handleTitleChange(e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded"
            placeholder="Untitled"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Label (for references)
          </label>
          <input
            type="text"
            value={node.label || ''}
            onChange={(e) => handleLabelChange(e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded font-mono"
            placeholder="my-label"
          />
          {node.label && (
            <p className="text-xs text-gray-500 mt-1">
              Reference: <code>\ref{'{'}{node.label}{'}'}</code>
            </p>
          )}
        </div>

        <div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.numbered !== false}
              onChange={(e) => handleNumberedToggle(e.target.checked)}
            />
            <span className="text-xs text-gray-700">Numbered</span>
          </label>
          {node.number && (
            <p className="text-xs text-gray-500 mt-1">Number: {node.number}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Kind
          </label>
          <p className="text-xs text-gray-600">{node.kind}</p>
        </div>

        {node.meta && Object.keys(node.meta).length > 0 && (
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Metadata
            </label>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
              {JSON.stringify(node.meta, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

