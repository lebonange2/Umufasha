import { DocNode, NodeKind, DocumentState, VALID_PARENT_CHILD, NODE_LEVELS } from './types';

/**
 * Core tree operations for document structure
 */

export function createNode(
  state: DocumentState,
  parentId: string | null,
  kind: NodeKind,
  position?: number
): { state: DocumentState; nodeId: string } {
  // Validate parent/child relationship
  if (parentId !== null) {
    const parent = state.nodes[parentId];
    if (!parent) {
      throw new Error(`Parent node ${parentId} not found`);
    }
    const validChildren = VALID_PARENT_CHILD[parent.kind];
    if (!validChildren.includes(kind)) {
      throw new Error(`Cannot create ${kind} as child of ${parent.kind}`);
    }
  }

  const nodeId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const siblings = getChildren(state, parentId);
  
  // Determine order
  let order: number;
  if (position !== undefined && position >= 0 && position <= siblings.length) {
    order = position;
    // Shift existing siblings
    siblings.forEach((sibling) => {
      if (sibling.order >= order) {
        state.nodes[sibling.id].order = sibling.order + 1;
      }
    });
  } else {
    order = siblings.length;
  }

  const newNode: DocNode = {
    id: nodeId,
    kind,
    parentId,
    order,
    numbered: kind !== 'toc' && kind !== 'paragraph', // Default numbering
    content: kind === 'paragraph' || kind === 'page' ? '' : undefined,
  };

  const newNodes = { ...state.nodes, [nodeId]: newNode };
  const newState = { ...state, nodes: newNodes };

  // Renumber after creation
  const renumberedState = computeNumbers(newState);

  return { state: renumberedState, nodeId };
}

export function deleteNode(
  state: DocumentState,
  nodeId: string,
  moveChildrenUp: boolean = false
): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  const children = getChildren(state, nodeId);
  
  if (children.length > 0 && !moveChildrenUp) {
    // Recursively delete children
    let newState = state;
    for (const child of children) {
      newState = deleteNode(newState, child.id, false);
    }
    state = newState;
  } else if (children.length > 0 && moveChildrenUp) {
    // Move children to parent
    const newNodes = { ...state.nodes };
    children.forEach((child) => {
      newNodes[child.id] = {
        ...child,
        parentId: node.parentId,
        order: child.order + (node.parentId ? getChildren(state, node.parentId).length : 0),
      };
    });
    state = { ...state, nodes: newNodes };
  }

  // Remove from labels if labeled
  const newLabels = { ...state.labels };
  if (node.label) {
    delete newLabels[node.label];
  }

  // Remove node and reorder siblings
  const siblings = getChildren(state, node.parentId);
  const newNodes = { ...state.nodes };
  delete newNodes[nodeId];
  
  siblings.forEach((sibling) => {
    if (sibling.id !== nodeId && sibling.order > node.order) {
      newNodes[sibling.id].order = sibling.order - 1;
    }
  });

  const newState = { ...state, nodes: newNodes, labels: newLabels };
  return computeNumbers(newState);
}

export function moveNode(
  state: DocumentState,
  nodeId: string,
  newParentId: string | null,
  newOrder: number
): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  // Validate new parent
  if (newParentId !== null) {
    const newParent = state.nodes[newParentId];
    if (!newParent) {
      throw new Error(`New parent ${newParentId} not found`);
    }
    const validChildren = VALID_PARENT_CHILD[newParent.kind];
    if (!validChildren.includes(node.kind)) {
      throw new Error(`Cannot move ${node.kind} to ${newParent.kind}`);
    }
  }

  // Check for cycles
  if (newParentId && isDescendant(state, newParentId, nodeId)) {
    throw new Error('Cannot move node into its own descendant');
  }

  const oldParentId = node.parentId;
  const oldOrder = node.order;

  // Remove from old position
  const oldSiblings = getChildren(state, oldParentId);
  const newNodes = { ...state.nodes };
  
  oldSiblings.forEach((sibling) => {
    if (sibling.id !== nodeId && sibling.order > oldOrder) {
      newNodes[sibling.id].order = sibling.order - 1;
    }
  });

  // Insert at new position
  const newSiblings = getChildren({ ...state, nodes: newNodes }, newParentId).filter(
    (n) => n.id !== nodeId
  );
  
  newSiblings.forEach((sibling) => {
    if (sibling.order >= newOrder) {
      newNodes[sibling.id].order = sibling.order + 1;
    }
  });

  // Update node
  newNodes[nodeId] = {
    ...node,
    parentId: newParentId,
    order: newOrder,
  };

  const newState = { ...state, nodes: newNodes };
  return computeNumbers(newState);
}

