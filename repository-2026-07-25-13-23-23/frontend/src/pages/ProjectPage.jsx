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
