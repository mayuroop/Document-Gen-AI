import { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, User } from 'lucide-react';
import { chatAboutProject } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatPanel({ projectId, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: "👋 Hi! I'm your AI assistant for this project. Ask me anything about the codebase — architecture, APIs, how things work, or suggestions for improvement.",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const response = await chatAboutProject(projectId, userMsg);
      setMessages(prev => [...prev, { role: 'ai', content: response.response }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: '❌ Sorry, I encountered an error. Please try again.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      width: 380, minWidth: 380, borderLeft: '1px solid var(--border-color)',
      display: 'flex', flexDirection: 'column', background: 'var(--bg-secondary)',
      height: 'calc(100vh - 110px)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px', borderBottom: '1px solid var(--border-color)',
      }}>
