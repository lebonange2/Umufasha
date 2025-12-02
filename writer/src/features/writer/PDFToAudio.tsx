import { useState, useRef, useEffect } from 'react';

interface AudioFile {
  id: string;
  filename: string;
  size: number;
  file_path: string;
  document_id?: string;
  document_name?: string;
}

interface PDFToAudioProps {
  documentId?: string;
  documentName?: string;
}

export default function PDFToAudio({ documentId }: PDFToAudioProps) {
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState<string>('');
  const [audioFile, setAudioFile] = useState<AudioFile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(documentId || null);
  const [documents, setDocuments] = useState<any[]>([]);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await fetch('/api/writer/documents');
      const data = await response.json();
      if (data.success) {
        setDocuments(data.documents);
        // Auto-select if documentId provided
        if (documentId && !selectedDocId) {
          setSelectedDocId(documentId);
        }
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleConvertToAudio = async () => {
    if (!selectedDocId) {
      setError('Please select a document to convert');
      return;
    }

    setConverting(true);
    setError(null);
    setProgress('Extracting text from PDF...');
    setAudioFile(null);

    try {
      setProgress('Converting text to speech... This may take a few minutes for large documents.');
      
      const response = await fetch(`/api/writer/documents/${selectedDocId}/convert-to-audio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          language: 'en',
        }),
      });

      const data = await response.json();
      
      if (data.success && data.audio) {
        setAudioFile(data.audio);
        setProgress('Conversion completed!');
        
        // Auto-play audio when ready
        setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.load();
          }
        }, 500);
      } else {
        throw new Error(data.error || 'Conversion failed');
      }
    } catch (error: any) {
      console.error('Conversion error:', error);
      setError(error.message || 'Failed to convert PDF to audio. Make sure TTS models are installed.');
    } finally {
      setConverting(false);
      setProgress('');
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

  return (
    <div className="space-y-4">

      <div className="space-y-3">
        {/* Document Selection */}
        <div>
          <label className="block text-xs font-medium mb-1">Select PDF Document</label>
          {documents.length === 0 ? (
            <p className="text-xs text-gray-500 py-2">
              No documents available. Upload a PDF document first.
            </p>
          ) : (
            <select
              value={selectedDocId || ''}
              onChange={(e) => setSelectedDocId(e.target.value)}
              disabled={converting}
              className="w-full p-2 border rounded text-sm disabled:opacity-50"
            >
              <option value="">-- Select a document --</option>
              {documents
                .filter((doc) => doc.type.includes('pdf') || doc.name.endsWith('.pdf'))
                .map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.name} ({formatFileSize(doc.size)})
                  </option>
                ))}
            </select>
          )}
        </div>

        {/* Convert Button */}
        <button
          onClick={handleConvertToAudio}
          disabled={!selectedDocId || converting}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
          <div className="p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
            {progress}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
            <strong>Error:</strong> {error}
            <div className="mt-2 text-xs">
              <p>To install TTS models, run:</p>
              <code className="block bg-red-100 p-1 rounded mt-1">
                pip install TTS
              </code>
              <p className="mt-2">Or for lighter option:</p>
              <code className="block bg-red-100 p-1 rounded mt-1">
                pip install piper-tts
              </code>
            </div>
          </div>
        )}

        {/* Audio Player */}
        {audioFile && (
          <div className="space-y-2 p-3 bg-green-50 border border-green-200 rounded">
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
          </div>
        )}

        {/* Info Box */}
        <div className="p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600">
          <p className="font-medium mb-1">ℹ️ About this feature:</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>Uses high-quality local TTS models (Coqui XTTS v2 or Piper TTS)</li>
            <li>Converts entire PDF books to audio</li>
            <li>No API keys required - runs completely locally</li>
            <li>Large documents may take several minutes to process</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

