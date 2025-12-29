import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import EmbeddedGraph from '../../components/EmbeddedGraph';

interface BookPublishingHouseProject {
  project_id: string;
  title: string | null;
  premise: string;
  current_phase: string;
  status: string;
  output_directory: string;
  reference_documents?: string[];
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

export default function BookPublishingHousePage() {
  const navigate = useNavigate();
  const [project, setProject] = useState<BookPublishingHouseProject | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentArtifacts, setCurrentArtifacts] = useState<PhaseArtifacts | null>(null);
  const [editableArtifactsJson, setEditableArtifactsJson] = useState<string>('');
  const [jsonParseError, setJsonParseError] = useState<string | null>(null);
  const [chatLog, setChatLog] = useState<any[]>([]);
  const [showChatLog, setShowChatLog] = useState(false);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
  const [previousProjects, setPreviousProjects] = useState<any[]>([]);
  const [showPreviousProjects, setShowPreviousProjects] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [showGraph, setShowGraph] = useState(true); // Show graph by default
  const [graphKey, setGraphKey] = useState(0); // Force graph refresh
  
  // Form state
  const [title, setTitle] = useState('');
  const [premise, setPremise] = useState('');
  const [wordCount, setWordCount] = useState('');
  const [audience, setAudience] = useState('');
  const [outputDir, setOutputDir] = useState('book_outputs');
  const [model, setModel] = useState('qwen3:30b'); // Model selection for worker agents
  const [ceoModel, setCeoModel] = useState('qwen3:30b'); // Model selection for CEO/manager agents
  const [attachedDocuments, setAttachedDocuments] = useState<File[]>([]);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileSelection = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const newFiles = Array.from(event.target.files);
      // Filter to only PDF and TXT files
      const validFiles = newFiles.filter(file => {
        const isPDF = file.type.includes('pdf') || file.name.endsWith('.pdf');
        const isTXT = file.type.includes('text/plain') || file.name.endsWith('.txt');
        return isPDF || isTXT;
      });
      
      if (validFiles.length !== newFiles.length) {
        alert('Some files were skipped. Only PDF and TXT files are allowed.');
      }
      
