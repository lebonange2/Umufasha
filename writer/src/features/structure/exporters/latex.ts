import { DocumentState, DocNode } from '../types';
import { getChildren } from '../tree';
import { updateReferencesInContent } from '../references';

export function exportToLaTeX(state: DocumentState): string {
  let output = '\\documentclass[12pt]{book}\n';
  output += '\\usepackage[utf8]{inputenc}\n';
  output += '\\begin{document}\n\n';

  // Check if TOC node exists
  const rootNodes = getChildren(state, null);
  const hasTOC = rootNodes.some((node) => node.kind === 'toc');
  
  if (hasTOC) {
    output += '\\tableofcontents\n\\newpage\n\n';
  }

  function renderNode(node: DocNode): void {
    // LaTeX command based on kind
    const commands: Record<string, string> = {
      part: '\\part',
      chapter: '\\chapter',
      section: '\\section',
      subsection: '\\subsection',
      subsubsection: '\\subsubsection',
    };

    const command = commands[node.kind];
    
    if (command) {
      // Title
      const title = node.title || '';
      if (title) {
        output += `${command}{${escapeLaTeX(title)}}`;
        
        // Label if exists
        if (node.label) {
          output += `\\label{${node.label}}`;
        }
        
        output += '\n';
      }
    }

    // Content with references resolved
    if (node.content) {
      let content = updateReferencesInContent(state, node.content);
      
      // Convert reference patterns to LaTeX \ref{}
      content = content.replace(/\[ref:([^\]]+)\]/g, '\\ref{$1}');
      content = content.replace(/\{\{ref:([^}]+)\}\}/g, '\\ref{$1}');
      
      // Escape LaTeX special characters in content
      content = escapeLaTeXContent(content);
      
      output += content + '\n\n';
    }

    // Children
    const children = getChildren(state, node.id);
    children.forEach((child) => {
      renderNode(child);
    });
  }

  rootNodes.forEach((node) => {
    if (node.kind !== 'toc') {
      renderNode(node);
    }
  });

  output += '\\end{document}\n';
  return output;
}

function escapeLaTeX(text: string): string {
  return text
    .replace(/\\/g, '\\textbackslash{}')
    .replace(/\{/g, '\\{')
    .replace(/\}/g, '\\}')
    .replace(/\$/g, '\\$')
    .replace(/\&/g, '\\&')
    .replace(/\#/g, '\\#')
    .replace(/\^/g, '\\textasciicircum{}')
    .replace(/\_/g, '\\_')
    .replace(/\~/g, '\\textasciitilde{}')
    .replace(/\%/g, '\\%');
}

function escapeLaTeXContent(text: string): string {
  // Less aggressive escaping for content (preserve some formatting)
  return text
    .replace(/\$/g, '\\$')
    .replace(/\&/g, '\\&')
    .replace(/\#/g, '\\#')
    .replace(/\_/g, '\\_')
    .replace(/\{/g, '\\{')
    .replace(/\}/g, '\\}')
    .replace(/\\/g, '\\textbackslash{}');
}

