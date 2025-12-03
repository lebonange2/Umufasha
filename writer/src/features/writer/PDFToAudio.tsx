import { useState, useRef, useEffect } from 'react';

interface AudioFile {
  id: string;
  filename: string;
  size: number;
  file_path: string;
  document_id?: string;
  document_name?: string;
}

interface PDFSource {
  id: string;
  name: string;
  source: 'uploaded' | 'ferrari' | 'book-writer';
  size?: number;
  project_id?: string;
  file_type?: 'pdf' | 'txt'; // Track file type
}

interface PDFToAudioProps {
  documentId?: string;
  documentName?: string;
}

export default function PDFToAudio({ documentId: _documentId }: PDFToAudioProps) {
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState<string>('');
  const [audioFile, setAudioFile] = useState<AudioFile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<PDFSource | null>(null);
  const [uploadedDocs, setUploadedDocs] = useState<any[]>([]);
  const [ferrariProjects, setFerrariProjects] = useState<any[]>([]);
  const [bookWriterProjects, setBookWriterProjects] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Load all PDF sources on mount and check TTS availability
  useEffect(() => {
    loadAllPDFs();
    checkTTSAvailability();
  }, []);

  const checkTTSAvailability = async () => {
    try {
      const response = await fetch('/api/writer/tts-check');
      const data = await response.json();
      
      if (!data.available) {
        // Show error with install instructions
        const errorMsg = data.message || 'Bark TTS is not available.';
        const installCmd = data.install_command || 'pip install git+https://github.com/suno-ai/bark.git';
        const note = data.note || 'After installation, restart the server';
        setError(`${errorMsg}\n\nTo install Bark TTS, run:\n\n${installCmd}\n\n${note}`);
      } else {
        // Clear any previous errors if TTS is available
        setError(null);
        console.log('✅ Bark TTS is available:', data.message);
      }
    } catch (error) {
      console.error('Failed to check TTS availability:', error);
      // Don't set error here - let the conversion attempt show the real error
      // This prevents false errors if the endpoint is temporarily unavailable
    }
  };

  const loadAllPDFs = async () => {
    await Promise.all([
      loadUploadedDocuments(),
      loadFerrariProjects(),
      loadBookWriterProjects()
    ]);
  };

  const loadUploadedDocuments = async () => {
    try {
      const response = await fetch('/api/writer/documents');
      const data = await response.json();
      if (data.success) {
        // Filter for both PDF and TXT files
        // Filter for both PDF and TXT files, and add file_type metadata
        setUploadedDocs(data.documents
          .filter((doc: any) => 
            doc.type.includes('pdf') || doc.name.endsWith('.pdf') ||
            doc.type.includes('text/plain') || doc.name.endsWith('.txt')
          )
          .map((doc: any) => ({
            ...doc,
            file_type: (doc.type.includes('text/plain') || doc.name.endsWith('.txt')) ? 'txt' : 'pdf'
          }))
        );
      }
    } catch (error) {
      console.error('Failed to load uploaded documents:', error);
    }
  };

  const loadFerrariProjects = async () => {
    try {
      const response = await fetch('/api/ferrari-company/projects');
      const data = await response.json();
      if (data.success && data.projects) {
        setFerrariProjects(data.projects.filter((p: any) => p.has_pdf));
      }
    } catch (error) {
      console.error('Failed to load Ferrari projects:', error);
    }
  };

  const loadBookWriterProjects = async () => {
    try {
      const response = await fetch('/api/book-writer/projects-with-pdfs');
      const data = await response.json();
      if (data.success && data.projects) {
        setBookWriterProjects(data.projects.filter((p: any) => p.has_pdf));
      }
    } catch (error) {
      console.error('Failed to load book-writer projects:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check file type - accept both PDF and TXT files
    const isPDF = file.type.includes('pdf') || file.name.endsWith('.pdf');
    const isTXT = file.type.includes('text/plain') || file.name.endsWith('.txt');
    
    if (!isPDF && !isTXT) {
      alert('Please upload a PDF or TXT file.');
      return;
    }

    // Check file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      alert('File too large. Maximum size is 50MB.');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/writer/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        await loadUploadedDocuments();
        // Auto-select the newly uploaded document
        // Determine file type
        const isTXT = data.document.type?.includes('text/plain') || data.document.name?.endsWith('.txt');
        const fileType = isTXT ? 'txt' : 'pdf';
        
        const newDoc: PDFSource = {
          id: data.document.id,
          name: data.document.name,
          source: 'uploaded',
          size: data.document.size,
          file_type: fileType
        };
        setSelectedSource(newDoc);
        setShowUpload(false);
        alert(`PDF "${data.document.name}" uploaded successfully!`);
      } else {
        alert('Upload failed: ' + (data.error || 'Unknown error'));
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      alert('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleConvertToAudio = async () => {
    if (!selectedSource) {
      setError('Please select a PDF or TXT file to convert');
      return;
    }

    setConverting(true);
    setError(null);
    setProgress('Starting conversion...');
    setAudioFile(null);

    try {
      // Start conversion (returns task ID immediately)
      const startResponse = await fetch(`/api/writer/documents/${selectedSource.id}/convert-to-audio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          language: 'en',
        }),
      });

      if (!startResponse.ok) {
        const errorData = await startResponse.json().catch(() => ({ detail: `HTTP ${startResponse.status}` }));
        throw new Error(errorData.detail || errorData.error || `Conversion failed (${startResponse.status})`);
      }

      const startData = await startResponse.json();
      
      if (!startData.success || !startData.task_id) {
        throw new Error(startData.error || startData.detail || 'Failed to start conversion');
      }

      const taskId = startData.task_id;
      setProgress('Conversion started. Processing... This may take several minutes for large documents.');

      // Poll for status
      const pollInterval = 2000; // Poll every 2 seconds
      const maxAttempts = 600; // Max 20 minutes (600 * 2s)
      let attempts = 0;

      const pollStatus = async (): Promise<void> => {
        try {
          const statusResponse = await fetch(`/api/writer/tts-status/${taskId}`);
          
          if (!statusResponse.ok) {
            throw new Error(`Status check failed (${statusResponse.status})`);
          }

          const statusData = await statusResponse.json();
          
          if (statusData.status === 'completed' && statusData.audio) {
            setAudioFile(statusData.audio);
            setProgress('Conversion completed!');
            
            // Auto-play audio when ready
            setTimeout(() => {
              if (audioRef.current) {
                audioRef.current.load();
              }
            }, 500);
            return;
          } else if (statusData.status === 'failed') {
            throw new Error(statusData.error || statusData.progress || 'Conversion failed');
          } else if (statusData.status === 'processing' || statusData.status === 'pending') {
            // Update progress message
            if (statusData.progress) {
              setProgress(statusData.progress);
            }
            
            // Continue polling
            attempts++;
            if (attempts >= maxAttempts) {
              throw new Error('Conversion timed out. Please try again or use a smaller document.');
            }
            
            setTimeout(pollStatus, pollInterval);
          }
        } catch (error: any) {
          if (error.message && !error.message.includes('timed out')) {
            // Only throw if it's not a polling continuation
            throw error;
          }
          throw error;
        }
      };

      // Start polling
      await pollStatus();
      
    } catch (error: any) {
      console.error('Conversion error:', error);
      let errorMessage = error.message || 'Failed to convert document to audio.';
      
      // Provide more specific error messages
      if (errorMessage.includes('TTS model not available') || errorMessage.includes('No TTS model')) {
        errorMessage = 'Bark TTS not installed. Install with: pip install git+https://github.com/suno-ai/bark.git';
      } else if (errorMessage.includes('Bark')) {
        errorMessage = 'Bark TTS not available. Install with: pip install git+https://github.com/suno-ai/bark.git';
      }
      
      setError(errorMessage);
    } finally {
      setConverting(false);
      // Don't clear progress if conversion completed successfully (audioFile is set)
      if (!audioFile) {
        // Only clear progress if conversion failed
        setTimeout(() => setProgress(''), 3000);
      }
    }
  };

  const handleDownloadAudio = () => {
    if (audioFile) {
      window.open(audioFile.file_path, '_blank');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getSourceLabel = (source: string): string => {
    switch (source) {
      case 'uploaded': return '📄 Uploaded';
      case 'ferrari': return '🏎️ Ferrari Company';
      case 'book-writer': return '📚 Book Writer';
      default: return source;
    }
  };

  // Combine all PDF sources
  const allPDFs: PDFSource[] = [
    ...uploadedDocs.map(doc => ({
      id: doc.id,
      name: doc.name,
      source: 'uploaded' as const,
      size: doc.size
    })),
    ...ferrariProjects.map(proj => ({
      id: proj.project_id,
      name: proj.title || 'Untitled',
      source: 'ferrari' as const,
      project_id: proj.project_id
    })),
    ...bookWriterProjects.map(proj => ({
      id: proj.id,
      name: proj.title || 'Untitled',
      source: 'book-writer' as const,
      project_id: proj.id
    }))
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        {/* Upload Section */}
        <div className="flex items-center justify-between mb-4">
          <label className="block text-sm font-semibold">Document Source</label>
          <button
            onClick={() => setShowUpload(!showUpload)}
            disabled={uploading}
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {uploading ? '⏳ Uploading...' : '📁 Upload PDF/TXT'}
          </button>
        </div>

        {showUpload && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileUpload}
              className="w-full text-sm"
              disabled={uploading}
            />
            <p className="text-sm text-gray-600 mt-2">
              Select a PDF or TXT file to upload (max 50MB)
            </p>
          </div>
        )}

        {/* Document Selection */}
        <div className="mb-4">
          <label className="block text-sm font-semibold mb-2">Select Document (PDF or TXT)</label>
          {allPDFs.length === 0 ? (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded">
              <p className="text-sm text-gray-600">
                No documents available. Upload a PDF or TXT file, or generate one using Ferrari Company or Book Writer.
              </p>
            </div>
          ) : (
            <select
              value={selectedSource?.id || ''}
              onChange={(e) => {
                const selected = allPDFs.find(pdf => pdf.id === e.target.value);
                setSelectedSource(selected || null);
              }}
              disabled={converting}
              className="w-full p-3 border rounded text-sm disabled:opacity-50 bg-white"
            >
              <option value="">-- Select a document (PDF or TXT) --</option>
              {uploadedDocs.length > 0 && (
                <optgroup label="📄 Uploaded Documents">
                  {uploadedDocs.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.name} {doc.file_type === 'txt' ? '(TXT)' : '(PDF)'} ({formatFileSize(doc.size)})
                    </option>
                  ))}
                </optgroup>
              )}
              {ferrariProjects.length > 0 && (
                <optgroup label="🏎️ Ferrari Company Books">
                  {ferrariProjects.map((proj) => (
                    <option key={proj.project_id} value={proj.project_id}>
                      {proj.title || 'Untitled'} {proj.status === 'complete' ? '✓' : ''}
                    </option>
                  ))}
                </optgroup>
              )}
              {bookWriterProjects.length > 0 && (
                <optgroup label="📚 Book Writer Projects">
                  {bookWriterProjects.map((proj) => (
                    <option key={proj.id} value={proj.id}>
                      {proj.title || 'Untitled'} {proj.status === 'complete' ? '✓' : ''}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          )}
        </div>

        {selectedSource && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded mb-4">
            <p className="font-semibold text-sm mb-1">Selected Document:</p>
            <p className="text-gray-700 text-sm">
              {getSourceLabel(selectedSource.source)} - {selectedSource.name}
            </p>
          </div>
        )}

        {/* Convert Button */}
        <button
          onClick={handleConvertToAudio}
          disabled={!selectedSource || converting}
          className="w-full px-6 py-3 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-base font-semibold"
        >
          {converting ? (
            <>
              <span className="animate-spin">⏳</span>
              <span>Converting...</span>
            </>
          ) : (
            <>
              <span>🎵</span>
              <span>Convert to Audio</span>
            </>
          )}
        </button>

        {/* Progress Message */}
        {progress && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800 mb-4">
            <div className="flex items-center gap-2">
              <span className="animate-spin">⏳</span>
              <span>{progress}</span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded text-sm text-red-800 mb-4">
            <strong className="font-semibold">Error:</strong> {error}
            <div className="mt-3 text-sm">
              <p className="font-medium mt-2">To install Bark TTS, run:</p>
              <code className="block bg-red-100 p-2 rounded mt-2 text-sm font-mono">
                pip install git+https://github.com/suno-ai/bark.git
              </code>
              <p className="mt-3 text-xs text-gray-600">
                Note: Bark works with Python &gt;=3.8 (including 3.12+). First run will download ~2GB of models.
              </p>
            </div>
          </div>
        )}

        {/* Audio Player */}
        {audioFile && (
          <div className="space-y-3 p-6 bg-green-50 border border-green-200 rounded mb-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800">
                  ✅ Audio Generated Successfully!
                </p>
                <p className="text-xs text-green-600 mt-1">
                  {audioFile.filename} ({formatFileSize(audioFile.size)})
                </p>
              </div>
              <button
                onClick={handleDownloadAudio}
                className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
              >
                📥 Download
              </button>
            </div>

            <audio
              ref={audioRef}
              controls
              className="w-full"
              src={audioFile.file_path}
            >
              Your browser does not support the audio element.
            </audio>
            <div className="flex items-center justify-between mt-3">
              <span className="text-sm text-gray-600">
                {audioFile.filename} ({formatFileSize(audioFile.size)})
              </span>
              <button
                onClick={handleDownloadAudio}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              >
                ⬇️ Download Audio
              </button>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="p-6 bg-gray-50 border border-gray-200 rounded">
          <h3 className="font-semibold text-base mb-3">ℹ️ About PDF to Audio Conversion</h3>
          <ul className="list-disc list-inside space-y-2 text-sm text-gray-700">
            <li>Upload PDFs directly or use PDFs generated by Ferrari Company / Book Writer</li>
            <li>Uses Bark TTS by Suno AI - high-quality text-to-audio model</li>
            <li>Converts entire PDF books to audio format</li>
            <li>No API keys required - runs completely locally</li>
            <li>Works with Python &gt;=3.8 (including 3.12+)</li>
            <li>First run downloads ~2GB of models automatically</li>
            <li>Large documents may take several minutes to process</li>
            <li>Generated audio files are saved and can be downloaded</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
