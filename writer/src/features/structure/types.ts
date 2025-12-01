export type NodeKind = 'part' | 'chapter' | 'section' | 'subsection' | 'subsubsection' | 'paragraph' | 'page' | 'toc';

export interface DocNode {
  id: string;
  kind: NodeKind;
  parentId: string | null;
  order: number;
  title?: string;
  content?: string; // rich/plain text body for leaf-ish nodes
  label?: string; // unique label for \ref
  numbered?: boolean; // default true unless style says otherwise
  number?: string; // computed e.g. "2.3.1"
  meta?: Record<string, any>; // notes, custom fields
}

export type NumberingScheme = 'roman' | 'arabic' | 'dotted' | 'none';

export interface NumberingSettings {
  part: NumberingScheme;
  chapter: NumberingScheme;
  section: NumberingScheme;
  subsection: NumberingScheme;
  subsubsection: NumberingScheme;
}

export interface PageModeSettings {
  enabled: boolean;
  wordsPerPage: number;
}

export interface DocumentState {
  rootId: string;
  nodes: Record<string, DocNode>;
  settings: {
    numbering: NumberingSettings;
    pageMode: PageModeSettings;
  };
  labels: Record<string, string>; // label -> nodeId
  versions: Version[]; // reuse existing versioning
}

export interface Version {
  id: string;
  createdAt: number;
  state: DocumentState;
}

// Valid parent/child relationships
export const VALID_PARENT_CHILD: Record<NodeKind, NodeKind[]> = {
  part: ['chapter'],
  chapter: ['section', 'page', 'paragraph'],
  section: ['subsection', 'paragraph'],
  subsection: ['subsubsection', 'paragraph'],
  subsubsection: ['paragraph'],
  paragraph: [],
  page: ['paragraph'],
  toc: [],
};

// Default numbering settings
export const DEFAULT_NUMBERING: NumberingSettings = {
  part: 'roman',
  chapter: 'arabic',
  section: 'dotted',
  subsection: 'dotted',
  subsubsection: 'dotted',
};

// Node kind hierarchy (for level-based operations)
export const NODE_LEVELS: Record<NodeKind, number> = {
  part: 0,
  chapter: 1,
  section: 2,
  subsection: 3,
  subsubsection: 4,
  paragraph: 5,
  page: 1, // Same level as chapter when used
  toc: 0,
};

