import { DocNode, DocumentState } from './types';
import { getNodePath } from './tree';

/**
 * Label and cross-reference management
 */

export function setLabel(
  state: DocumentState,
  nodeId: string,
  label: string | null
): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  // Check uniqueness if setting a label
  if (label) {
    const existingNodeId = state.labels[label];
    if (existingNodeId && existingNodeId !== nodeId) {
      throw new Error(`Label "${label}" is already in use`);
    }
  }

  // Remove old label
  const newLabels = { ...state.labels };
  if (node.label) {
    delete newLabels[node.label];
  }

  // Add new label
  if (label) {
    newLabels[label] = nodeId;
  }

  const newNodes = { ...state.nodes };
  newNodes[nodeId] = {
    ...node,
    label: label || undefined,
  };

  return { ...state, nodes: newNodes, labels: newLabels };
}

export function findByLabel(state: DocumentState, label: string): DocNode | null {
  const nodeId = state.labels[label];
  if (!nodeId) {
    return null;
  }
  return state.nodes[nodeId] || null;
}

export interface Reference {
  type: 'ref';
  label: string;
  nodeId: string;
  displayText?: string;
}

export function parseReference(text: string): Reference | null {
  // Match patterns like \ref{label} or [ref:label] or {{ref:label}}
  const patterns = [
    /\\ref\{([^}]+)\}/,
    /\[ref:([^\]]+)\]/,
    /\{\{ref:([^}]+)\}\}/,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return {
        type: 'ref',
        label: match[1],
        nodeId: '',
      };
    }
  }

  return null;
}

export function insertReference(state: DocumentState, targetNodeId: string): Reference {
  const targetNode = state.nodes[targetNodeId];
  if (!targetNode) {
    throw new Error(`Target node ${targetNodeId} not found`);
  }

  if (!targetNode.label) {
    throw new Error(`Target node ${targetNodeId} has no label`);
  }

  return {
    type: 'ref',
    label: targetNode.label,
    nodeId: targetNodeId,
    displayText: formatReferenceText(state, targetNodeId),
  };
}

export function formatReferenceText(state: DocumentState, nodeId: string): string {
  const node = state.nodes[nodeId];
  if (!node) {
    return 'Unknown';
  }

  const path = getNodePath(state, nodeId);
  
  // Find the most significant node in the path
  let displayNode = node;
  for (let i = path.length - 1; i >= 0; i--) {
    if (path[i].kind === 'part' || path[i].kind === 'chapter' || path[i].kind === 'section') {
      displayNode = path[i];
      break;
    }
  }

  const kindLabels: Record<string, string> = {
    part: 'Part',
    chapter: 'Chapter',
    section: 'Section',
    subsection: 'Subsection',
    subsubsection: 'Subsubsection',
  };

  const kindLabel = kindLabels[displayNode.kind] || '';
  const number = displayNode.number || '';
  
  if (number) {
    return `${kindLabel} ${number}`;
  } else if (displayNode.title) {
    return displayNode.title;
  } else {
    return kindLabel || 'Reference';
  }
}

export function renderReferenceInText(
  state: DocumentState,
  ref: Reference
): string {
  const node = findByLabel(state, ref.label);
  if (!node) {
    return `[Reference to ${ref.label} not found]`;
  }

  return formatReferenceText(state, node.id);
}

export function updateReferencesInContent(
  state: DocumentState,
  content: string
): string {
  // Find all references in content
  const refPattern = /(\\ref\{([^}]+)\}|\[ref:([^\]]+)\]|\{\{ref:([^}]+)\}\})/g;
  let result = content;
  let match;

  while ((match = refPattern.exec(content)) !== null) {
    const label = match[2] || match[3] || match[4];
    const node = findByLabel(state, label);
    
    if (node) {
      const displayText = formatReferenceText(state, node.id);
      result = result.replace(match[0], displayText);
    }
  }

  return result;
}

export function extractReferencesFromContent(content: string): Reference[] {
  const refs: Reference[] = [];
  const refPattern = /(\\ref\{([^}]+)\}|\[ref:([^\]]+)\]|\{\{ref:([^}]+)\}\})/g;
  let match;

  while ((match = refPattern.exec(content)) !== null) {
    const label = match[2] || match[3] || match[4];
    refs.push({
      type: 'ref',
      label,
      nodeId: '',
    });
  }

  return refs;
}

