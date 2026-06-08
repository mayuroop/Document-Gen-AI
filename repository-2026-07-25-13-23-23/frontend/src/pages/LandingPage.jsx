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
