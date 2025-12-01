import { Mindmap, MindmapNode } from '../types';

/**
 * Export mindmap as JSON
 */
export function exportAsJSON(mindmap: Mindmap): string {
  return JSON.stringify(mindmap, null, 2);
}

/**
 * Download JSON file
 */
export function downloadJSON(mindmap: Mindmap): void {
  const json = exportAsJSON(mindmap);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${mindmap.title.replace(/[^a-z0-9]/gi, '_')}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export canvas as PNG
 */
export function exportAsPNG(canvas: HTMLCanvasElement, filename: string = 'mindmap.png'): void {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}

/**
 * Export canvas as SVG
 */
export function exportAsSVG(nodes: MindmapNode[], width: number, height: number, filename: string = 'mindmap.svg'): void {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', width.toString());
  svg.setAttribute('height', height.toString());
  svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

  // Draw connections
  nodes.forEach(node => {
    if (node.parentId) {
      const parent = nodes.find(n => n.id === node.parentId);
      if (parent) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', (parent.x + (parent.width || 100) / 2).toString());
        line.setAttribute('y1', (parent.y + (parent.height || 40) / 2).toString());
        line.setAttribute('x2', (node.x + (node.width || 100) / 2).toString());
        line.setAttribute('y2', (node.y + (node.height || 40) / 2).toString());
        line.setAttribute('stroke', '#999');
        line.setAttribute('stroke-width', '2');
        svg.appendChild(line);
      }
    }
  });

  // Draw nodes
  nodes.forEach(node => {
    const w = node.width || 100;
    const h = node.height || 40;
    const x = node.x - w / 2;
    const y = node.y - h / 2;

    if (node.shape === 'pill') {
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x.toString());
      rect.setAttribute('y', y.toString());
      rect.setAttribute('width', w.toString());
      rect.setAttribute('height', h.toString());
      rect.setAttribute('rx', (h / 2).toString());
      rect.setAttribute('ry', (h / 2).toString());
      rect.setAttribute('fill', node.color);
      svg.appendChild(rect);
    } else {
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', x.toString());
      rect.setAttribute('y', y.toString());
      rect.setAttribute('width', w.toString());
      rect.setAttribute('height', h.toString());
      rect.setAttribute('rx', '8');
      rect.setAttribute('fill', node.color);
      svg.appendChild(rect);
    }

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', node.x.toString());
    text.setAttribute('y', (node.y + 5).toString());
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', node.textColor);
    text.setAttribute('font-family', 'Arial, sans-serif');
    text.setAttribute('font-size', '14');
    text.textContent = node.text;
    svg.appendChild(text);
  });

  const svgString = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([svgString], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

