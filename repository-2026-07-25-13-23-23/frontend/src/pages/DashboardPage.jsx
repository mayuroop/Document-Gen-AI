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
