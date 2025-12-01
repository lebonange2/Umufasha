import { DocumentState } from '../types';

export function exportToJSON(state: DocumentState): string {
  return JSON.stringify(state, null, 2);
}

