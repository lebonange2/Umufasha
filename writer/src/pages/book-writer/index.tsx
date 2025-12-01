import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface BookProject {
  id: string;
  title: string;
  initial_prompt?: string;
  num_chapters: number;
  status: string;
  created_at: string;
  updated_at: string;
}

interface MainPoint {
  text: string;
}

interface Subsection {
  title: string;
  main_points: MainPoint[];
}

interface Section {
  title: string;
  subsections: Subsection[];
}

interface ChapterOutline {
  chapter_number: number;
  title: string;
  prompt: string;
  sections?: Section[];
}

interface BookOutline {
  id: string;
  project_id: string;
  outline_data: ChapterOutline[];
  created_at: string;
  updated_at: string;
}

interface BookChapter {
  id: string;
  project_id: string;
  chapter_number: number;
  title: string;
  content?: string;
  prompt?: string;
  status: string;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export default function BookWriterPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<BookProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<BookProject | null>(null);
  const [outline, setOutline] = useState<BookOutline | null>(null);
  const [chapters, setChapters] = useState<BookChapter[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<BookChapter | null>(null);
  const [viewMode, setViewMode] = useState<'outline' | 'chapters'>('outline'); // 'outline' or 'chapters'
  const [editingOutline, setEditingOutline] = useState<ChapterOutline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // New project form
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [newProjectPrompt, setNewProjectPrompt] = useState('');
  const [newProjectChapters, setNewProjectChapters] = useState(25);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load project details when selected
  useEffect(() => {
    if (selectedProject) {
      loadProjectDetails(selectedProject.id);
    }
  }, [selectedProject]);

  // Initialize editing outline when outline is loaded and normalize main points format
  useEffect(() => {
    if (outline && outline.outline_data) {
      // Normalize main points - convert strings to objects if needed
      const normalizedOutline = outline.outline_data.map(chapter => ({
        ...chapter,
        sections: (chapter.sections || []).map(section => ({
          ...section,
          subsections: (section.subsections || []).map(subsection => ({
            ...subsection,
            main_points: (subsection.main_points || []).map(mp => 
              typeof mp === 'string' ? { text: mp } : mp
            )
          }))
        }))
      }));
      setEditingOutline(normalizedOutline);
    }
  }, [outline]);

  const loadProjects = async () => {
    try {
      const response = await fetch('/api/book-writer/projects');
      if (!response.ok) throw new Error('Failed to load projects');
      const data = await response.json();
      setProjects(data);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const loadProjectDetails = async (projectId: string) => {
    try {
      // Load outline
      try {
        const outlineResponse = await fetch(`/api/book-writer/projects/${projectId}/outline`);
        if (outlineResponse.ok) {
          const outlineData = await outlineResponse.json();
          setOutline(outlineData);
        }
      } catch (e) {
        // Outline might not exist yet
        setOutline(null);
      }

      // Load chapters
      const chaptersResponse = await fetch(`/api/book-writer/projects/${projectId}/chapters`);
      if (chaptersResponse.ok) {
        const chaptersData = await chaptersResponse.json();
        setChapters(chaptersData);
      }
    } catch (err: any) {
      console.error('Failed to load project details:', err);
    }
  };

  const createProject = async () => {
    if (!newProjectTitle || !newProjectPrompt) {
      setError('Title and prompt are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/book-writer/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newProjectTitle,
          initial_prompt: newProjectPrompt,
          num_chapters: newProjectChapters,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create project');
      }

      const project = await response.json();
      setProjects([...projects, project]);
      setSelectedProject(project);
      setShowNewProject(false);
      setNewProjectTitle('');
      setNewProjectPrompt('');
      setNewProjectChapters(25);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateOutline = async () => {
    if (!selectedProject) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/book-writer/projects/${selectedProject.id}/generate-outline`, {
        method: 'POST',
      });

      if (!response.ok) {
        // Try to parse as JSON first
        let errorMessage = 'Failed to generate outline';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If not JSON, get text
          const text = await response.text();
          if (text.includes('<!DOCTYPE')) {
            errorMessage = `Server error (${response.status}): The server returned an HTML error page. Check server logs.`;
          } else {
            errorMessage = text || errorMessage;
          }
        }
        throw new Error(errorMessage);
      }

      const outlineData = await response.json();
      setOutline(outlineData);
      setEditingOutline([...outlineData.outline_data]);
      setViewMode('outline'); // Switch to outline view after generation
      await loadProjectDetails(selectedProject.id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateBook = async () => {
    if (!selectedProject) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/book-writer/projects/${selectedProject.id}/generate-book`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Try to parse as JSON first
        let errorMessage = 'Failed to generate book';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If not JSON, get text
          const text = await response.text();
          if (text.includes('<!DOCTYPE')) {
            errorMessage = `Server error (${response.status}): The server returned an HTML error page. Check server logs.`;
          } else {
            errorMessage = text || errorMessage;
          }
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      await loadProjectDetails(selectedProject.id);
      alert(`Book generation started! ${result.completed_chapters || 0} chapters completed out of ${result.total_chapters || 0}. This may take a while.`);
    } catch (err: any) {
      console.error('Generate book error:', err);
      setError(err.message || 'Failed to generate book');
    } finally {
      setLoading(false);
    }
  };

  const openChapter = (chapter: BookChapter) => {
    setSelectedChapter(chapter);
  };

  const saveChapter = async (chapterId: string, content: string) => {
    if (!selectedProject) return;

    try {
      const chapter = chapters.find(c => c.id === chapterId);
      if (!chapter) return;

      const response = await fetch(
        `/api/book-writer/projects/${selectedProject.id}/chapters/${chapter.chapter_number}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: content }),
        }
      );

      if (!response.ok) throw new Error('Failed to save chapter');

      await loadProjectDetails(selectedProject.id);
      if (selectedChapter?.id === chapterId) {
        const updated = await response.json();
        setSelectedChapter(updated);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const saveOutline = async () => {
    if (!selectedProject || !outline) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/book-writer/projects/${selectedProject.id}/outline`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingOutline),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to save outline';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          const text = await response.text();
          errorMessage = text || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const updatedOutline = await response.json();
      setOutline(updatedOutline);
      alert('Outline saved successfully!');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const isOutlineComplete = (): boolean => {
    if (!editingOutline || editingOutline.length === 0) {
      return false;
    }

    // Check each chapter has required structure
    for (const chapter of editingOutline) {
      // Must have title
      if (!chapter.title || chapter.title.trim() === '') {
        return false;
      }

      // Must have sections
      if (!chapter.sections || chapter.sections.length === 0) {
        return false;
      }

      // Each section must have subsections
      for (const section of chapter.sections) {
        if (!section.title || section.title.trim() === '') {
          return false;
        }
        if (!section.subsections || section.subsections.length === 0) {
          return false;
        }

        // Each subsection must have main points
        for (const subsection of section.subsections) {
          if (!subsection.title || subsection.title.trim() === '') {
            return false;
          }
          if (!subsection.main_points || subsection.main_points.length === 0) {
            return false;
          }

          // Each main point must have text
          for (const mp of subsection.main_points) {
            const mpText = typeof mp === 'string' ? mp : mp.text;
            if (!mpText || mpText.trim() === '') {
              return false;
            }
          }
        }
      }
    }

    return true;
  };

  const getOutlineValidationMessage = (): string | null => {
    if (!editingOutline || editingOutline.length === 0) {
      return 'Outline is empty';
    }

    const issues: string[] = [];

    editingOutline.forEach((chapter, chIdx) => {
      if (!chapter.title || chapter.title.trim() === '') {
        issues.push(`Chapter ${chIdx + 1}: Missing title`);
      }

      if (!chapter.sections || chapter.sections.length === 0) {
        issues.push(`Chapter ${chIdx + 1}: Missing sections`);
      } else {
        chapter.sections.forEach((section, secIdx) => {
          if (!section.title || section.title.trim() === '') {
            issues.push(`Chapter ${chIdx + 1}, Section ${secIdx + 1}: Missing title`);
          }

          if (!section.subsections || section.subsections.length === 0) {
            issues.push(`Chapter ${chIdx + 1}, Section ${secIdx + 1}: Missing subsections`);
          } else {
            section.subsections.forEach((subsection, subIdx) => {
              if (!subsection.title || subsection.title.trim() === '') {
                issues.push(`Chapter ${chIdx + 1}, Section ${secIdx + 1}, Subsection ${subIdx + 1}: Missing title`);
              }

              if (!subsection.main_points || subsection.main_points.length === 0) {
                issues.push(`Chapter ${chIdx + 1}, Section ${secIdx + 1}, Subsection ${subIdx + 1}: Missing main points`);
              } else {
                subsection.main_points.forEach((mp, mpIdx) => {
                  const mpText = typeof mp === 'string' ? mp : mp.text;
                  if (!mpText || mpText.trim() === '') {
                    issues.push(`Chapter ${chIdx + 1}, Section ${secIdx + 1}, Subsection ${subIdx + 1}, Main Point ${mpIdx + 1}: Empty`);
                  }
                });
              }
            });
          }
        });
      }
    });

    return issues.length > 0 ? issues.join('; ') : null;
  };

  const deleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return;

    try {
      const response = await fetch(`/api/book-writer/projects/${projectId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete project');

      setProjects(projects.filter(p => p.id !== projectId));
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
        setOutline(null);
        setChapters([]);
        setSelectedChapter(null);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Projects List */}
      <div className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Book Projects</h2>
            <button
              onClick={() => setShowNewProject(!showNewProject)}
              className="px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              + New
            </button>
          </div>
          {showNewProject && (
            <div className="mt-2 space-y-2">
              <input
                type="text"
                placeholder="Book Title"
                value={newProjectTitle}
                onChange={(e) => setNewProjectTitle(e.target.value)}
                className="w-full px-2 py-1 text-sm border rounded"
              />
              <textarea
                placeholder="Initial Prompt"
                value={newProjectPrompt}
                onChange={(e) => setNewProjectPrompt(e.target.value)}
                className="w-full px-2 py-1 text-sm border rounded"
                rows={3}
              />
              <input
                type="number"
                placeholder="Number of Chapters"
                value={newProjectChapters}
                onChange={(e) => setNewProjectChapters(parseInt(e.target.value) || 25)}
                className="w-full px-2 py-1 text-sm border rounded"
              />
              <div className="flex gap-2">
                <button
                  onClick={createProject}
                  disabled={loading}
                  className="flex-1 px-2 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Create
                </button>
                <button
                  onClick={() => setShowNewProject(false)}
                  className="px-2 py-1 text-sm bg-gray-300 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
        <div className="flex-1 overflow-y-auto">
          {projects.map((project) => (
            <div
              key={project.id}
              className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                selectedProject?.id === project.id ? 'bg-blue-50' : ''
              }`}
              onClick={() => setSelectedProject(project)}
            >
              <div className="font-medium">{project.title}</div>
              <div className="text-xs text-gray-500">{project.status}</div>
              <div className="text-xs text-gray-400">{project.num_chapters} chapters</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
            {error}
          </div>
        )}

        {selectedProject ? (
          <div className="flex-1 flex">
            {/* Project Details */}
            <div className="flex-1 flex flex-col">
              <div className="p-4 border-b bg-white">
                  <div className="flex items-center justify-between">
                  <div>
                    <h1 className="text-2xl font-bold">{selectedProject.title}</h1>
                    <p className="text-sm text-gray-500">Status: {selectedProject.status}</p>
                  </div>
                  <div className="flex gap-2 items-center">
                    {outline && (
                      <div className="flex gap-1 bg-gray-100 rounded p-1">
                        <button
                          onClick={() => setViewMode('outline')}
                          className={`px-3 py-1 text-sm rounded ${
                            viewMode === 'outline' 
                              ? 'bg-white shadow' 
                              : 'hover:bg-gray-200'
                          }`}
                        >
                          Outline
                        </button>
                        <button
                          onClick={() => setViewMode('chapters')}
                          className={`px-3 py-1 text-sm rounded ${
                            viewMode === 'chapters' 
                              ? 'bg-white shadow' 
                              : 'hover:bg-gray-200'
                          }`}
                        >
                          Chapters
                        </button>
                      </div>
                    )}
                    {!outline && (
                      <button
                        onClick={generateOutline}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                      >
                        Generate Outline
                      </button>
                    )}
                    {outline && viewMode === 'outline' && (
                      <button
                        onClick={saveOutline}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                      >
                        Save Outline
                      </button>
                    )}
                    {outline && viewMode === 'chapters' && selectedProject.status !== 'complete' && (
                      <button
                        onClick={generateBook}
                        disabled={loading || !isOutlineComplete()}
                        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        title={!isOutlineComplete() ? getOutlineValidationMessage() || 'Outline must be complete' : 'Generate the full book'}
                      >
                        Generate Book {!isOutlineComplete() && '(Incomplete)'}
                      </button>
                    )}
                    <button
                      onClick={() => deleteProject(selectedProject.id)}
                      className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => navigate('/')}
                      className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
                    >
                      Back to Writer
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex-1 flex overflow-hidden">
                {viewMode === 'outline' ? (
                  /* Outline Editor */
                  <div className="flex-1 flex flex-col overflow-hidden">
                    <div className="p-4 border-b bg-white">
                      <div className="flex items-center justify-between">
                        <div>
                          <h2 className="text-xl font-semibold">Book Outline</h2>
                          <p className="text-sm text-gray-500">Edit sections, subsections, and main points</p>
                        </div>
                        <div className="text-right">
                          {isOutlineComplete() ? (
                            <div className="text-sm text-green-600 font-semibold">✓ Outline Complete</div>
                          ) : (
                            <div className="text-sm text-orange-600">
                              <div className="font-semibold">⚠ Outline Incomplete</div>
                              <div className="text-xs mt-1 max-w-xs">
                                {getOutlineValidationMessage() || 'Please fill in all required fields'}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4">
                      {editingOutline.length > 0 ? (
                        <OutlineEditor
                          outline={editingOutline}
                          onChange={setEditingOutline}
                        />
                      ) : (
                        <div className="text-center text-gray-500 py-8">
                          No outline data available. Generate an outline first.
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Chapters List */}
                    <div className="w-64 bg-white border-r overflow-y-auto">
                      <div className="p-2 border-b font-semibold">Chapters</div>
                      {outline ? (
                        <div>
                          {outline.outline_data.map((ch) => {
                            const chapter = chapters.find(c => c.chapter_number === ch.chapter_number);
                            return (
                              <div
                                key={ch.chapter_number}
                                className={`p-2 border-b cursor-pointer hover:bg-gray-50 ${
                                  selectedChapter?.chapter_number === ch.chapter_number ? 'bg-blue-50' : ''
                                }`}
                                onClick={() => chapter && openChapter(chapter)}
                              >
                                <div className="font-medium">
                                  Chapter {ch.chapter_number}: {ch.title}
                                </div>
                                {chapter && (
                                  <div className="text-xs text-gray-500">
                                    {chapter.status} • {chapter.word_count} words
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="p-4 text-gray-500 text-sm">
                          No outline yet. Generate an outline first.
                        </div>
                      )}
                    </div>

                    {/* Chapter Editor */}
                    <div className="flex-1 flex flex-col">
                      {selectedChapter ? (
                        <>
                          <div className="p-4 border-b bg-white">
                            <h2 className="text-xl font-semibold">
                              Chapter {selectedChapter.chapter_number}: {selectedChapter.title}
                            </h2>
                          </div>
                          <ChapterEditor
                            chapter={selectedChapter}
                            onSave={(content) => saveChapter(selectedChapter.id, content)}
                          />
                        </>
                      ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-500">
                          Select a chapter to view and edit
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a project or create a new one to get started
          </div>
        )}
      </div>
    </div>
  );
}

function OutlineEditor({ 
  outline, 
  onChange 
}: { 
  outline: ChapterOutline[]; 
  onChange: (outline: ChapterOutline[]) => void;
}) {
  const updateChapter = (index: number, updates: Partial<ChapterOutline>) => {
    const newOutline = [...outline];
    newOutline[index] = { ...newOutline[index], ...updates };
    onChange(newOutline);
  };

  const updateSection = (chapterIndex: number, sectionIndex: number, updates: Partial<Section>) => {
    const newOutline = [...outline];
    if (!newOutline[chapterIndex].sections) {
      newOutline[chapterIndex].sections = [];
    }
    const sections = [...(newOutline[chapterIndex].sections || [])];
    sections[sectionIndex] = { ...sections[sectionIndex], ...updates };
    newOutline[chapterIndex].sections = sections;
    onChange(newOutline);
  };

  const updateSubsection = (
    chapterIndex: number,
    sectionIndex: number,
    subsectionIndex: number,
    updates: Partial<Subsection>
  ) => {
    const newOutline = [...outline];
    if (!newOutline[chapterIndex].sections) return;
    const sections = [...(newOutline[chapterIndex].sections || [])];
    const subsections = [...(sections[sectionIndex].subsections || [])];
    subsections[subsectionIndex] = { ...subsections[subsectionIndex], ...updates };
    sections[sectionIndex].subsections = subsections;
    newOutline[chapterIndex].sections = sections;
    onChange(newOutline);
  };

  const updateMainPoint = (
    chapterIndex: number,
    sectionIndex: number,
    subsectionIndex: number,
    mainPointIndex: number,
    text: string
  ) => {
    const newOutline = [...outline];
    if (!newOutline[chapterIndex].sections) return;
    const sections = [...(newOutline[chapterIndex].sections || [])];
    const subsections = [...(sections[sectionIndex].subsections || [])];
    const mainPoints = [...(subsections[subsectionIndex].main_points || [])];
    mainPoints[mainPointIndex] = { text };
    subsections[subsectionIndex].main_points = mainPoints;
    sections[sectionIndex].subsections = subsections;
    newOutline[chapterIndex].sections = sections;
    onChange(newOutline);
  };

  const addMainPoint = (chapterIndex: number, sectionIndex: number, subsectionIndex: number) => {
    const newOutline = [...outline];
    if (!newOutline[chapterIndex].sections) return;
    const sections = [...(newOutline[chapterIndex].sections || [])];
    const subsections = [...(sections[sectionIndex].subsections || [])];
    if (!subsections[subsectionIndex].main_points) {
      subsections[subsectionIndex].main_points = [];
    }
    subsections[subsectionIndex].main_points.push({ text: '' });
    sections[sectionIndex].subsections = subsections;
    newOutline[chapterIndex].sections = sections;
    onChange(newOutline);
  };

  const removeMainPoint = (
    chapterIndex: number,
    sectionIndex: number,
    subsectionIndex: number,
    mainPointIndex: number
  ) => {
    const newOutline = [...outline];
    if (!newOutline[chapterIndex].sections) return;
    const sections = [...(newOutline[chapterIndex].sections || [])];
    const subsections = [...(sections[sectionIndex].subsections || [])];
    subsections[subsectionIndex].main_points = subsections[subsectionIndex].main_points.filter(
      (_, i) => i !== mainPointIndex
    );
    sections[sectionIndex].subsections = subsections;
    newOutline[chapterIndex].sections = sections;
    onChange(newOutline);
  };

  return (
    <div className="space-y-6">
      {outline.map((chapter, chapterIndex) => (
        <div key={chapterIndex} className="border rounded-lg p-4 bg-white">
          <div className="mb-4">
            <input
              type="text"
              value={chapter.title}
              onChange={(e) => updateChapter(chapterIndex, { title: e.target.value })}
              className="text-xl font-bold w-full border-b-2 border-gray-300 focus:border-blue-500 outline-none pb-1"
              placeholder="Chapter Title"
            />
            <div className="text-sm text-gray-500 mt-1">
              Chapter {chapter.chapter_number}
            </div>
          </div>

          {chapter.sections && chapter.sections.length > 0 ? (
            <div className="space-y-4 ml-4">
              {chapter.sections.map((section, sectionIndex) => (
                <div key={sectionIndex} className="border-l-2 border-blue-200 pl-4">
                  <input
                    type="text"
                    value={section.title}
                    onChange={(e) => updateSection(chapterIndex, sectionIndex, { title: e.target.value })}
                    className="text-lg font-semibold w-full border-b border-gray-200 focus:border-blue-400 outline-none pb-1 mb-2"
                    placeholder="Section Title"
                  />
                  
                  {section.subsections && section.subsections.length > 0 ? (
                    <div className="space-y-3 ml-4">
                      {section.subsections.map((subsection, subsectionIndex) => (
                        <div key={subsectionIndex} className="border-l-2 border-green-200 pl-4">
                          <input
                            type="text"
                            value={subsection.title}
                            onChange={(e) => updateSubsection(chapterIndex, sectionIndex, subsectionIndex, { title: e.target.value })}
                            className="text-md font-medium w-full border-b border-gray-200 focus:border-green-400 outline-none pb-1 mb-2"
                            placeholder="Subsection Title"
                          />
                          
                          <div className="ml-4 space-y-2">
                            <div className="text-xs font-semibold text-gray-600 mb-1">Main Points:</div>
                            {subsection.main_points && subsection.main_points.length > 0 ? (
                              subsection.main_points.map((mp, mpIndex) => (
                                <div key={mpIndex} className="flex items-start gap-2">
                                  <span className="text-gray-400 mt-1">•</span>
                                  <input
                                    type="text"
                                    value={mp.text}
                                    onChange={(e) => updateMainPoint(chapterIndex, sectionIndex, subsectionIndex, mpIndex, e.target.value)}
                                    className="flex-1 text-sm border border-gray-200 rounded px-2 py-1 focus:border-blue-400 outline-none"
                                    placeholder="Main point for paragraph"
                                  />
                                  <button
                                    onClick={() => removeMainPoint(chapterIndex, sectionIndex, subsectionIndex, mpIndex)}
                                    className="text-red-500 hover:text-red-700 text-sm"
                                  >
                                    ×
                                  </button>
                                </div>
                              ))
                            ) : (
                              <div className="text-xs text-gray-400 italic">No main points yet</div>
                            )}
                            <button
                              onClick={() => addMainPoint(chapterIndex, sectionIndex, subsectionIndex)}
                              className="text-xs text-blue-500 hover:text-blue-700 mt-1"
                            >
                              + Add Main Point
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-gray-400 italic ml-4">No subsections</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-400 italic ml-4">No sections defined</div>
          )}
        </div>
      ))}
    </div>
  );
}

function ChapterEditor({ chapter, onSave }: { chapter: BookChapter; onSave: (content: string) => void }) {
  const [content, setContent] = useState(chapter.content || '');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setContent(chapter.content || '');
  }, [chapter]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(content);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="p-2 border-b bg-gray-50 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {content.split(/\s+/).length} words • {content.length} characters
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="flex-1 p-4 font-mono text-sm resize-none outline-none"
        placeholder="Chapter content will appear here..."
      />
    </div>
  );
}

