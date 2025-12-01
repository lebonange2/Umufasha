import { BrowserRouter, Routes, Route } from 'react-router-dom';
import WriterPage from './pages/writer';
import OutlinePreviewPage from './pages/outline-preview';
import BookWriterPage from './pages/book-writer';

function App() {
  // Determine base path based on current location
  // When served from /writer, use /writer as basename
  // When served from /writer-static/, use /writer-static/ as basename
  const currentPath = window.location.pathname;
  let basePath = '/writer-static/';
  
  // If we're at /writer (not /writer-static), use /writer as basename
  if (currentPath === '/writer' || (currentPath.startsWith('/writer/') && !currentPath.startsWith('/writer-static'))) {
    basePath = '/writer';
  }
  
  return (
    <BrowserRouter basename={basePath}>
      <Routes>
        <Route path="/" element={<WriterPage />} />
        <Route path="outline-preview" element={<OutlinePreviewPage />} />
        <Route path="book-writer" element={<BookWriterPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

