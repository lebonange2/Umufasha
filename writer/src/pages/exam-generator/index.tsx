import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';

interface ExamGeneratorProject {
  project_id: string;
  input_file_path: string;
  output_directory: string;
  current_phase: string;
  status: string;
  num_problems: number;  // Problems per objective
  num_objectives?: number;  // Number of learning objectives
  total_problems?: number;  // Total problems: num_objectives * num_problems
  validation_iterations: number;
  model: string;
  problems: any[];
  validation_results: any[];
  final_review: any;
  output_files: Record<string, string>;
}

const PHASE_NAMES: Record<string, string> = {
  content_analysis: 'Content Analysis',
  problem_generation: 'Problem Generation',
  validation: 'Validation',
  final_review: 'Final Review',
  complete: 'Complete'
};

export default function ExamGeneratorPage() {
  const navigate = useNavigate();
  const [project, setProject] = useState<ExamGeneratorProject | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<any>(null);
  
  // Form state
  const [inputFile, setInputFile] = useState<File | null>(null);
  const [inputText, setInputText] = useState('');
  const [numProblems, setNumProblems] = useState(10);
  const [validationIterations, setValidationIterations] = useState(3);
  const [model, setModel] = useState('qwen3:30b');
  const [outputDir, setOutputDir] = useState('exam_outputs');
  const [useFileUpload, setUseFileUpload] = useState(true);
  
  const [previousProjects, setPreviousProjects] = useState<any[]>([]);
  const [showPreviousProjects, setShowPreviousProjects] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(false);

  useEffect(() => {
    if (project && project.status === 'generating') {
      pollGenerationStatus();
    }
  }, [project]);

  const pollGenerationStatus = async () => {
    if (!project) return;

    const poll = async () => {
      try {
        const response = await fetch(`/api/exam-generator/projects/${project.project_id}/status`);
        if (!response.ok) {
          throw new Error('Failed to get generation status');
        }
        const status = await response.json();
        setGenerationStatus(status);

        if (status.status === 'complete') {
          setGenerating(false);
          await refreshProject();
        } else if (status.status === 'error') {
          setGenerating(false);
          setError(status.error || 'Generation failed');
        } else if (status.status === 'generating') {
          // Continue polling, update UI with progress
          setTimeout(poll, 2000);
        } else {
          setTimeout(poll, 2000);
        }
      } catch (err: any) {
        console.error('Poll generation status error:', err);
        setTimeout(poll, 3000);
      }
    };

    poll();
  };

  const refreshProject = async () => {
    if (!project) return;

    try {
      const response = await fetch(`/api/exam-generator/projects/${project.project_id}`);
      if (!response.ok) {
        throw new Error('Failed to refresh project');
      }
      const data = await response.json();
      setProject(data);
    } catch (err: any) {
      console.error('Refresh project error:', err);
    }
  };

  const loadPreviousProjects = async () => {
    setLoadingProjects(true);
    try {
      const response = await fetch('/api/exam-generator/projects');
      if (!response.ok) {
        throw new Error('Failed to load projects');
      }
      const data = await response.json();
      setPreviousProjects(data);
      setShowPreviousProjects(true);
    } catch (err: any) {
      console.error('Load projects error:', err);
      setError(err.message || 'Failed to load previous projects');
    } finally {
      setLoadingProjects(false);
    }
  };

  const loadProject = async (projectId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/exam-generator/projects/${projectId}`);
      if (!response.ok) {
        throw new Error('Failed to load project');
      }
      const data = await response.json();
      setProject(data);
      setShowPreviousProjects(false);
    } catch (err: any) {
      console.error('Load project error:', err);
      setError(err.message || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    setLoading(true);
    setError(null);

    try {
      let projectData;

      if (useFileUpload && inputFile) {
        // Upload file
        const formData = new FormData();
        formData.append('file', inputFile);
        formData.append('output_directory', outputDir);
        formData.append('num_problems', numProblems.toString());
        formData.append('validation_iterations', validationIterations.toString());
        formData.append('model', model);

        const response = await fetch('/api/exam-generator/projects/upload', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = 'Failed to create project';
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            errorMessage = errorText || errorMessage;
          }
          throw new Error(errorMessage);
        }

        projectData = await response.json();
      } else {
        // Use text input
        if (!inputText.trim()) {
          throw new Error('Please provide input text or upload a file');
        }

        const response = await fetch('/api/exam-generator/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            input_content: inputText,
            output_directory: outputDir,
            num_problems: numProblems,
            validation_iterations: validationIterations,
            model: model
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = 'Failed to create project';
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            errorMessage = errorText || errorMessage;
          }
          throw new Error(errorMessage);
        }

        projectData = await response.json();
      }

      console.log('Created project - num_objectives:', projectData.num_objectives, 'total_problems:', projectData.total_problems, 'num_problems:', projectData.num_problems);
      setProject(projectData);
    } catch (err: any) {
      console.error('Create project error:', err);
      setError(err.message || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const startGeneration = async () => {
    if (!project) return;

    setGenerating(true);
    setError(null);

    try {
      const response = await fetch(`/api/exam-generator/projects/${project.project_id}/generate`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = 'Failed to start generation';
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      await refreshProject();
      pollGenerationStatus();
    } catch (err: any) {
      console.error('Start generation error:', err);
      let errorMessage = err.message || 'Failed to start generation';
      
      // Check for connection errors
      if (errorMessage.includes('connection') || errorMessage.includes('failed') || errorMessage.includes('NetworkError')) {
        errorMessage = 'Connection error: Could not connect to the server. Please ensure the backend server is running and accessible.';
      }
      
      setError(errorMessage);
      setGenerating(false);
    }
  };

  const downloadFile = async (fileType: 'problems' | 'solutions' | 'combined') => {
    if (!project) return;

    try {
      const response = await fetch(`/api/exam-generator/projects/${project.project_id}/download/${fileType}`);
      if (!response.ok) {
        throw new Error('Failed to download file');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${fileType}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Download file error:', err);
      setError(err.message || 'Failed to download file');
    }
  };

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-3xl font-bold">Exam Generator</h1>
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                Back to Writer
              </button>
            </div>
            <p className="text-gray-600 mb-6">
              Generate high-quality multiple choice exam questions from text content using AI agents.
              The system validates questions through multiple iterations to ensure correctness.
            </p>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Input Method
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={useFileUpload}
                      onChange={() => setUseFileUpload(true)}
                      className="mr-2"
                    />
                    Upload File (.txt)
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={!useFileUpload}
                      onChange={() => setUseFileUpload(false)}
                      className="mr-2"
                    />
                    Paste Text
                  </label>
                </div>
              </div>

              {useFileUpload ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Input File (.txt)
                  </label>
                  <input
                    type="file"
                    accept=".txt"
                    onChange={(e) => setInputFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Input Text
                  </label>
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    rows={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Paste or type the content you want to generate exam questions from..."
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    # of Problems per Learning Objective
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={numProblems}
                    onChange={(e) => setNumProblems(parseInt(e.target.value) || 10)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Each learning objective in your input will get this many problems
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Validation Iterations
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={validationIterations}
                    onChange={(e) => setValidationIterations(parseInt(e.target.value) || 3)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="qwen3:30b">qwen3:30b</option>
                    <option value="llama3:latest">llama3:latest</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Output Directory
                  </label>
                  <input
                    type="text"
                    value={outputDir}
                    onChange={(e) => setOutputDir(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={createProject}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Creating...' : 'Create Project'}
                </button>
                <button
                  onClick={loadPreviousProjects}
                  disabled={loadingProjects}
                  className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingProjects ? 'Loading...' : 'Load Previous Projects'}
                </button>
              </div>

              {showPreviousProjects && (
                <div className="mt-4">
                  <h3 className="text-lg font-semibold mb-2">Previous Projects</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {previousProjects.map((p) => (
                      <div
                        key={p.project_id}
                        className="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer"
                        onClick={() => loadProject(p.project_id)}
                      >
                        <div className="font-medium">{p.input_file_path || 'Text Input'}</div>
                        <div className="text-sm text-gray-500">
                          Status: {p.status} | Phase: {p.current_phase} | Problems: {p.num_problems}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold">Exam Generator</h1>
            <div className="flex gap-2">
              <button
                onClick={() => setProject(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                New Project
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Back to Writer
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div className="text-sm text-gray-600">Status</div>
              <div className="text-lg font-semibold">{project.status}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Current Phase</div>
              <div className="text-lg font-semibold">{PHASE_NAMES[project.current_phase] || project.current_phase}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Total Problems</div>
              <div className="text-lg font-semibold">
                {project.total_problems || (project.num_objectives ? project.num_objectives * project.num_problems : project.num_problems)}
              </div>
              {project.num_objectives && (
                <div className="text-xs text-gray-500 mt-1">
                  {project.num_objectives} objectives × {project.num_problems} per objective
                </div>
              )}
            </div>
            <div>
              <div className="text-sm text-gray-600">Validation Iterations</div>
              <div className="text-lg font-semibold">{project.validation_iterations}</div>
            </div>
          </div>

          {project.status === 'in_progress' && (
            <div>
              <button
                onClick={startGeneration}
                disabled={generating}
                className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generating ? 'Generating...' : 'Start Generation'}
              </button>
              <p className="mt-2 text-sm text-gray-600">
                Note: Ensure Ollama is running at http://localhost:11434 with the selected model ({project.model}) installed.
              </p>
            </div>
          )}

          {generating && generationStatus && (
            <div className="mt-4 p-4 bg-blue-50 rounded-md">
              <div className="text-sm font-medium mb-2">Generation Status</div>
              <div className="text-sm text-gray-700 mb-1">
                <span className="font-semibold">Phase:</span> {PHASE_NAMES[generationStatus.phase] || generationStatus.phase}
              </div>
              <div className="text-sm text-gray-700 mb-2">
                <span className="font-semibold">Progress:</span> {generationStatus.progress || 0}%
              </div>
              {generationStatus.message && (
                <div className="text-sm text-gray-600 italic">{generationStatus.message}</div>
              )}
              {generationStatus.error && (
                <div className="text-sm text-red-600 mt-2">Error: {generationStatus.error}</div>
              )}
              <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${generationStatus.progress || 0}%` }}
                ></div>
              </div>
            </div>
          )}

          {project.status === 'complete' && (
            <div className="mt-4">
              <h3 className="text-lg font-semibold mb-2">Download Generated Files</h3>
              <div className="flex gap-4">
                <button
                  onClick={() => downloadFile('problems')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Download Problems.txt
                </button>
                <button
                  onClick={() => downloadFile('solutions')}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Download Solutions.txt
                </button>
                <button
                  onClick={() => downloadFile('combined')}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                >
                  Download Problems_with_solutions.txt
                </button>
              </div>
            </div>
          )}
        </div>

        {project.problems && project.problems.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Generated Problems ({project.problems.length})</h2>
            <div className="space-y-6">
              {project.problems.map((problem: any, idx: number) => (
                <div key={idx} className="border border-gray-200 rounded-md p-4">
                  <div className="font-semibold mb-2">Problem {problem.problem_number}</div>
                  <div className="text-sm text-gray-600 mb-2">
                    Topic: {problem.topic} | Difficulty: {problem.difficulty}
                  </div>
                  <div className="mb-2">{renderLaTeX(problem.question)}</div>
                  <div className="ml-4 space-y-1">
                    {Object.entries(problem.choices || {}).map(([choice, text]: [string, any]) => (
                      <div key={choice} className="text-sm">
                        {choice}. {renderLaTeX(String(text))} {choice === problem.correct_answer && <span className="text-green-600 font-bold">✓</span>}
                      </div>
                    ))}
                  </div>
                  {problem.explanation && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="text-sm font-semibold mb-1">Explanation:</div>
                      <div className="text-sm text-gray-700">{renderLaTeX(problem.explanation)}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {project.final_review && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">Final Review</h2>
            <div className="space-y-2">
              <div>
                <span className="font-semibold">Overall Quality:</span> {project.final_review.overall_quality}
              </div>
              <div>
                <span className="font-semibold">Approval Status:</span> {project.final_review.approval_status}
              </div>
              {project.final_review.issues_found && project.final_review.issues_found.length > 0 && (
                <div>
                  <span className="font-semibold">Issues Found:</span>
                  <ul className="list-disc list-inside ml-4">
                    {project.final_review.issues_found.map((issue: string, idx: number) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
              {project.final_review.recommendations && project.final_review.recommendations.length > 0 && (
                <div>
                  <span className="font-semibold">Recommendations:</span>
                  <ul className="list-disc list-inside ml-4">
                    {project.final_review.recommendations.map((rec: string, idx: number) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
