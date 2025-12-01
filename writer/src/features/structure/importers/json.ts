import { DocumentState, DEFAULT_NUMBERING } from '../types';
import { computeNumbers } from '../tree';

export function importFromJSON(json: string): DocumentState {
  const parsed = JSON.parse(json);
  
  // Validate structure
  if (!parsed.rootId || !parsed.nodes || !parsed.settings) {
    throw new Error('Invalid document structure');
  }

  // Ensure all required fields
  const state: DocumentState = {
    rootId: parsed.rootId,
    nodes: parsed.nodes,
    settings: {
      numbering: {
        ...DEFAULT_NUMBERING,
        ...parsed.settings?.numbering,
      },
      pageMode: {
        enabled: parsed.settings?.pageMode?.enabled || false,
        wordsPerPage: parsed.settings?.pageMode?.wordsPerPage || 300,
      },
    },
    labels: parsed.labels || {},
    versions: parsed.versions || [],
  };

  // Rebuild labels map if missing
  if (!state.labels || Object.keys(state.labels).length === 0) {
    state.labels = {};
    Object.values(state.nodes).forEach((node) => {
      if (node.label) {
        state.labels[node.label] = node.id;
      }
    });
  }

  // Renumber
  return computeNumbers(state);
}

