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

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bot size={18} style={{ color: '#6c5ce7' }} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>AI Chat</span>
        </div>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: 'var(--text-muted)',
          cursor: 'pointer', padding: 4,
        }}>
          <X size={18} />
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflow: 'auto', padding: 16,
        display: 'flex', flexDirection: 'column', gap: 12,
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex', flexDirection: 'column',
            alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4,
              fontSize: '0.75rem', color: 'var(--text-muted)',
            }}>
              {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
              {msg.role === 'user' ? 'You' : 'AI Assistant'}
            </div>
            <div className={`chat-bubble ${msg.role === 'user' ? 'user' : 'ai'}`}>
              {msg.role === 'ai' ? (
                <div className="markdown-body" style={{ fontSize: '0.85rem' }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
            <span style={{ fontSize: '0.8rem' }}>Thinking...</span>
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      {/* Input */}
      <div style={{
        padding: '12px 16px', borderTop: '1px solid var(--border-color)',
        display: 'flex', gap: 8,
