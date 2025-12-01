import { DocumentState, DocNode } from './types';
import { getChildren } from './tree';

/**
 * Virtual pagination utilities
 */

export interface PageInfo {
  nodeId: string;
  pageNumber: number;
  wordCount: number;
  startWord: number;
  endWord: number;
}

export function computePages(state: DocumentState, chapterId: string): PageInfo[] {
  if (!state.settings.pageMode.enabled) {
    return [];
  }

  const chapter = state.nodes[chapterId];
  if (!chapter || chapter.kind !== 'chapter') {
    return [];
  }

  const pages: PageInfo[] = [];
  const wordsPerPage = state.settings.pageMode.wordsPerPage;
  
  // Collect all text content from chapter and its descendants
  let allText = '';
  
  function collectText(nodeId: string): void {
    const node = state.nodes[nodeId];
    if (!node) return;
    
    if (node.content) {
      allText += node.content + ' ';
    }
    
    const children = getChildren(state, nodeId);
    children.forEach((child) => {
      if (child.kind !== 'page') {
        collectText(child.id);
      }
    });
  }
  
  collectText(chapterId);
  
  const words = allText.trim().split(/\s+/).filter((w) => w.length > 0);
  const totalWords = words.length;
  
  // Create pages
  let currentPage = 1;
  let currentWord = 0;
  
  while (currentWord < totalWords) {
    const pageWords = words.slice(currentWord, currentWord + wordsPerPage);
    const wordCount = pageWords.length;
    
    pages.push({
      nodeId: `${chapterId}_page_${currentPage}`,
      pageNumber: currentPage,
      wordCount,
      startWord: currentWord + 1,
      endWord: currentWord + wordCount,
    });
    
    currentWord += wordCount;
    currentPage++;
  }
  
  return pages;
}

export function getPageCount(state: DocumentState, chapterId: string): number {
  const pages = computePages(state, chapterId);
  return pages.length;
}

export function getWordCount(node: DocNode): number {
  if (!node.content) {
    return 0;
  }
  return node.content.trim().split(/\s+/).filter((w) => w.length > 0).length;
}

export function getTotalWordCount(state: DocumentState, nodeId: string): number {
  const node = state.nodes[nodeId];
  if (!node) {
    return 0;
  }

  let count = getWordCount(node);
  const children = getChildren(state, nodeId);
  
  children.forEach((child) => {
    count += getTotalWordCount(state, child.id);
  });
  
  return count;
}

