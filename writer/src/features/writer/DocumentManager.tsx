import { useState, useEffect, useRef } from 'react';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  text_preview: string;
  uploaded_at: string;
}

interface DocumentManagerProps {
  selectedDocuments: string[];
  onDocumentsChange: (docIds: string[]) => void;
  textContext: string;
  onTextContextChange: (text: string) => void;
}

export default function DocumentManager({
  selectedDocuments,
  onDocumentsChange,
  textContext,
  onTextContextChange,
}: DocumentManagerProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [showTextContext, setShowTextContext] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textContextRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await fetch('/api/writer/documents');
      const data = await response.json();
      if (data.success) {
        setDocuments(data.documents);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
    ];
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt'];

    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      alert('Unsupported file type. Please upload PDF, DOCX, or TXT files.');
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
        await loadDocuments();
        // Auto-select the newly uploaded document
        onDocumentsChange([...selectedDocuments, data.document.id]);
        alert(`Document "${data.document.name}" uploaded successfully!`);
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

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const response = await fetch(`/api/writer/documents/${docId}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (data.success) {
        await loadDocuments();
        // Remove from selected if it was selected
        onDocumentsChange(selectedDocuments.filter((id) => id !== docId));
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete document');
    }
  };

  const handleToggleDocument = (docId: string) => {
    if (selectedDocuments.includes(docId)) {
      onDocumentsChange(selectedDocuments.filter((id) => id !== docId));
    } else {
      onDocumentsChange([...selectedDocuments, docId]);
    }
  };

  const handleSaveTextContext = async () => {
    if (!textContext.trim()) {
      alert('Please enter some text context');
      return;
    }

    try {
      // Generate a text ID
      const textId = `text_${Date.now()}`;
      const response = await fetch(`/api/writer/documents/${textId}/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: textContext }),
      });

      const data = await response.json();
      if (data.success) {
        await loadDocuments();
        alert('Text context saved!');
      }
    } catch (error) {
      console.error('Save text context error:', error);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type: string): string => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    return '📄';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm">Context Documents</h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : '📁 Upload'}
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* Text Context Toggle */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={showTextContext}
            onChange={(e) => setShowTextContext(e.target.checked)}
          />
          <span>Add Text Context</span>
        </label>
      </div>

      {showTextContext && (
        <div className="space-y-2">
          <textarea
            ref={textContextRef}
            value={textContext}
            onChange={(e) => onTextContextChange(e.target.value)}
            placeholder="Enter additional context text here..."
            className="w-full p-2 border rounded text-sm"
            rows={4}
          />
          <button
            onClick={handleSaveTextContext}
            className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
          >
            Save Text Context
          </button>
        </div>
      )}

      {/* Documents List */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {documents.length === 0 ? (
          <p className="text-xs text-gray-500 text-center py-4">
            No documents uploaded. Click "Upload" to add PDF, DOCX, or TXT files.
          </p>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.id}
              className={`p-2 border rounded text-xs ${
                selectedDocuments.includes(doc.id)
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-white border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{getFileIcon(doc.type)}</span>
                    <label className="flex items-center gap-1 cursor-pointer flex-1 min-w-0">
                      <input
                        type="checkbox"
                        checked={selectedDocuments.includes(doc.id)}
                        onChange={() => handleToggleDocument(doc.id)}
                        className="mr-1"
                      />
                      <span className="font-medium truncate">{doc.name}</span>
                    </label>
                  </div>
                  <div className="text-gray-500 text-xs">
                    {formatFileSize(doc.size)} • {new Date(doc.uploaded_at).toLocaleDateString()}
                  </div>
                  {doc.text_preview && (
                    <div className="text-gray-600 text-xs mt-1 line-clamp-2">
                      {doc.text_preview}...
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteDocument(doc.id)}
                  className="text-red-500 hover:text-red-700 text-xs px-1"
                  title="Delete document"
                >
                  ✕
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedDocuments.length > 0 && (
        <div className="text-xs text-gray-600 pt-2 border-t">
          {selectedDocuments.length} document{selectedDocuments.length !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
}