export function promoteNode(state: DocumentState, nodeId: string): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  const currentLevel = NODE_LEVELS[node.kind];
  if (currentLevel === 0) {
    throw new Error('Cannot promote top-level node');
  }

  // Find the next level up
  const parent = node.parentId ? state.nodes[node.parentId] : null;
  if (!parent) {
    throw new Error('Cannot promote root-level node');
  }

  // Determine new kind based on parent
  let newKind: NodeKind;
  if (parent.kind === 'part') {
    newKind = 'chapter';
  } else if (parent.kind === 'chapter') {
    newKind = 'section';
  } else if (parent.kind === 'section') {
    newKind = 'subsection';
  } else if (parent.kind === 'subsection') {
    newKind = 'subsubsection';
  } else {
    throw new Error(`Cannot promote ${node.kind} from ${parent.kind}`);
  }

  const newNodes = { ...state.nodes };
  newNodes[nodeId] = {
    ...node,
    kind: newKind,
  };

  const newState = { ...state, nodes: newNodes };
  return computeNumbers(newState);
}

export function demoteNode(state: DocumentState, nodeId: string): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  // Determine new kind
  let newKind: NodeKind;
  if (node.kind === 'chapter') {
    newKind = 'section';
  } else if (node.kind === 'section') {
    newKind = 'subsection';
  } else if (node.kind === 'subsection') {
    newKind = 'subsubsection';
  } else if (node.kind === 'subsubsection') {
    newKind = 'paragraph';
  } else {
    throw new Error(`Cannot demote ${node.kind}`);
  }

  // Check if parent allows this kind
  const parent = node.parentId ? state.nodes[node.parentId] : null;
  if (parent) {
    const validChildren = VALID_PARENT_CHILD[parent.kind];
    if (!validChildren.includes(newKind)) {
      // Need to move to a different parent or create intermediate node
      throw new Error(`Cannot demote ${node.kind} - parent ${parent.kind} does not allow ${newKind}`);
    }
  }

  const newNodes = { ...state.nodes };
  newNodes[nodeId] = {
    ...node,
    kind: newKind,
  };

  const newState = { ...state, nodes: newNodes };
  return computeNumbers(newState);
}

export function splitAtCaret(
  state: DocumentState,
  nodeId: string,
  caretPosition: number
): { state: DocumentState; newNodeId: string } {
  const node = state.nodes[nodeId];
  if (!node || !node.content) {
    throw new Error(`Node ${nodeId} has no content to split`);
  }

  const beforeText = node.content.slice(0, caretPosition).trim();
  const afterText = node.content.slice(caretPosition).trim();

  // Update current node
  const newNodes = { ...state.nodes };
  newNodes[nodeId] = {
    ...node,
    content: beforeText,
  };

  // Create new sibling
  const siblings = getChildren(state, node.parentId);
  const newNodeId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const newNode: DocNode = {
    id: newNodeId,
    kind: node.kind,
    parentId: node.parentId,
    order: node.order + 1,
    content: afterText,
    numbered: node.numbered,
  };

  // Shift siblings
  siblings.forEach((sibling) => {
    if (sibling.id !== nodeId && sibling.order > node.order) {
      newNodes[sibling.id].order = sibling.order + 1;
    }
  });

  newNodes[newNodeId] = newNode;

  const newState = { ...state, nodes: newNodes };
  const renumberedState = computeNumbers(newState);
  return { state: renumberedState, newNodeId };
}

