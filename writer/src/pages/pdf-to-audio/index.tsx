import { useNavigate } from 'react-router-dom';
import PDFToAudio from '../../features/writer/PDFToAudio';

export default function PDFToAudioPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <div className="border-b p-4 bg-gray-50 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
              aria-label="Back to Writer"
            >
              ← Back to Writer
            </button>
            <div>
              <h1 className="text-2xl font-bold">PDF to Audio Converter</h1>
              <p className="text-sm text-gray-600 mt-1">
                Convert PDF books to audio using local TTS models
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          <PDFToAudio />
        </div>
      </div>
    </div>
  );
}

