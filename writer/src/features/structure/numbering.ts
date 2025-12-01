import { DocumentState, NumberingSettings } from './types';
import { computeNumbers } from './tree';

/**
 * Numbering utilities and configuration
 */

export function updateNumberingSettings(
  state: DocumentState,
  settings: Partial<NumberingSettings>
): DocumentState {
  const newSettings = {
    ...state.settings,
    numbering: {
      ...state.settings.numbering,
      ...settings,
    },
  };

  const newState = { ...state, settings: newSettings };
  return computeNumbers(newState);
}

export function toggleNodeNumbering(
  state: DocumentState,
  nodeId: string,
  numbered: boolean
): DocumentState {
  const node = state.nodes[nodeId];
  if (!node) {
    throw new Error(`Node ${nodeId} not found`);
  }

  const newNodes = { ...state.nodes };
  newNodes[nodeId] = {
    ...node,
    numbered,
  };

  const newState = { ...state, nodes: newNodes };
  return computeNumbers(newState);
}

export function getNumberingForNode(
  state: DocumentState,
  nodeId: string
): string | undefined {
  const node = state.nodes[nodeId];
  if (!node) {
    return undefined;
  }

  return node.number;
}