      // Check file sizes
      const oversizedFiles = validFiles.filter(file => file.size > 50 * 1024 * 1024);
      if (oversizedFiles.length > 0) {
        alert(`Some files are too large (max 50MB): ${oversizedFiles.map(f => f.name).join(', ')}`);
        const sizedFiles = validFiles.filter(file => file.size <= 50 * 1024 * 1024);
        setAttachedDocuments(prev => [...prev, ...sizedFiles]);
      } else {
        setAttachedDocuments(prev => [...prev, ...validFiles]);
      }
    }
  };

  const uploadDocuments = async (files: File[]): Promise<string[]> => {
    if (files.length === 0) return [];

    setUploadingDocs(true);
    const uploadedDocIds: string[] = [];

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/writer/documents/upload', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (data.success) {
          uploadedDocIds.push(data.document.id);
        } else {
          alert(`Failed to upload "${file.name}": ${data.error || 'Unknown error'}`);
        }
      }

      return uploadedDocIds;
    } catch (error: any) {
      console.error('Document upload error:', error);
      alert('Failed to upload documents: ' + error.message);
      return [];
    } finally {
      setUploadingDocs(false);
    }
  };

  const removeDocument = (index: number) => {
    setAttachedDocuments(prev => prev.filter((_, i) => i !== index));
  };

  const createProject = async () => {
    if (!premise.trim()) {
      setError('Premise is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Upload documents first if any
      let referenceDocumentIds: string[] = [];
      if (attachedDocuments.length > 0) {
        referenceDocumentIds = await uploadDocuments(attachedDocuments);
      }

      const response = await fetch('/api/ferrari-company/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim() || null,
          premise: premise.trim(),
          target_word_count: wordCount ? parseInt(wordCount) : null,
          audience: audience.trim() || null,
          output_directory: outputDir.trim() || 'book_outputs',
          reference_documents: referenceDocumentIds.length > 0 ? referenceDocumentIds : null,
          model: model,
          ceo_model: ceoModel !== model ? ceoModel : null
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
      // Start phase execution (returns immediately)
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/execute-phase`, {
        method: 'POST'
      });

      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = 'Failed to start phase execution';
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
        throw new Error(errorMessage);
      }

      const result = JSON.parse(responseText);
      
      // If already running, start polling
      if (result.status === 'running' || result.status === 'started') {
        // Start polling for status
        pollPhaseStatus();
      } else {
        // Shouldn't happen, but handle it
        setLoading(false);
      }
    } catch (err: any) {
      console.error('Execute phase error:', err);
      setError(err.message || 'Failed to execute phase');
      setLoading(false);
    }
  };

  const pollPhaseStatus = async () => {
    if (!project) return;

    // Poll indefinitely until phase completes or fails (no timeout)
    // The phase will complete when the server finishes processing
    const poll = async () => {
      try {
        // Fetch without timeout - let it run indefinitely
        const controller = new AbortController();
        const response = await fetch(`/api/ferrari-company/projects/${project!.project_id}/phase-status`, {
          signal: controller.signal,
          // No timeout - let the request complete naturally
        });
        const responseText = await response.text();

        if (!response.ok) {
          // Try to parse error
          let errorMessage = 'Failed to get phase status';
          try {
            const errorData = JSON.parse(responseText);
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            errorMessage = responseText || errorMessage;
          }
          // Don't throw for non-critical errors - just log and continue polling
          if (response.status === 404) {
            console.error('Project not found, stopping poll');
            setError(errorMessage);
            setLoading(false);
            return;
          }
          // For other errors, log but continue polling (might be transient)
          console.warn('Phase status check error (will retry):', errorMessage);
          setTimeout(poll, 2000); // Retry after 2 seconds
          return;
        }

        const status = JSON.parse(responseText);

        if (status.status === 'completed') {
          // Phase completed!
          setCurrentArtifacts(status.artifacts);
          // Initialize editable JSON with formatted artifacts
          setEditableArtifactsJson(JSON.stringify(status.artifacts, null, 2));
          setJsonParseError(null);
          setChatLog(status.chat_log || []);
          setLoading(false);
          await refreshProject();
          // Sync graph after phase completion
          await syncGraphAfterPhase();
          // Force graph refresh
          setGraphKey(prev => prev + 1);
        } else if (status.status === 'failed') {
          setError(status.error || 'Phase execution failed');
          setLoading(false);
        } else if (status.status === 'running') {
          // Still running, continue polling indefinitely
          // Poll again after 1 second
          setTimeout(poll, 1000);
        } else {
          // Not started or unknown - continue polling in case it starts
          console.log('Phase status unknown, continuing to poll...');
          setTimeout(poll, 2000); // Poll again after 2 seconds
        }
      } catch (err: any) {
        console.error('Poll phase status error:', err);
        // Don't stop polling on transient errors - retry after a delay
        // Only stop if it's a critical error (like 404)
        if (err.message && err.message.includes('404')) {
          setError(err.message || 'Project not found');
          setLoading(false);
        } else {
          // Transient error - retry after 3 seconds
          console.warn('Transient error during polling, will retry:', err.message);
          setTimeout(poll, 3000);
        }
      }
    };

    // Start polling
    poll();
  };

  const handleJsonChange = (value: string) => {
    setEditableArtifactsJson(value);
    // Try to parse JSON to validate
    try {
      JSON.parse(value);
      setJsonParseError(null);
    } catch (e: any) {
      setJsonParseError(e.message || 'Invalid JSON');
    }
  };

  const getEditedArtifacts = (): PhaseArtifacts | null => {
    if (!editableArtifactsJson.trim()) return currentArtifacts;
    
    try {
      const parsed = JSON.parse(editableArtifactsJson);
      return parsed as PhaseArtifacts;
    } catch (e) {
      // If JSON is invalid, return original artifacts
      return currentArtifacts;
    }
  };

  const makeDecision = async (decision: 'approve' | 'request_changes' | 'stop') => {
    if (!project) return;

    // Validate JSON before proceeding
    if (jsonParseError) {
      setError(`Invalid JSON: ${jsonParseError}. Please fix the JSON before proceeding.`);
      return;
    }

    setLoading(true);
    setError(null);
    
    setCurrentArtifacts(null); // Clear current artifacts
    setEditableArtifactsJson(''); // Clear editable JSON

    try {
      // Get edited artifacts if user made changes
      const artifactsToUse = getEditedArtifacts();
      const hasChanges = artifactsToUse && JSON.stringify(artifactsToUse) !== JSON.stringify(currentArtifacts);
      
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          decision,
          modified_artifacts: hasChanges ? artifactsToUse : null
        })
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
      
      // Sync graph after decision
      await syncGraphAfterPhase();
      setGraphKey(prev => prev + 1);
      
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

  const syncGraphAfterPhase = async () => {
    if (!project) return;
    
    try {
      // Trigger graph sync on backend
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/sync-graph`, {
        method: 'POST',
      });
      if (response.ok) {
        console.log('Graph synced successfully');
      } else {
        console.warn('Graph sync failed, but continuing');
      }
    } catch (err) {
      console.warn('Graph sync error (non-critical):', err);
    }
  };

  const fetchPreviousProjects = async () => {
    setLoadingProjects(true);
    setError(null);
    try {
      const response = await fetch('/api/ferrari-company/projects');
      if (response.ok) {
        const responseText = await response.text();
        try {
          const data = JSON.parse(responseText);
          const projects = data.projects || [];
          setPreviousProjects(projects);
          // Automatically show the list if there are projects, or show it anyway so user can see "No projects" message
          setShowPreviousProjects(true);
        } catch (parseErr) {
          console.error('Failed to parse projects list:', parseErr);
          setError('Failed to load previous projects');
        }
      } else {
        const responseText = await response.text();
        console.error('Failed to fetch projects:', response.status, responseText);
        setError('Failed to load previous projects');
      }
    } catch (err) {
      console.error('Failed to fetch projects:', err);
      setError('Failed to load previous projects');
    } finally {
      setLoadingProjects(false);
    }
  };

  const resumeProject = async (projectId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/ferrari-company/projects/${projectId}`);
      if (response.ok) {
        const responseText = await response.text();
        try {
          const projectData = JSON.parse(responseText);
          setProject(projectData);
          setShowPreviousProjects(false);
          // Refresh phase status if in progress
          if (projectData.status === 'in_progress') {
            await pollPhaseStatus();
          }
        } catch (parseErr) {
          console.error('Failed to parse project data:', parseErr);
          setError('Failed to load project');
        }
      } else {
        const responseText = await response.text();
        console.error('Failed to load project:', response.status, responseText);
        setError('Failed to load project');
      }
    } catch (err: any) {
      console.error('Failed to resume project:', err);
      setError(err.message || 'Failed to resume project');
    } finally {
      setLoading(false);
    }
  };

  const downloadProgressReport = async () => {
    if (!project) return;

    try {
      const response = await fetch(`/api/ferrari-company/projects/${project.project_id}/progress-report`);
      if (!response.ok) {
        const responseText = await response.text();
        let errorMessage = 'Download failed';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          errorMessage = responseText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // Get the blob and create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `progress_report_${project.project_id}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Download progress report error:', err);
      setError(err.message || 'Failed to download progress report');
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
    // Check for project ID in URL params
    const params = new URLSearchParams(window.location.search);
    const projectId = params.get('project_id');
    if (projectId && !project) {
      // Load existing project
      resumeProject(projectId);
    }
  }, []);

  useEffect(() => {
    // Fetch previous projects on mount if no project is loaded
    if (!project) {
      fetchPreviousProjects();
    }
  }, []);

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
              <h1 className="text-3xl font-bold">Book Publishing House</h1>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    if (showPreviousProjects) {
                      setShowPreviousProjects(false);
                    } else {
                      fetchPreviousProjects();
                    }
                  }}
                  disabled={loadingProjects}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {loadingProjects ? 'Loading...' : showPreviousProjects ? '✕ Hide Projects' : '📚 View Previous Projects'}
                </button>
                <button
                  onClick={() => navigate('/')}
                  className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
                >
                  Back to Writer
                </button>
              </div>
            </div>

            {showPreviousProjects && (
              <div className="mb-6 bg-white border-2 border-blue-200 rounded-lg p-6 shadow-md">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold text-gray-800">Previous Projects</h2>
                  <button
                    onClick={() => setShowPreviousProjects(false)}
                    className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm"
                  >
                    ✕ Close
                  </button>
                </div>
                {loadingProjects ? (
                  <p className="text-gray-500 text-center py-4">Loading projects...</p>
                ) : previousProjects.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 text-lg mb-2">No previous projects found.</p>
                    <p className="text-gray-400 text-sm">Create a new project to get started!</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {previousProjects.map((proj) => (
                      <div
                        key={proj.project_id}
                        className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:shadow-md bg-white transition-all"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg text-gray-800 mb-1">
                              {proj.title || 'Untitled Book'}
                            </h3>
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                              {proj.premise}
                            </p>
                            <div className="mt-3 flex flex-wrap gap-4 text-xs">
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                Status: <strong>{proj.status}</strong>
                              </span>
                              <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                                Phase: <strong>{PHASE_NAMES[proj.current_phase] || proj.current_phase}</strong>
                              </span>
                              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                                Created: <strong>{new Date(proj.created_at).toLocaleDateString()}</strong>
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <button
                              onClick={() => resumeProject(proj.project_id)}
                              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm font-semibold shadow"
                            >
                              ▶ Resume
                            </button>
                            <a
                              href={`/api/ferrari-company/projects/${proj.project_id}/progress-report`}
                              download
                              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm inline-block text-center font-semibold shadow"
                            >
                              📄 Report
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

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
                <label className="block text-sm font-medium mb-2">Book Premise/Story Idea *</label>
                <textarea
                  value={premise}
                  onChange={(e) => setPremise(e.target.value)}
                  placeholder="Enter your book premise, story idea, or detailed synopsis. You can write as much as you need to describe your story concept, characters, world, plot points, themes, or any other relevant details..."
                  rows={12}
                  className="w-full px-4 py-2 border rounded resize-y"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Provide a detailed description of your book idea. This can be as long as needed.</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Reference Documents (optional)</label>
                <p className="text-xs text-gray-500 mb-2">Attach PDF or TXT files for story reference, research materials, or existing drafts.</p>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,application/pdf,text/plain"
                    onChange={handleFileSelection}
                    className="hidden"
                  />
                  <div className="flex items-center gap-4">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingDocs}
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                    >
                      {uploadingDocs ? 'Uploading...' : '📎 Attach Documents'}
                    </button>
                    <span className="text-sm text-gray-600">
                      {attachedDocuments.length > 0 
                        ? `${attachedDocuments.length} file(s) selected`
                        : 'No files selected'}
                    </span>
                  </div>
                  {attachedDocuments.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {attachedDocuments.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                          <span className="text-sm text-gray-700">
                            📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                          <button
                            type="button"
                            onClick={() => removeDocument(index)}
                            className="text-red-500 hover:text-red-700 text-sm"
                          >
                            ✕ Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Worker Agents Model *</label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-4 py-2 border rounded"
                  >
                    <option value="qwen3:30b">Qwen3 30B (Recommended - Higher Quality)</option>
                    <option value="llama3:latest">Llama 3 Latest (Faster)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Model for content generation agents (CPSO, Story Design, etc.)</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">CEO/Manager Model *</label>
                  <select
                    value={ceoModel}
                    onChange={(e) => setCeoModel(e.target.value)}
                    className="w-full px-4 py-2 border rounded"
                  >
                    <option value="qwen3:30b">Qwen3 30B (Recommended - Higher Quality)</option>
                    <option value="llama3:latest">Llama 3 Latest (Faster)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Model for CEO and manager agents that approve phases</p>
                </div>
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
            <div className="flex gap-2">
              <button
                onClick={() => navigate(`/writer/graph/${project.project_id}`)}
                className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
              >
                🕸️ Knowledge Graph
              </button>
              <button
                onClick={downloadProgressReport}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                📄 Progress Report
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
              >
                Back to Writer
              </button>
            </div>
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

          {/* Knowledge Graph - Always visible when project exists */}
          {project && !isComplete && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold">📊 Knowledge Graph</h3>
                <button
                  onClick={() => setShowGraph(!showGraph)}
                  className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
                >
                  {showGraph ? 'Hide' : 'Show'} Graph
                </button>
              </div>
              {showGraph && (
                <EmbeddedGraph 
                  key={graphKey}
                  projectId={project.project_id} 
                  height="500px"
                  autoRefresh={true}
                  refreshInterval={5000}
                />
              )}
            </div>
          )}

          {currentArtifacts && !isComplete && (
            <div className="bg-white border-2 border-blue-200 rounded-lg p-6 mb-4 shadow-md">
              <div className="mb-4">
                <h3 className="text-xl font-bold mb-2">Phase Results: {currentPhaseName}</h3>
                <p className="text-gray-600 mb-4">Review the generated content below and make your decision.</p>
              </div>
              
              <div className="mb-4">
                <div className="mb-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phase Results (Editable JSON)
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    You can edit the JSON below to modify the phase results before approving.
                  </p>
                </div>
                <div className="bg-gray-50 border rounded p-4">
                  <textarea
                    value={editableArtifactsJson}
                    onChange={(e) => handleJsonChange(e.target.value)}
                    className="w-full h-96 p-3 font-mono text-sm bg-white border border-gray-300 rounded resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    spellCheck={false}
                    placeholder="Loading artifacts..."
                  />
                </div>
                {jsonParseError && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                    <p className="text-sm text-red-700">
                      <strong>JSON Error:</strong> {jsonParseError}
                    </p>
                    <p className="text-xs text-red-600 mt-1">
                      Please fix the JSON syntax before proceeding.
                    </p>
                  </div>
                )}
                {!jsonParseError && editableArtifactsJson && (
                  <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded">
                    <p className="text-sm text-green-700">
                      ✓ Valid JSON - Ready to proceed
                    </p>
                  </div>
                )}
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

