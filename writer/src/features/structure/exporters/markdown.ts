import { DocumentState, DocNode } from '../types';
import { getChildren } from '../tree';
import { updateReferencesInContent } from '../references';

export function exportToMarkdown(state: DocumentState): string {
  const rootNodes = getChildren(state, null);
  let output = '';

  function renderNode(node: DocNode, depth: number = 0): void {
    const headingLevel = Math.min(depth + 1, 6);
    const prefix = '#'.repeat(headingLevel);
    
    // Title with number
    let title = '';
    if (node.number && node.numbered !== false) {
      title = `${node.number} ${node.title || ''}`.trim();
    } else {
      title = node.title || '';
    }

    if (title) {
      // Create anchor from title or label
      const anchor = node.label || 
        title.toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '');
      
      output += `${prefix} ${title} {#${anchor}}\n\n`;
    }

    // Content with references resolved
    if (node.content) {
      const content = updateReferencesInContent(state, node.content);
      output += content + '\n\n';
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

