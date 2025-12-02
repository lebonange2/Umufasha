import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface FerrariProject {
  project_id: string;
  title: string | null;
  premise: string;
  current_phase: string;
  status: string;
  output_directory: string;
}

interface PhaseArtifacts {
  book_brief?: any;
  world_dossier?: any;
  character_bible?: any;
  plot_arc?: any;
  outline?: any[];
  draft_chapters?: any;
  revision_report?: any;
  formatted_manuscript?: string;
  launch_package?: any;
}

interface FileInfo {
  json?: { path: string; exists: boolean };
  pdf?: { path: string; exists: boolean };
  zip?: { path: string; exists: boolean };
  chat_log?: { path: string; exists: boolean };
}

const PHASE_NAMES: Record<string, string> = {
  strategy_concept: 'Strategy & Concept',
  early_design: 'Early Design',
  detailed_engineering: 'Detailed Engineering',
  prototypes_testing: 'Prototypes & Testing',
  industrialization_packaging: 'Industrialization & Packaging',
  marketing_launch: 'Marketing & Launch',
  complete: 'Complete'
};

export default function FerrariCompanyPage() {
  const navigate = useNavigate();
  const [project, setProject] = useState<FerrariProject | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentArtifacts, setCurrentArtifacts] = useState<PhaseArtifacts | null>(null);
  const [chatLog, setChatLog] = useState<any[]>([]);
  const [showChatLog, setShowChatLog] = useState(false);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  
  // Form state
  const [title, setTitle] = useState('');
  const [premise, setPremise] = useState('');
  const [wordCount, setWordCount] = useState('');
  const [audience, setAudience] = useState('');
  const [outputDir, setOutputDir] = useState('book_outputs');

  const createProject = async () => {
    if (!premise.trim()) {
      setError('Premise is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/ferrari-company/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim() || null,
          premise: premise.trim(),
          target_word_count: wordCount ? parseInt(wordCount) : null,
          audience: audience.trim() || null,
          output_directory: outputDir.trim() || 'book_outputs'
        })
      });

      // Read response as text first (can only read once)
      const responseText = await response.text();

      if (!response.ok) {
        // Try to parse as JSON
        let errorMessage = 'Failed to create project';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If not JSON, use text
          if (responseText.includes('<!DOCTYPE')) {
            errorMessage = `Server error (${response.status}): The server returned an HTML error page. Check server logs.`;
          } else {
            errorMessage = responseText || errorMessage;
          }
        }
        throw new Error(errorMessage);
      }

      // Parse JSON from text
      const projectData = JSON.parse(responseText);
      setProject(projectData);
    } catch (err: any) {
      console.error('Create project error:', err);
      setError(err.message || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const executePhase = async () => {
    if (!project) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/execute-phase`, {
        method: 'POST'
      });

      // Read response as text first (can only read once)
      const responseText = await response.text();

      if (!response.ok) {
        // Try to parse as JSON
        let errorMessage = 'Failed to execute phase';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If not JSON, use text
          if (responseText.includes('<!DOCTYPE')) {
            errorMessage = `Server error (${response.status}): The server returned an HTML error page. This usually means an internal error occurred. Check server logs.`;
          } else {
            errorMessage = responseText || errorMessage;
          }
        }
        throw new Error(errorMessage);
      }

      // Parse JSON from text
      const result = JSON.parse(responseText);
      setCurrentArtifacts(result.artifacts);
      setChatLog(result.chat_log || []);
      
      // Refresh project status
      await refreshProject();
    } catch (err: any) {
      console.error('Execute phase error:', err);
      setError(err.message || 'Failed to execute phase');
    } finally {
      setLoading(false);
    }
  };

  const makeDecision = async (decision: 'approve' | 'request_changes' | 'stop') => {
    if (!project) return;

    setLoading(true);
    setError(null);
    setCurrentArtifacts(null); // Clear current artifacts

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision })
      });

      // Read response as text first (can only read once)
      const responseText = await response.text();

      if (!response.ok) {
        // Try to parse as JSON
        let errorMessage = 'Failed to process decision';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // If not JSON, use text
          if (responseText.includes('<!DOCTYPE')) {
            errorMessage = `Server error (${response.status}): The server returned an HTML error page. Check server logs.`;
          } else {
            errorMessage = responseText || errorMessage;
          }
        }
        throw new Error(errorMessage);
      }

      // Parse JSON from text
      const result = JSON.parse(responseText);
      
      // Refresh project
      await refreshProject();
      
      // If approved and not complete, execute next phase automatically
      if (decision === 'approve' && result.status !== 'complete') {
        // Auto-execute next phase (same as CLI flow)
        setTimeout(async () => {
          await executePhase();
        }, 1000);
      } else if (result.status === 'complete') {
        // Check for files
        await checkFiles();
      } else if (decision === 'request_changes') {
        // Re-execute phase to show new artifacts
        setTimeout(async () => {
          await executePhase();
        }, 500);
      }
    } catch (err: any) {
      console.error('Decision error:', err);
      setError(err.message || 'Failed to process decision');
    } finally {
      setLoading(false);
    }
  };

  const refreshProject = async () => {
    if (!project) return;

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}`);
      if (response.ok) {
        const responseText = await response.text();
        try {
          const projectData = JSON.parse(responseText);
          setProject(projectData);
        } catch (parseErr) {
          console.error('Failed to parse project data:', parseErr);
        }
      } else {
        // Handle error response
        const responseText = await response.text();
        console.error('Failed to refresh project:', response.status, responseText);
      }
    } catch (err) {
      console.error('Failed to refresh project:', err);
    }
  };

  const checkFiles = async () => {
    if (!project) return;

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/files`);
      if (response.ok) {
        const responseText = await response.text();
        try {
          const data = JSON.parse(responseText);
          setFileInfo(data.files);
        } catch (parseErr) {
          console.error('Failed to parse file info:', parseErr);
        }
      } else {
        // Handle error response
        const responseText = await response.text();
        console.error('Failed to check files:', response.status, responseText);
      }
    } catch (err) {
      console.error('Failed to check files:', err);
    }
  };

  const downloadFile = async (fileType: string) => {
    if (!project) return;

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/download/${fileType}`);
      if (!response.ok) {
        // Try to get error message
        let errorMessage = 'Download failed';
        try {
          const responseText = await response.text();
          try {
            const errorData = JSON.parse(responseText);
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            if (responseText.includes('<!DOCTYPE')) {
              errorMessage = `Server error (${response.status}): The server returned an HTML error page. Check server logs.`;
            } else {
              errorMessage = responseText || errorMessage;
            }
          }
        } catch (e) {
          errorMessage = `Download failed with status ${response.status}`;
        }
        throw new Error(errorMessage);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || `${fileType}.${fileType === 'zip' ? 'zip' : fileType === 'pdf' ? 'pdf' : 'json'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Download error:', err);
      setError(err.message || 'Failed to download file');
    }
  };

  const loadChatLog = async () => {
    if (!project) return;

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/chat-log`);
      if (response.ok) {
        const responseText = await response.text();
        try {
          const data = JSON.parse(responseText);
          setChatLog(data.chat_log || []);
        } catch (parseErr) {
          console.error('Failed to parse chat log:', parseErr);
          setChatLog([]);
        }
      } else {
        // Handle error response
        const responseText = await response.text();
        console.error('Failed to load chat log:', response.status, responseText);
        setChatLog([]);
      }
    } catch (err) {
      console.error('Failed to load chat log:', err);
      setChatLog([]);
    }
  };

  useEffect(() => {
    if (project) {
      loadChatLog();
      if (project.status === 'complete') {
        checkFiles();
      }
    }
  }, [project]);

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-3xl font-bold">Ferrari-Style Book Creation Company</h1>
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
              >
                Back to Writer
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Working Title (optional)</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter book title"
                  className="w-full px-4 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Short Idea/Premise (1-3 sentences) *</label>
                <textarea
                  value={premise}
                  onChange={(e) => setPremise(e.target.value)}
                  placeholder="A man from Earth goes to live on Mars where there is an advanced civilization."
                  rows={4}
                  className="w-full px-4 py-2 border rounded"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Target Word Count (optional)</label>
                  <input
                    type="number"
                    value={wordCount}
                    onChange={(e) => setWordCount(e.target.value)}
                    placeholder="80000"
                    className="w-full px-4 py-2 border rounded"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Target Audience (optional)</label>
                  <input
                    type="text"
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                    placeholder="Science Fiction readers"
                    className="w-full px-4 py-2 border rounded"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Output Directory</label>
                <input
                  type="text"
                  value={outputDir}
                  onChange={(e) => setOutputDir(e.target.value)}
                  placeholder="book_outputs"
                  className="w-full px-4 py-2 border rounded"
                />
              </div>

              {error && (
                <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
                  {error}
                </div>
              )}

              <button
                onClick={createProject}
                disabled={loading || !premise.trim()}
                className="w-full px-6 py-3 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentPhaseName = PHASE_NAMES[project.current_phase] || project.current_phase;
  const isComplete = project.status === 'complete';
  const needsExecution = !isComplete && !currentArtifacts;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold">{project.title || 'Untitled Book'}</h1>
              <p className="text-gray-600 mt-2">{project.premise}</p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
            >
              Back to Writer
            </button>
          </div>

          <div className="flex items-center gap-4 mb-4">
            <div className="px-4 py-2 bg-blue-100 rounded">
              <span className="font-semibold">Status:</span> {project.status}
            </div>
            <div className="px-4 py-2 bg-green-100 rounded">
              <span className="font-semibold">Current Phase:</span> {currentPhaseName}
            </div>
          </div>

          {error && (
            <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
              {error}
            </div>
          )}

          {isComplete && fileInfo && (
            <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4">
              <h3 className="font-bold mb-2">✓ Book Generation Complete!</h3>
              <div className="flex gap-2 flex-wrap">
                {fileInfo.zip?.exists && (
                  <button
                    onClick={() => downloadFile('zip')}
                    className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
                  >
                    📦 Download Complete Archive (ZIP)
                  </button>
                )}
                {fileInfo.json?.exists && (
                  <button
                    onClick={() => downloadFile('json')}
                    className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
                  >
                    📥 Download JSON Package
                  </button>
                )}
                {fileInfo.pdf?.exists && (
                  <button
                    onClick={() => downloadFile('pdf')}
                    className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                  >
                    📄 Download PDF Book
                  </button>
                )}
                {fileInfo.chat_log?.exists && (
                  <button
                    onClick={() => downloadFile('chat-log')}
                    className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                  >
                    💬 Download Chat Log
                  </button>
                )}
              </div>
            </div>
          )}

          {needsExecution && (
            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="mb-2 font-semibold">Ready to execute: <strong>{currentPhaseName}</strong></p>
                  <p className="text-sm text-gray-600">Click to start this phase of the book creation pipeline</p>
                </div>
                <button
                  onClick={executePhase}
                  disabled={loading}
                  className="px-6 py-3 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 font-semibold"
                >
                  {loading ? 'Executing...' : '▶ Execute Phase'}
                </button>
              </div>
            </div>
          )}

          {loading && !currentArtifacts && (
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
              <p className="font-semibold">Processing phase...</p>
              <p className="text-sm text-gray-600 mt-1">This may take a few moments. Please wait.</p>
            </div>
          )}

          {currentArtifacts && !isComplete && (
            <div className="bg-white border-2 border-blue-200 rounded-lg p-6 mb-4 shadow-md">
              <div className="mb-4">
                <h3 className="text-xl font-bold mb-2">Phase Results: {currentPhaseName}</h3>
                <p className="text-gray-600 mb-4">Review the generated content below and make your decision.</p>
              </div>
              
              <div className="mb-4">
                <div className="bg-gray-50 border rounded p-4 max-h-96 overflow-auto">
                  <pre className="text-sm whitespace-pre-wrap">
                    {JSON.stringify(currentArtifacts, null, 2)}
                  </pre>
                </div>
              </div>
              
              <div className="border-t pt-4">
                <p className="text-sm font-semibold mb-3">Your Decision:</p>
                <div className="flex gap-3">
                  <button
                    onClick={() => makeDecision('approve')}
                    disabled={loading}
                    className="flex-1 px-6 py-3 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 font-semibold shadow"
                  >
                    ✓ Approve & Continue to Next Phase
                  </button>
                  <button
                    onClick={() => makeDecision('request_changes')}
                    disabled={loading}
                    className="px-6 py-3 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50 font-semibold shadow"
                  >
                    ↻ Request Changes
                  </button>
                  <button
                    onClick={() => makeDecision('stop')}
                    disabled={loading}
                    className="px-6 py-3 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 font-semibold shadow"
                  >
                    ✗ Stop Project
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="mt-4">
            <button
              onClick={() => setShowChatLog(!showChatLog)}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              {showChatLog ? 'Hide' : 'Show'} Chat Log
            </button>
          </div>

          {showChatLog && (
            <div className="mt-4 bg-gray-50 border rounded p-4 max-h-96 overflow-auto">
              <h3 className="font-bold mb-2">Agent Chat Log</h3>
              {chatLog.length === 0 ? (
                <p className="text-gray-500">No messages yet</p>
              ) : (
                <div className="space-y-2">
                  {chatLog.map((msg, idx) => (
                    <div key={idx} className="bg-white p-2 rounded text-sm">
                      <div className="font-semibold">
                        {msg.from_agent} → {msg.to_agent}
                      </div>
                      <div className="text-gray-600 text-xs">{msg.timestamp}</div>
                      <div className="mt-1">{msg.content.substring(0, 200)}...</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

