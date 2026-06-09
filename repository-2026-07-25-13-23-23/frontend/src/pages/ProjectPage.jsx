import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getProject, getDocumentation, regenerateProject } from '../services/api';
import { exportToPdf } from '../services/pdfExport';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import DocViewer from '../components/DocViewer';
import DiagramViewer from '../components/DiagramViewer';
import ApiViewer from '../components/ApiViewer';
import FileExplorer from '../components/FileExplorer';
import ChatPanel from '../components/ChatPanel';
import SearchModal from '../components/SearchModal';
import {
  RefreshCw, Download, Search, MessageSquare,
  Loader, AlertTriangle, FileDown
} from 'lucide-react';

const DOC_SECTIONS = [
  { key: 'readme', label: 'README', icon: '📖' },
  { key: 'architecture', label: 'Architecture', icon: '🏗️' },
  { key: 'api_docs', label: 'API Docs', icon: '🔌' },
  { key: 'database', label: 'Database', icon: '🗄️' },
  { key: 'setup', label: 'Setup', icon: '⚙️' },
  { key: 'deployment', label: 'Deployment', icon: '🚀' },
  { key: 'troubleshooting', label: 'Troubleshooting', icon: '🔧' },
  { key: 'changelog', label: 'Changelog', icon: '📝' },
  { key: 'security', label: 'Security', icon: '🔐' },
  { key: 'performance', label: 'Performance', icon: '⚡' },
  { key: 'scalability', label: 'Scalability', icon: '📈' },
  { key: 'testing', label: 'Testing', icon: '🧪' },
  { key: 'roadmap', label: 'Roadmap', icon: '🗺️' },
  { key: 'license', label: 'License', icon: '📄' },
];

export default function ProjectPage({ theme, toggleTheme }) {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [docs, setDocs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('readme');
  const [activeView, setActiveView] = useState('docs'); // docs, diagrams, api, files
  const [activeDiagram, setActiveDiagram] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const proj = await getProject(projectId);
      setProject(proj);

      if (proj.status === 'completed') {
        const docData = await getDocumentation(projectId);
        setDocs(docData);
      }
    } catch (err) {
      console.error('Failed to load project:', err);
    } finally {

      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
    // Poll if not completed
    const interval = setInterval(async () => {
      try {
        const proj = await getProject(projectId);
        setProject(proj);
        if (proj.status === 'completed' && !docs) {
          const docData = await getDocumentation(projectId);
          setDocs(docData);
          clearInterval(interval);
        }
        if (proj.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {}
    }, 3000);

    return () => clearInterval(interval);
  }, [projectId, fetchData]);

  const handleRegenerate = async () => {
    try {
      await regenerateProject(projectId);
      toast.success('Regeneration started');
      setDocs(null);
      fetchData();
    } catch (err) {
      toast.error('Failed to regenerate');
    }
  };

  const handleExportMd = () => {
    if (!docs) return;
    const documentation = docs.documentation || {};
    let combined = '';
    for (const [key, content] of Object.entries(documentation)) {
      combined += `# ${key.toUpperCase().replace('_', ' ')}\n\n${content}\n\n---\n\n`;
    }
    const blob = new Blob([combined], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${project?.repo_name || 'docs'}_documentation.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Markdown exported!');
  };

  const [exportingPdf, setExportingPdf] = useState(false);

  const handleExportPdf = async () => {
    if (!docs) return;
    setExportingPdf(true);
    const toastId = toast.loading('Generating PDF... This may take a moment.');
    try {
      await exportToPdf(
        project?.repo_name || 'Project',
        docs.documentation || {},
        docs.diagrams || []
      );
      toast.success('PDF exported successfully!', { id: toastId });
    } catch (err) {
      console.error('PDF export error:', err);
      toast.error('PDF export failed. Try again.', { id: toastId });
    } finally {
      setExportingPdf(false);
    }
  };

  // Keyboard shortcut for search
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setShowSearch(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh' }}>
        <Header theme={theme} toggleTheme={toggleTheme} minimal />
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: 'calc(100vh - 60px)', flexDirection: 'column', gap: 16,
        }}>
          <div className="spinner" />
          <p style={{ color: 'var(--text-secondary)' }}>Loading project...</p>
        </div>
      </div>
    );
  }


  // Processing state
  if (project && project.status !== 'completed' && project.status !== 'failed') {
    return (
      <div style={{ minHeight: '100vh' }}>
        <Header theme={theme} toggleTheme={toggleTheme} minimal />
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: 'calc(100vh - 60px)', flexDirection: 'column', gap: 20,
          padding: 24,
        }}>
          <div className="spinner" style={{ width: 56, height: 56, borderWidth: 4 }} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 600 }}>
            Generating Documentation
          </h2>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', maxWidth: 400 }}>
            Analyzing <strong>{project.repo_name}</strong> repository...
            <br />This may take a few minutes depending on the repo size.
          </p>

          <div style={{ width: '100%', maxWidth: 400, marginTop: 12 }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between', marginBottom: 8,
              fontSize: '0.85rem',
            }}>
              <span className={`status-badge status-${project.status}`}>
                {project.status}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>{project.progress}%</span>
            </div>
            <div className="progress-bar" style={{ height: 8 }}>
              <div className="progress-bar-fill" style={{ width: `${project.progress}%` }} />
            </div>
          </div>

          <div style={{
            marginTop: 20, padding: '16px 24px',
            background: 'var(--bg-card)', borderRadius: 12,
            border: '1px solid var(--border-color)',
            fontSize: '0.85rem', color: 'var(--text-secondary)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Loader size={14} className="animate-spin" /> Processing Steps:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingLeft: 22 }}>
              {['Clone repository', 'Process files', 'AI analysis', 'Generate documentation', 'Create diagrams'].map((step, i) => {
                const stepProgress = [5, 15, 25, 60, 88];
                const done = project.progress > stepProgress[i];
                const active = project.progress >= stepProgress[i] && project.progress <= (stepProgress[i + 1] || 100);
