import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MindmapperPage from './pages/MindmapperPage';

function App() {
  // Determine base path based on current location
  // When served from /brainstorm/mindmapper, use /brainstorm/mindmapper as basename
  // When served from /mindmapper-static/, use /mindmapper-static/ as basename
  const currentPath = window.location.pathname;
  let basePath = '/mindmapper-static/';
  
  // If we're at /brainstorm/mindmapper (not /mindmapper-static), use /brainstorm/mindmapper as basename
  if (currentPath === '/brainstorm/mindmapper' || (currentPath.startsWith('/brainstorm/mindmapper/') && !currentPath.startsWith('/mindmapper-static'))) {
    basePath = '/brainstorm/mindmapper';
  }
  
  return (
    <BrowserRouter basename={basePath}>
      <Routes>
        <Route path="/" element={<MindmapperPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

