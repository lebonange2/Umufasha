import { describe, it, expect } from 'vitest';
import { DocumentState, DEFAULT_NUMBERING } from '../types';
import { createNode } from '../tree';
import { setLabel, findByLabel, formatReferenceText } from '../references';

describe('References', () => {
  it('should set and find labels', () => {
    const state: DocumentState = {
      rootId: 'root',
      nodes: {
        root: {
          id: 'root',
          kind: 'toc',
          parentId: null,
          order: 0,
        },
      },
      settings: {
        numbering: DEFAULT_NUMBERING,
        pageMode: { enabled: false, wordsPerPage: 300 },
      },
      labels: {},
      versions: [],
    };

    const { state: state1, nodeId } = createNode(state, null, 'section');
    const state2 = setLabel(state1, nodeId, 'my-section');

    const found = findByLabel(state2, 'my-section');
    expect(found?.id).toBe(nodeId);
  });

  it('should prevent duplicate labels', () => {
    const state: DocumentState = {
      rootId: 'root',
      nodes: {
        root: {
          id: 'root',
          kind: 'toc',
          parentId: null,
          order: 0,
        },
      },
      settings: {
        numbering: DEFAULT_NUMBERING,
        pageMode: { enabled: false, wordsPerPage: 300 },
      },
      labels: {},
      versions: [],
    };

    const { state: state1, nodeId: node1 } = createNode(state, null, 'section');
    const { state: state2, nodeId: node2 } = createNode(state1, null, 'section');

    const state3 = setLabel(state2, node1, 'my-label');
    
    expect(() => {
      setLabel(state3, node2, 'my-label');
    }).toThrow('already in use');
  });

  it('should format reference text correctly', () => {
    const state: DocumentState = {
      rootId: 'root',
      nodes: {
        root: {
          id: 'root',
          kind: 'toc',
          parentId: null,
          order: 0,
        },
      },
      settings: {
        numbering: DEFAULT_NUMBERING,
        pageMode: { enabled: false, wordsPerPage: 300 },
      },
      labels: {},
      versions: [],
    };

    const { state: state1, nodeId } = createNode(state, null, 'section');
    const state2 = setLabel(state1, nodeId, 'my-section');
    
    // Update node with number
    const node = state2.nodes[nodeId];
    const state3 = {
      ...state2,
      nodes: {
        ...state2.nodes,
        [nodeId]: {
          ...node,
          number: '2.3',
        },
      },
    };

    const text = formatReferenceText(state3, nodeId);
    expect(text).toContain('Section');
    expect(text).toContain('2.3');
  });
});

