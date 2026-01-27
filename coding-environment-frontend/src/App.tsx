import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CodingEnvironmentPage from './pages/CodingEnvironmentPage';

function App() {
  return (
    <BrowserRouter basename="/coding_environment">
      <Routes>
        <Route path="/" element={<CodingEnvironmentPage />} />
        <Route path="*" element={<CodingEnvironmentPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
