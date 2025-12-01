import { DocumentState } from './types';
import { getNodePath, getChildren } from './tree';

/**
 * Structure-aware AI prompt builders
 */

export function buildStructureAwareSystemPrompt(): string {
  return `You are a structure-aware book assistant. Respect the document hierarchy (Part/Chapter/Section/Subsection/Subsubsection/Paragraph). 
When continuing text, keep within the current node's scope. When asked to outline, return a tree. 
Do not renumber—leave numbering to the app.`;
}

export function buildOutlineFromDraftPrompt(state: DocumentState): string {
  // Collect all content
  let content = '';
  Object.values(state.nodes).forEach((node) => {
    if (node.content) {
      content += `[${node.kind}${node.title ? `: ${node.title}` : ''}]\n${node.content}\n\n`;
    }
  });

  return `From the current draft text, propose a hierarchical outline with:
- parts[], each with chapters[], each with sections[], optionally subsections[].

Return JSON only:
{
  "parts": [
    {
      "title": "",
      "chapters": [
        {
          "title": "",
          "sections": [
            {
              "title": "",
              "subsections": [
                {"title": ""}
              ]
            }
          ]
        }
      ]
    }
  ]
}

Current draft:
${content}`;
}

export function buildInsertSectionPrompt(
  state: DocumentState,
  nodeId: string
): string {
  const node = state.nodes[nodeId];
  if (!node) {
    return '';
  }

  const path = getNodePath(state, nodeId);
  const siblings = getChildren(state, node.parentId || null);
  
  const context = {
    currentNode: {
      kind: node.kind,
      title: node.title,
      content: node.content?.slice(0, 500),
    },
    parentChain: path.slice(0, -1).map((n) => ({
      kind: n.kind,
      title: n.title,
      number: n.number,
    })),
    siblings: siblings.map((s) => ({
      title: s.title,
      number: s.number,
    })),
  };

  return `Given this node context, propose 3 candidate section titles and a 120–180 word starter paragraph for the selected title. 
Keep scope local; do not repeat earlier content.

Context:
${JSON.stringify(context, null, 2)}

Return JSON:
{
  "titles": ["Title 1", "Title 2", "Title 3"],
  "paragraphs": {
    "Title 1": "120-180 word paragraph...",
    "Title 2": "120-180 word paragraph...",
    "Title 3": "120-180 word paragraph..."
  }
}`;
}

export function buildRetitleAndSummarizePrompt(
  state: DocumentState,
  nodeId: string
): string {
  const node = state.nodes[nodeId];
  if (!node) {
    return '';
  }

  const path = getNodePath(state, nodeId);
  const parent = path.length > 1 ? path[path.length - 2] : null;

  return `Suggest a concise, informative title (<= 60 chars) and a 2–3 sentence summary for this node, matching the parent's theme.

Parent: ${parent ? `${parent.kind} ${parent.number || ''} ${parent.title || ''}` : 'Root'}

Node text:
${node.content || node.title || ''}

Return JSON:
{
  "title": "Suggested title",
  "summary": "2-3 sentence summary"
}`;
}

export function buildCrossReferenceHelperPrompt(
  state: DocumentState,
  userQuery: string
): string {
  // Collect all labeled nodes
  const labeledNodes = Object.entries(state.labels).map(([label, nodeId]) => {
    const node = state.nodes[nodeId];
    return {
      label,
      number: node.number,
      title: node.title,
      kind: node.kind,
    };
  });

  return `User intent: "${userQuery}"
Suggest 3 nodes to cross-reference (by label and computed number), with a 1-sentence rationale each.

Available labeled nodes:
${JSON.stringify(labeledNodes, null, 2)}

Return JSON only:
{
  "suggestions": [
    {
      "label": "label-name",
      "number": "2.3",
      "title": "Node Title",
      "rationale": "Why this reference is relevant"
    }
  ]
}`;
}

