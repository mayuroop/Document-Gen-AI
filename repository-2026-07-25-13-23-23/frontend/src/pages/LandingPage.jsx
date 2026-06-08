import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { createProject } from '../services/api';
import Header from '../components/Header';
import {
  GitBranch, FileText, Cpu, BarChart3, Download,
  MessageSquare, Zap, Shield, ArrowRight, Sparkles
} from 'lucide-react';

const FEATURES = [
  { icon: <Cpu size={24} />, title: 'AI-Powered Analysis', desc: 'Deep code analysis using local Ollama LLM for intelligent documentation.' },
  { icon: <FileText size={24} />, title: '14 Doc Types', desc: 'README, Architecture, API Docs, Setup, Security, and 9 more sections.' },
  { icon: <BarChart3 size={24} />, title: 'Auto Diagrams', desc: 'Architecture, sequence, flowchart, and ER diagrams generated automatically.' },
  { icon: <MessageSquare size={24} />, title: 'AI Chat', desc: 'Ask questions about the codebase and get intelligent answers.' },
  { icon: <Download size={24} />, title: 'Export Options', desc: 'Export as Markdown or HTML static site with one click.' },
  { icon: <Shield size={24} />, title: 'Secure & Private', desc: 'Your code stays local. No data sent to external services.' },
];

export default function LandingPage({ theme, toggleTheme }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return toast.error('Please enter a GitHub URL');

    setLoading(true);
    try {
      const project = await createProject(repoUrl.trim());
      toast.success('Project created! Generating documentation...');
      navigate(`/project/${project.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh' }}>
      <Header theme={theme} toggleTheme={toggleTheme} />

      {/* Hero Section */}
      <section style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: '80px 24px 60px', textAlign: 'center',

        position: 'relative', overflow: 'hidden',
      }}>
        {/* Background glow */}
        <div style={{
          position: 'absolute', width: 600, height: 600, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(108,92,231,0.12) 0%, transparent 70%)',
          top: '-200px', left: '50%', transform: 'translateX(-50%)',
          pointerEvents: 'none',
        }} />

        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(108, 92, 231, 0.1)', border: '1px solid rgba(108, 92, 231, 0.3)',
          borderRadius: 20, padding: '6px 16px', marginBottom: 24,
          fontSize: '0.85rem', color: '#a78bfa',
        }}>
          <Sparkles size={14} /> AI-Powered Documentation Generator
        </div>

        <h1 style={{
          fontSize: 'clamp(2.2rem, 5vw, 3.8rem)', fontWeight: 800,
          lineHeight: 1.15, maxWidth: 800, marginBottom: 20,
        }}>
          Transform Repos Into{' '}
          <span className="gradient-text">Professional Docs</span>
          {' '}Instantly
        </h1>

        <p style={{
          fontSize: '1.15rem', color: 'var(--text-secondary)',
          maxWidth: 600, lineHeight: 1.7, marginBottom: 40,
        }}>
          Paste any GitHub repository URL and get comprehensive documentation
          with architecture diagrams, API docs, and more — all powered by AI.
        </p>

        {/* Repo Input */}
        <form onSubmit={handleSubmit} style={{
          display: 'flex', gap: 12, width: '100%', maxWidth: 620,
          position: 'relative',
        }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <GitBranch size={18} style={{
              position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }} />
            <input
              id="repo-url-input"
              type="url"
              className="input-field"
              placeholder="https://github.com/owner/repository"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              style={{ paddingLeft: 44 }}
