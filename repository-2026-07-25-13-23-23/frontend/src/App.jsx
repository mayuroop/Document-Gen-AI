import { Routes, Route } from 'react-router-dom';
import { useTheme } from './hooks/useTheme';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import ProjectPage from './pages/ProjectPage';

export default function App() {
  const { theme, toggleTheme } = useTheme();

  return (
    <Routes>
      <Route path="/" element={<LandingPage theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="/dashboard" element={<DashboardPage theme={theme} toggleTheme={toggleTheme} />} />
      <Route path="/project/:projectId" element={<ProjectPage theme={theme} toggleTheme={toggleTheme} />} />
    </Routes>
  );
}
