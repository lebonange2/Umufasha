import { DocumentState, DocNode } from '../types';
import { getChildren } from '../tree';
import { updateReferencesInContent } from '../references';

export function exportToPlainText(state: DocumentState): string {
  const rootNodes = getChildren(state, null);
  let output = '';

  function renderNode(node: DocNode, depth: number = 0): void {
    const indent = '  '.repeat(depth);
    
    // Title with number
    let title = '';
    if (node.number && node.numbered !== false) {
      title = `${node.number} ${node.title || ''}`.trim();
    } else {
      title = node.title || '';
    }

    if (title) {
      output += `${indent}${title}\n`;
    }

    // Content with references resolved
    if (node.content) {
      const content = updateReferencesInContent(state, node.content);
      const lines = content.split('\n');
      lines.forEach((line) => {
        output += `${indent}  ${line}\n`;
      });
      output += '\n';
    }

    // Children
    const children = getChildren(state, node.id);
    children.forEach((child) => {
      renderNode(child, depth + 1);
    });
  }

  rootNodes.forEach((node) => {
    renderNode(node);
  });

  return output.trim();
}

