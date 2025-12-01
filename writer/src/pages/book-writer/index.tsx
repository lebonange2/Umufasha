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

interface ChapterOutline {
  chapter_number: number;
  title: string;
  prompt: string;
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
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate outline');
      }

      const outlineData = await response.json();
      setOutline(outlineData);
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
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate book');
      }

      await loadProjectDetails(selectedProject.id);
      alert('Book generation started! This may take a while. Check back later.');
    } catch (err: any) {
      setError(err.message);
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
                  <div className="flex gap-2">
                    {!outline && (
                      <button
                        onClick={generateOutline}
                        disabled={loading}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                      >
                        Generate Outline
                      </button>
                    )}
                    {outline && selectedProject.status !== 'complete' && (
                      <button
                        onClick={generateBook}
                        disabled={loading}
                        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                      >
                        Generate Book
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
                {/* Outline/Chapters List */}
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

