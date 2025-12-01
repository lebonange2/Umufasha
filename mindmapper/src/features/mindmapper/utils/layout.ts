import { MindmapNode } from '../types';

/**
 * Calculate node dimensions based on text content
 */
export function calculateNodeSize(text: string, minWidth: number = 80, minHeight: number = 40): { width: number; height: number } {
  // Simple estimation: ~8px per character width, ~20px per line height
  const lines = text.split('\n');
  const maxLineLength = Math.max(...lines.map(line => line.length), 1);
  const width = Math.max(maxLineLength * 8 + 20, minWidth);
  const height = Math.max(lines.length * 20 + 20, minHeight);
  return { width, height };
}

/**
 * Get all children of a node
 */
export function getChildren(nodes: MindmapNode[], parentId: string | null): MindmapNode[] {
  return nodes.filter(node => node.parentId === parentId);
}

/**
 * Get all descendants of a node (recursive)
 */
export function getDescendants(nodes: MindmapNode[], parentId: string): MindmapNode[] {
  const children = getChildren(nodes, parentId);
  const descendants = [...children];
  for (const child of children) {
    descendants.push(...getDescendants(nodes, child.id));
  }
  return descendants;
}

/**
 * Calculate a radial layout for nodes
 */
export function calculateRadialLayout(
  nodes: MindmapNode[],
  centerX: number,
  centerY: number,
  radius: number = 150
): MindmapNode[] {
  const root = nodes.find(n => n.parentId === null);
  if (!root) return nodes;

  const updated = [...nodes];
  const rootIndex = updated.findIndex(n => n.id === root.id);
  updated[rootIndex] = { ...root, x: centerX, y: centerY };

  const children = getChildren(nodes, root.id);
  const angleStep = (2 * Math.PI) / Math.max(children.length, 1);

  children.forEach((child, index) => {
    const angle = index * angleStep;
    const childIndex = updated.findIndex(n => n.id === child.id);
    updated[childIndex] = {
      ...child,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };

    // Layout grandchildren
    const grandchildren = getChildren(nodes, child.id);
    grandchildren.forEach((grandchild, grandIndex) => {
      const grandAngle = angle + (grandIndex - grandchildren.length / 2) * 0.3;
      const grandIndexInUpdated = updated.findIndex(n => n.id === grandchild.id);
      if (grandIndexInUpdated >= 0) {
        updated[grandIndexInUpdated] = {
          ...grandchild,
          x: centerX + radius * Math.cos(angle) + radius * 0.7 * Math.cos(grandAngle),
          y: centerY + radius * Math.sin(angle) + radius * 0.7 * Math.sin(grandAngle),
        };
      }
    });
  });

  return updated;
}

/**
 * Check if two nodes overlap
 */
export function nodesOverlap(node1: MindmapNode, node2: MindmapNode, padding: number = 10): boolean {
  const w1 = node1.width || 100;
  const h1 = node1.height || 40;
  const w2 = node2.width || 100;
  const h2 = node2.height || 40;

  return !(
    node1.x + w1 / 2 + padding < node2.x - w2 / 2 - padding ||
    node1.x - w1 / 2 - padding > node2.x + w2 / 2 + padding ||
    node1.y + h1 / 2 + padding < node2.y - h2 / 2 - padding ||
    node1.y - h1 / 2 - padding > node2.y + h2 / 2 + padding
  );
}

