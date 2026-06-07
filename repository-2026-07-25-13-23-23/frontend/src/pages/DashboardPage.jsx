import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { listProjects, createProject, deleteProject } from '../services/api';
import Header from '../components/Header';
import {
  GitBranch, Plus, Trash2, ExternalLink, Clock,
  FileText, RefreshCw, AlertCircle
} from 'lucide-react';

const STATUS_COLORS = {
  pending: '#ffc107',
  cloning: '#2196f3',
  processing: '#6c5ce7',
  generating: '#9c27b0',
  completed: '#4caf50',
  failed: '#f44336',
};

export default function DashboardPage({ theme, toggleTheme }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data.projects);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setCreating(true);
    try {
      const project = await createProject(repoUrl.trim());

      toast.success('Project created!');
      setShowModal(false);
      setRepoUrl('');
      navigate(`/project/${project.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Delete this project?')) return;
    try {
      await deleteProject(id);
      toast.success('Project deleted');
      fetchProjects();
    } catch (err) {
      toast.error('Failed to delete project');
    }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  return (
    <div style={{ minHeight: '100vh' }}>
      <Header theme={theme} toggleTheme={toggleTheme} minimal />

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 32,
        }}>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>Projects</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: 4 }}>
              {projects.length} project{projects.length !== 1 ? 's' : ''} generated
            </p>
          </div>
          <button
            id="new-project-btn"
            className="btn-primary"
            onClick={() => setShowModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Plus size={18} /> New Project
          </button>
        </div>
