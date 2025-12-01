import { describe, it, expect } from 'vitest';
import { DocumentState, DEFAULT_NUMBERING } from '../types';
import { createNode, deleteNode, moveNode, promoteNode, demoteNode } from '../tree';

describe('Tree Operations', () => {
  function createInitialState(): DocumentState {
    return {
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
  }

  it('should create nodes', () => {
    const state = createInitialState();
    const { state: newState, nodeId } = createNode(state, null, 'chapter');
    
    expect(newState.nodes[nodeId]).toBeDefined();
    expect(newState.nodes[nodeId].kind).toBe('chapter');
  });

  it('should delete nodes', () => {
    const state = createInitialState();
    const { state: state1, nodeId } = createNode(state, null, 'chapter');
    const state2 = deleteNode(state1, nodeId);
    
    expect(state2.nodes[nodeId]).toBeUndefined();
  });

  it('should move nodes', () => {
    const state = createInitialState();
    const { state: state1, nodeId: part1 } = createNode(state, null, 'part');
    const { state: state2, nodeId: part2 } = createNode(state1, null, 'part');
    const { state: state3, nodeId: chapter } = createNode(state2, part1, 'chapter');
    
    const state4 = moveNode(state3, chapter, part2, 0);
    const movedChapter = state4.nodes[chapter];
    
    expect(movedChapter.parentId).toBe(part2);
    expect(movedChapter.order).toBe(0);
  });

  it('should promote nodes', () => {
    const state = createInitialState();
    const { state: state1, nodeId: part } = createNode(state, null, 'part');
    const { state: state2, nodeId: chapter } = createNode(state1, part, 'chapter');
    const { state: state3, nodeId: section } = createNode(state2, chapter, 'section');
    
    const state4 = promoteNode(state3, section);
    const promoted = state4.nodes[section];
    
    expect(promoted.kind).toBe('chapter');
  });

  it('should demote nodes', () => {
    const state = createInitialState();
    const { state: state1, nodeId: part } = createNode(state, null, 'part');
    const { state: state2, nodeId: chapter } = createNode(state1, part, 'chapter');
    
    const state3 = demoteNode(state2, chapter);
    const demoted = state3.nodes[chapter];
    
    expect(demoted.kind).toBe('section');
  });
});