export function mergeWithPrev(state: DocumentState, nodeId: string): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  const siblings = getChildren(state, node.parentId);
  const prevSibling = siblings.find((s) => s.order === node.order - 1);
  
  if (!prevSibling) {
    throw new Error('No previous sibling to merge with');
  }

  const newNodes = { ...state.nodes };
  const prevContent = prevSibling.content || '';
  const nodeContent = node.content || '';
  const separator = prevContent && nodeContent ? '\n\n' : '';
  
  newNodes[prevSibling.id] = {
    ...prevSibling,
    content: prevContent + separator + nodeContent,
  };

  // Remove current node and reorder
  delete newNodes[nodeId];
  siblings.forEach((sibling) => {
    if (sibling.id !== nodeId && sibling.order > node.order) {
      newNodes[sibling.id].order = sibling.order - 1;
    }
  });

  // Remove label if exists
  const newLabels = { ...state.labels };
  if (node.label) {
    delete newLabels[node.label];
  }

  const newState = { ...state, nodes: newNodes, labels: newLabels };
  return computeNumbers(newState);
}

export function getChildren(state: DocumentState, parentId: string | null): DocNode[] {
  return Object.values(state.nodes)
    .filter((node) => node.parentId === parentId)
    .sort((a, b) => a.order - b.order);
}

export function getNodePath(state: DocumentState, nodeId: string): DocNode[] {
  const path: DocNode[] = [];
  let current: DocNode | undefined = state.nodes[nodeId];
  
  while (current) {
    path.unshift(current);
    current = current.parentId ? state.nodes[current.parentId] : undefined;
  }
  
  return path;
}

export function isDescendant(state: DocumentState, ancestorId: string, descendantId: string): boolean {
  let current: DocNode | undefined = state.nodes[descendantId];
  
  while (current) {
    if (current.id === ancestorId) {
      return true;
    }
    current = current.parentId ? state.nodes[current.parentId] : undefined;
  }
  
  return false;
}

export function computeNumbers(state: DocumentState): DocumentState {
  const newNodes = { ...state.nodes };
  
  function processLevel(parentId: string | null, counters: number[]): void {
    const children = getChildren({ ...state, nodes: newNodes }, parentId);
    
    if (children.length === 0) return;
    
    // Process children in order
    let counter = 1;
    children.forEach((child) => {
      const numbering = state.settings.numbering[child.kind as keyof typeof state.settings.numbering];
      const numbered = child.numbered !== false && numbering !== 'none';
      
      if (numbered) {
        // Build number from counters + current counter
        const newCounters = [...counters, counter];
        const number = formatNumber(newCounters, child.kind, numbering);
        newNodes[child.id] = {
          ...child,
          number,
        };
        
        // Process children with updated counters
        processLevel(child.id, newCounters);
        counter++;
      } else {
        newNodes[child.id] = {
          ...child,
          number: undefined,
        };
        // Process children with same counters (no increment)
        processLevel(child.id, counters);
      }
    });
  }
  
  processLevel(null, []);
  
  return { ...state, nodes: newNodes };
}

function formatNumber(counters: number[], kind: NodeKind, scheme: string): string {
  if (scheme === 'none') {
    return '';
  }
  
  // For parts, use only the part counter with roman
  if (kind === 'part' && scheme === 'roman') {
    return toRoman(counters[counters.length - 1] || 1);
  }
  
  // For chapters, use only the chapter counter
  if (kind === 'chapter' && scheme === 'arabic') {
    return String(counters[counters.length - 1] || 1);
  }
  
  // For sections/subsections, use dotted notation (skip part if present)
  if (scheme === 'dotted') {
    // Find the chapter counter index (first non-part)
    let startIdx = 0;
    for (let i = 0; i < counters.length - 1; i++) {
      // Check if this level corresponds to chapter
      if (i === 0 && counters.length > 1) {
        // First counter might be part, skip it
        startIdx = 1;
        break;
      }
    }
    // Use all counters from chapter onwards
    return counters.slice(startIdx).join('.');
  }
  
  return String(counters[counters.length - 1] || 1);
}

function toRoman(num: number): string {
  const values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];
  const numerals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'];
  
  let result = '';
  for (let i = 0; i < values.length; i++) {
    while (num >= values[i]) {
      result += numerals[i];
      num -= values[i];
    }
  }
  return result;
}

