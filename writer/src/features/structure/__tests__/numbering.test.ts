import { describe, it, expect } from 'vitest';
import { DocumentState, DEFAULT_NUMBERING } from '../types';
import { createNode } from '../tree';

describe('Numbering', () => {
  it('should number parts with roman numerals', () => {
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

    const { state: state1 } = createNode(state, null, 'part');
    const { state: state2 } = createNode(state1, null, 'part');
    const { state: state3 } = createNode(state2, null, 'part');

    const part1 = Object.values(state3.nodes).find((n) => n.kind === 'part' && n.order === 0);
    const part2 = Object.values(state3.nodes).find((n) => n.kind === 'part' && n.order === 1);
    const part3 = Object.values(state3.nodes).find((n) => n.kind === 'part' && n.order === 2);

    expect(part1?.number).toBe('I');
    expect(part2?.number).toBe('II');
    expect(part3?.number).toBe('III');
  });

  it('should number chapters with arabic numerals', () => {
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

    const { state: state1, nodeId: partId } = createNode(state, null, 'part');
    const { state: state2 } = createNode(state1, partId, 'chapter');
    const { state: state3 } = createNode(state2, partId, 'chapter');

    const chapter1 = Object.values(state3.nodes).find((n) => n.kind === 'chapter' && n.order === 0);
    const chapter2 = Object.values(state3.nodes).find((n) => n.kind === 'chapter' && n.order === 1);

    expect(chapter1?.number).toBe('1');
    expect(chapter2?.number).toBe('2');
  });

  it('should number sections with dotted notation', () => {
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

    const { state: state1, nodeId: partId } = createNode(state, null, 'part');
    const { state: state2, nodeId: chapterId } = createNode(state1, partId, 'chapter');
    const { state: state3 } = createNode(state2, chapterId, 'section');
    const { state: state4 } = createNode(state3, chapterId, 'section');

    const section1 = Object.values(state4.nodes).find((n) => n.kind === 'section' && n.order === 0);
    const section2 = Object.values(state4.nodes).find((n) => n.kind === 'section' && n.order === 1);

    expect(section1?.number).toBe('1.1');
    expect(section2?.number).toBe('1.2');
  });
});

