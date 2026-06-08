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


        {/* Project Grid */}
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
            <div className="spinner" />
          </div>
        ) : projects.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '80px 24px',
          }}>
            <FileText size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
            <h3 style={{ fontSize: '1.2rem', marginBottom: 8 }}>No projects yet</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
              Create your first project by entering a GitHub URL.
            </p>
            <button className="btn-primary" onClick={() => setShowModal(true)}>
              Create Project
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: 16,
          }}>
            {projects.map((project, i) => (
              <div
                key={project.id}
                className="glass-card animate-fade-in"
                style={{
                  padding: 24, cursor: 'pointer', animationDelay: `${i * 0.05}s`,
                }}
                onClick={() => navigate(`/project/${project.id}`)}
              >
                <div style={{
                  display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                  marginBottom: 16,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 10,
                      background: 'rgba(108, 92, 231, 0.12)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <GitBranch size={18} style={{ color: '#6c5ce7' }} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{project.repo_name}</h3>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{project.owner}</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(project.id, e)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--text-muted)', padding: 4,
                    }}
                    title="Delete project"
                  >

                    <Trash2 size={16} />
                  </button>
                </div>

                {/* Status */}
                <div style={{ marginBottom: 12 }}>
                  <span className={`status-badge status-${project.status}`}>
                    <span style={{
                      width: 6, height: 6, borderRadius: '50%',
                      background: STATUS_COLORS[project.status] || '#999',
                      display: 'inline-block',
                    }} />
                    {project.status}
                  </span>
                </div>

                {/* Progress */}
                {project.status !== 'completed' && project.status !== 'failed' && (
                  <div style={{ marginBottom: 12 }}>
                    <div className="progress-bar">
                      <div className="progress-bar-fill" style={{ width: `${project.progress}%` }} />
                    </div>
                    <p style={{
                      fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4,
                    }}>{project.progress}% complete</p>
                  </div>
                )}

                {/* Error */}
                {project.error && (
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    color: '#f44336', fontSize: '0.8rem', marginBottom: 8,
                  }}>
                    <AlertCircle size={14} />
                    <span>{project.error.slice(0, 60)}...</span>
                  </div>
                )}

                {/* Meta */}
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 8,
                  borderTop: '1px solid var(--border-color)', paddingTop: 12,
                }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>

                    <Clock size={12} /> {formatDate(project.created_at)}
                  </span>
                  <span>{project.file_count} files</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 100, backdropFilter: 'blur(4px)',
        }} onClick={() => setShowModal(false)}>
          <div className="glass-card animate-fade-in" style={{
            padding: 32, width: '100%', maxWidth: 500,
          }} onClick={e => e.stopPropagation()}>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 8 }}>
              New Project
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 24 }}>
              Enter a GitHub repository URL to generate documentation.
            </p>
            <form onSubmit={handleCreate}>
              <input
                id="modal-repo-input"
                className="input-field"
                placeholder="https://github.com/owner/repo"
                value={repoUrl}
                onChange={e => setRepoUrl(e.target.value)}
                autoFocus
              />
              <div style={{ display: 'flex', gap: 12, marginTop: 20, justifyContent: 'flex-end' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Generate Docs'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
