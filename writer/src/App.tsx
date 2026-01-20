import { BrowserRouter, Routes, Route } from 'react-router-dom';
import WriterPage from './pages/writer';
import OutlinePreviewPage from './pages/outline-preview';
import BookWriterPage from './pages/book-writer';
import BookPublishingHousePage from './pages/ferrari-company';
import PDFToAudioPage from './pages/pdf-to-audio';
import GraphEditorPage from './pages/graph-editor';
import ExamGeneratorPage from './pages/exam-generator';

function App() {
  // Determine base path based on current location
  // When served from /writer, use /writer as basename
  // When served from /writer-static/, use /writer-static/ as basename
  const currentPath = window.location.pathname;
  
  // Default to /writer-static for built assets
  let basePath = '/writer-static';
  
  // If path starts with /writer (but not /writer-static), use /writer as basename
  if (currentPath.startsWith('/writer/') && !currentPath.startsWith('/writer-static/')) {
    basePath = '/writer';
  } else if (currentPath === '/writer') {
    basePath = '/writer';
  }
  
  // Debug logging (remove in production if needed)
  console.log('App basename:', basePath, 'currentPath:', currentPath);
  
  return (
    <BrowserRouter basename={basePath}>
      <Routes>
        <Route path="/" element={<WriterPage />} />
        <Route path="outline-preview" element={<OutlinePreviewPage />} />
        <Route path="book-writer" element={<BookWriterPage />} />
        <Route path="ferrari-company" element={<BookPublishingHousePage />} />
        <Route path="pdf-to-audio" element={<PDFToAudioPage />} />
        <Route path="graph/:projectId" element={<GraphEditorPage />} />
        <Route path="exam-generator" element={<ExamGeneratorPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

