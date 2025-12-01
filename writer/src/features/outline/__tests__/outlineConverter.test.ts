import { describe, it, expect } from 'vitest';
import { convertOutlineToDocument, normalizeOutlineData } from '../outlineConverter';
import { OutlineData } from '../outlineConverter';

describe('outlineConverter', () => {
  describe('normalizeOutlineData', () => {
    it('should handle outline with title and chapters', () => {
      const data = {
        title: 'Test Book',
        chapters: [
          { title: 'Chapter 1', sections: [] }
        ]
      };
      const result = normalizeOutlineData(data);
      expect(result.title).toBe('Test Book');
      expect(result.chapters).toHaveLength(1);
    });

    it('should handle array of chapters', () => {
      const data = [
        { title: 'Chapter 1', sections: [] }
      ];
      const result = normalizeOutlineData(data);
      expect(result.title).toBe('Untitled Document');
      expect(result.chapters).toHaveLength(1);
    });

    it('should handle object with chapters but no title', () => {
      const data = {
        chapters: [
          { title: 'Chapter 1', sections: [] }
        ]
      };
      const result = normalizeOutlineData(data);
      expect(result.title).toBe('Untitled Document');
      expect(result.chapters).toHaveLength(1);
    });
  });

  describe('convertOutlineToDocument', () => {
    it('should convert a simple outline with chapters', () => {
      const outline: OutlineData = {
        title: 'Test Book',
        chapters: [
          {
            title: 'Chapter 1',
            summary: 'First chapter',
            sections: [
              {
                title: 'Section 1.1',
                beats: ['Beat 1', 'Beat 2']
              }
            ]
          },
          {
            title: 'Chapter 2',
            sections: []
          }
        ]
      };

      const result = convertOutlineToDocument(outline);

      // Should have root TOC node
      expect(result.rootId).toBeDefined();
      expect(result.nodes[result.rootId].kind).toBe('toc');
      expect(result.nodes[result.rootId].title).toBe('Test Book');

      // Should have chapters at root level (parentId: null)
      const chapters = Object.values(result.nodes).filter(n => n.kind === 'chapter');
      expect(chapters).toHaveLength(2);
      
      chapters.forEach(chapter => {
        expect(chapter.parentId).toBeNull();
        expect(chapter.kind).toBe('chapter');
      });

      // Check first chapter
      const chapter1 = chapters.find(c => c.title === 'Chapter 1');
      expect(chapter1).toBeDefined();
      expect(chapter1?.content).toBe('First chapter');

      // Check sections
      const sections = Object.values(result.nodes).filter(n => n.kind === 'section');
      expect(sections).toHaveLength(1);
      
      const section1 = sections[0];
      expect(section1.title).toBe('Section 1.1');
      expect(section1.parentId).toBe(chapter1?.id);
      expect(section1.content).toBe('Beat 1\n\nBeat 2');
    });

    it('should handle empty outline gracefully', () => {
      const outline: OutlineData = {
        title: 'Empty Book',
        chapters: []
      };

      const result = convertOutlineToDocument(outline);

      expect(result.rootId).toBeDefined();
      expect(result.nodes[result.rootId].kind).toBe('toc');
      expect(result.nodes[result.rootId].title).toBe('Empty Book');
      
      const chapters = Object.values(result.nodes).filter(n => n.kind === 'chapter');
      expect(chapters).toHaveLength(0);
    });

    it('should handle chapters with subsections', () => {
      const outline: OutlineData = {
        title: 'Complex Book',
        chapters: [
          {
            title: 'Chapter 1',
            sections: [
              {
                title: 'Section 1.1',
                beats: ['Beat 1'],
                subsections: [
                  {
                    title: 'Subsection 1.1.1',
                    beats: ['Sub-beat 1', 'Sub-beat 2']
                  }
                ]
              }
            ]
          }
        ]
      };

      const result = convertOutlineToDocument(outline);

      const chapters = Object.values(result.nodes).filter(n => n.kind === 'chapter');
      expect(chapters).toHaveLength(1);

      const sections = Object.values(result.nodes).filter(n => n.kind === 'section');
      expect(sections).toHaveLength(1);

      const subsections = Object.values(result.nodes).filter(n => n.kind === 'subsection');
      expect(subsections).toHaveLength(1);

      const subsection = subsections[0];
      expect(subsection.title).toBe('Subsection 1.1.1');
      expect(subsection.content).toBe('Sub-beat 1\n\nSub-beat 2');
      expect(subsection.parentId).toBe(sections[0].id);
    });

    it('should not create chapters as children of TOC', () => {
      const outline: OutlineData = {
        title: 'Test',
        chapters: [
          { title: 'Chapter 1', sections: [] }
        ]
      };

      const result = convertOutlineToDocument(outline);

      const chapters = Object.values(result.nodes).filter(n => n.kind === 'chapter');
      expect(chapters.length).toBeGreaterThan(0);
      
      chapters.forEach(chapter => {
        // Chapters should NOT be children of TOC
        expect(chapter.parentId).not.toBe(result.rootId);
        // Chapters should be at root level
        expect(chapter.parentId).toBeNull();
      });
    });
  });
});

