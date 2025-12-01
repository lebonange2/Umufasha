export type NodeShape = 'rect' | 'pill';

export interface MindmapNode {
  id: string;
  parentId: string | null;
  x: number;
  y: number;
  text: string;
  color: string;
  textColor: string;
  shape: NodeShape;
  width?: number | null;
  height?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface Mindmap {
  id: string;
  title: string;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
  nodes: MindmapNode[];
}

export interface MindmapListItem {
  id: string;
  title: string;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
  node_count: number;
}

export interface ViewState {
  x: number;
  y: number;
  zoom: number;
}

export interface HistoryState {
  mindmaps: Mindmap[];
  currentIndex: number;
}

