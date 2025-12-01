import { DocumentState, DEFAULT_NUMBERING, DocNode } from '../structure/types';
import { computeNumbers } from '../structure/tree';

export interface OutlineChapter {
  title: string;
  summary?: string;
  sections?: OutlineSection[];
}

export interface OutlineSection {
  title: string;
  beats?: string[];
  subsections?: OutlineSection[];
}

export interface OutlineData {
  title?: string;
  chapters: OutlineChapter[];
}

// Handle both formats: { title: "...", chapters: [...] } and { chapters: [...] }
export function normalizeOutlineData(data: any): OutlineData {
  // If data is an object with a title property at root level
  if (data.title && data.chapters) {
    return data as OutlineData;
  }
  
  // If data is just the chapters array or has a different structure
  if (Array.isArray(data)) {
    return {
      title: 'Untitled Document',
      chapters: data,
    };
  }
  
  // If it's an object but title might be elsewhere
  if (data.chapters) {
    return {
      title: data.title || 'Untitled Document',
      chapters: data.chapters,
    };
  }
  
  // Fallback
  return {
    title: 'Untitled Document',
    chapters: [],
  };
}

/**
 * Converts an outline structure to a DocumentState
 */
export function convertOutlineToDocument(outlineData: OutlineData | any): DocumentState {
  // Normalize the outline data to handle different formats
  const outline = normalizeOutlineData(outlineData);
  
  // Validate that we have chapters to convert
  if (!outline.chapters || outline.chapters.length === 0) {
    console.warn('No chapters to convert in outline:', outline);
    // Return a minimal valid state
    const rootId = `root_${Date.now()}`;
    return {
      rootId,
      nodes: {
        [rootId]: {
          id: rootId,
          kind: 'toc',
          parentId: null,
          order: 0,
          title: outline.title || 'Untitled Document',
        },
      },
      settings: {
        numbering: DEFAULT_NUMBERING,
        pageMode: {
          enabled: false,
          wordsPerPage: 300,
        },
      },
      labels: {},
      versions: [],
    };
  }

  // Create initial state with a TOC node
  const rootId = `root_${Date.now()}`;
  const state: DocumentState = {
    rootId,
    nodes: {
      [rootId]: {
        id: rootId,
        kind: 'toc',
        parentId: null,
        order: 0,
        title: outline.title || 'Untitled Document',
      },
    },
    settings: {
      numbering: DEFAULT_NUMBERING,
      pageMode: {
        enabled: false,
        wordsPerPage: 300,
      },
    },
    labels: {},
    versions: [],
  };

  // Optimized conversion: Build all nodes first, then compute numbers once at the end
  // This avoids calling computeNumbers for every single node creation
  const nodes: Record<string, DocNode> = { ...state.nodes };
  let chapterOrder = 0;

  // Create chapters at root level (parentId: null) since TOC cannot have children
  outline.chapters.forEach((chapter) => {
    const chapterId = `chapter_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${chapterOrder}`;
    
    nodes[chapterId] = {
      id: chapterId,
      kind: 'chapter',
      parentId: null,
      order: chapterOrder,
      title: chapter.title,
      content: chapter.summary,
      numbered: true,
    };

    let sectionOrder = 0;
    
    // Create sections
    if (chapter.sections) {
      chapter.sections.forEach((section) => {
        const sectionId = `section_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${chapterOrder}_${sectionOrder}`;
        
        nodes[sectionId] = {
          id: sectionId,
          kind: 'section',
          parentId: chapterId,
          order: sectionOrder,
          title: section.title,
          content: section.beats && section.beats.length > 0 ? section.beats.join('\n\n') : undefined,
          numbered: true,
        };

        let subsectionOrder = 0;
        
        // Create subsections if they exist
        if (section.subsections) {
          section.subsections.forEach((subsection) => {
            const subId = `subsection_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${chapterOrder}_${sectionOrder}_${subsectionOrder}`;
            
            nodes[subId] = {
              id: subId,
              kind: 'subsection',
              parentId: sectionId,
              order: subsectionOrder,
              title: subsection.title,
              content: subsection.beats && subsection.beats.length > 0 ? subsection.beats.join('\n\n') : undefined,
              numbered: true,
            };
            
            subsectionOrder++;
          });
        }
        
        sectionOrder++;
      });
    }
    
    chapterOrder++;
  });

  // Create state with all nodes
  const finalState: DocumentState = {
    ...state,
    nodes,
  };

  // Compute numbers once at the end (much more efficient)
  return computeNumbers(finalState);
}

