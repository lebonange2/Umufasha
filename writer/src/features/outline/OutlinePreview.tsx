import { useState } from 'react';

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
  title: string;
  chapters: OutlineChapter[];
}

interface OutlinePreviewProps {
  outline: OutlineData;
  onApprove: (outline: OutlineData) => void;
  onCancel?: () => void;
  isApproving?: boolean;
}

export default function OutlinePreview({ outline, onApprove, onCancel, isApproving = false }: OutlinePreviewProps) {
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleChapter = (index: number) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const toggleSection = (chapterIndex: number, sectionIndex: number) => {
    const key = `${chapterIndex}-${sectionIndex}`;
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const handleApprove = () => {
    console.log('Approve button clicked');
    console.log('Outline to approve:', outline);
    
    if (!outline || !outline.chapters || outline.chapters.length === 0) {
      console.warn('Cannot approve: outline is empty');
      alert('Cannot approve an empty outline. Please generate an outline with at least one chapter first.');
      return;
    }
    
    try {
      // Call onApprove - it may be async but we don't need to await it
      onApprove(outline);
    } catch (error: any) {
      console.error('Error in handleApprove:', error);
      alert(`Error approving outline: ${error?.message || error || 'Unknown error'}. Please check the console for details.`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{outline.title}</h1>
          <p className="text-gray-600">Review your outline structure before converting to document format</p>
        </div>

        {/* Outline Tree */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Outline Structure</h2>
          
          {outline.chapters.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 text-lg mb-2">No chapters found in this outline.</p>
              <p className="text-gray-400 text-sm">The AI may not have generated a valid outline structure. Please check the browser console for details and try generating again.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {outline.chapters.map((chapter, chapterIndex) => (
              <div key={chapterIndex} className="border-l-2 border-blue-200 pl-4">
                {/* Chapter */}
                <div className="flex items-start gap-3 mb-2">
                  <button
                    onClick={() => toggleChapter(chapterIndex)}
                    className="mt-1 text-blue-600 hover:text-blue-800"
                    aria-label={expandedChapters.has(chapterIndex) ? 'Collapse' : 'Expand'}
                  >
                    {expandedChapters.has(chapterIndex) ? '▼' : '▶'}
                  </button>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Chapter {chapterIndex + 1}: {chapter.title}
                    </h3>
                    {chapter.summary && (
                      <p className="text-sm text-gray-600 mt-1">{chapter.summary}</p>
                    )}
                  </div>
                </div>

                {/* Sections */}
                {expandedChapters.has(chapterIndex) && chapter.sections && (
                  <div className="ml-8 mt-2 space-y-3">
                    {chapter.sections.map((section, sectionIndex) => (
                      <div key={sectionIndex} className="border-l-2 border-green-200 pl-4">
                        <div className="flex items-start gap-3 mb-2">
                          <button
                            onClick={() => toggleSection(chapterIndex, sectionIndex)}
                            className="mt-1 text-green-600 hover:text-green-800"
                            aria-label={expandedSections.has(`${chapterIndex}-${sectionIndex}`) ? 'Collapse' : 'Expand'}
                          >
                            {expandedSections.has(`${chapterIndex}-${sectionIndex}`) ? '▼' : '▶'}
                          </button>
                          <div className="flex-1">
                            <h4 className="text-base font-medium text-gray-800">
                              {section.title}
                            </h4>
                          </div>
                        </div>

                        {/* Beats */}
                        {expandedSections.has(`${chapterIndex}-${sectionIndex}`) && section.beats && (
                          <div className="ml-8 mt-2 space-y-2">
                            {section.beats.map((beat, beatIndex) => (
                              <div key={beatIndex} className="flex items-start gap-2">
                                <span className="text-gray-400 mt-1">•</span>
                                <p className="text-sm text-gray-700 flex-1">{beat}</p>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Subsections */}
                        {section.subsections && section.subsections.length > 0 && (
                          <div className="ml-8 mt-2 space-y-2">
                            {section.subsections.map((subsection, subIndex) => (
                              <div key={subIndex} className="border-l-2 border-yellow-200 pl-3">
                                <h5 className="text-sm font-medium text-gray-700 mb-1">
                                  {subsection.title}
                                </h5>
                                {subsection.beats && (
                                  <div className="ml-4 space-y-1">
                                    {subsection.beats.map((beat, beatIndex) => (
                                      <div key={beatIndex} className="flex items-start gap-2">
                                        <span className="text-gray-400 text-xs mt-1">◦</span>
                                        <p className="text-xs text-gray-600 flex-1">{beat}</p>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{outline.chapters.length}</div>
              <div className="text-sm text-gray-600">Chapters</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {outline.chapters.reduce((sum, ch) => sum + (ch.sections?.length || 0), 0)}
              </div>
              <div className="text-sm text-gray-600">Sections</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {outline.chapters.reduce((sum, ch) => 
                  sum + (ch.sections?.reduce((s, sec) => s + (sec.beats?.length || 0), 0) || 0), 0
                )}
              </div>
              <div className="text-sm text-gray-600">Beats</div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 justify-end">
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleApprove}
            disabled={outline.chapters.length === 0 || isApproving}
            className={`px-6 py-2 rounded-lg transition-colors font-medium ${
              outline.chapters.length === 0 || isApproving
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
            title={
              outline.chapters.length === 0 
                ? 'Cannot approve an empty outline' 
                : isApproving 
                ? 'Converting outline...' 
                : 'Convert outline to document structure'
            }
          >
            {isApproving ? 'Converting...' : 'Approve & Convert to Document'}
          </button>
        </div>
      </div>
    </div>
  );
}

