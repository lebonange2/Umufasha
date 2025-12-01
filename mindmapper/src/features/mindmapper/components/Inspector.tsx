import { MindmapNode, NodeShape } from '../types';

interface InspectorProps {
  node: MindmapNode | null;
  onUpdate: (updates: Partial<MindmapNode>) => void;
  onAddChild: () => void;
  onAddSibling: () => void;
  onDelete: () => void;
}

export default function Inspector({ node, onUpdate, onAddChild, onAddSibling, onDelete }: InspectorProps) {
  if (!node) {
    return (
      <div
        style={{
          width: '250px',
          backgroundColor: '#f8f9fa',
          borderLeft: '1px solid #e0e0e0',
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
        }}
      >
        Select a node to edit
      </div>
    );
  }

  return (
    <div
      style={{
        width: '250px',
        backgroundColor: '#f8f9fa',
        borderLeft: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>Node Properties</h3>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
            Text
          </label>
          <textarea
            value={node.text}
            onChange={(e) => onUpdate({ text: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px',
              minHeight: '80px',
              resize: 'vertical',
            }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
            Background Color
          </label>
          <input
            type="color"
            value={node.color}
            onChange={(e) => onUpdate({ color: e.target.value })}
            style={{
              width: '100%',
              height: '40px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
            Text Color
          </label>
          <input
            type="color"
            value={node.textColor}
            onChange={(e) => onUpdate({ textColor: e.target.value })}
            style={{
              width: '100%',
              height: '40px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
            Shape
          </label>
          <select
            value={node.shape}
            onChange={(e) => onUpdate({ shape: e.target.value as NodeShape })}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          >
            <option value="rect">Rectangle</option>
            <option value="pill">Pill</option>
          </select>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
            Position
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '12px', color: '#666' }}>X</label>
              <input
                type="number"
                value={node.x}
                onChange={(e) => onUpdate({ x: parseInt(e.target.value) || 0 })}
                style={{
                  width: '100%',
                  padding: '6px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '12px', color: '#666' }}>Y</label>
              <input
                type="number"
                value={node.y}
                onChange={(e) => onUpdate({ y: parseInt(e.target.value) || 0 })}
                style={{
                  width: '100%',
                  padding: '6px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid #e0e0e0' }}>
        <button
          onClick={onAddChild}
          style={{
            width: '100%',
            padding: '10px',
            marginBottom: '8px',
            backgroundColor: '#4facfe',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
          }}
        >
          Add Child Node
        </button>
        <button
          onClick={onAddSibling}
          style={{
            width: '100%',
            padding: '10px',
            marginBottom: '8px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Add Sibling Node
        </button>
        <button
          onClick={onDelete}
          style={{
            width: '100%',
            padding: '10px',
            backgroundColor: '#ff5252',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Delete Node
        </button>
      </div>
    </div>
  );
}

