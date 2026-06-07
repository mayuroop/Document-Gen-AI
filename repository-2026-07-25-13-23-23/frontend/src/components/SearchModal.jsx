import { useState, useEffect, useRef } from 'react';
import { Search, X, FileText, Code2 } from 'lucide-react';
import { searchDocs } from '../services/api';

export default function SearchModal({ projectId, onClose, onNavigate }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (query.length < 2) {
      setResults([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchDocs(projectId, query);
        setResults(data.results || []);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, projectId]);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') onClose();
  };

  return (

    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        paddingTop: 100, zIndex: 100, backdropFilter: 'blur(4px)',
      }}
      onClick={onClose}
      onKeyDown={handleKeyDown}
    >
      <div
        className="glass-card animate-fade-in"
        style={{ width: '100%', maxWidth: 600, maxHeight: 500, overflow: 'hidden' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
        }}>
          <Search size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search documentation..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: 'var(--text-primary)', fontSize: '1rem',
            }}
          />
          <button onClick={onClose} style={{
            background: 'none', border: 'none', color: 'var(--text-muted)',
            cursor: 'pointer',
          }}>
            <X size={18} />
          </button>
        </div>

        {/* Results */}
        <div style={{ maxHeight: 380, overflow: 'auto', padding: '8px 0' }}>
          {loading && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: 24, gap: 8, color: 'var(--text-muted)',
            }}>
              <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />

              Searching...
            </div>
          )}

          {!loading && query.length >= 2 && results.length === 0 && (
            <div style={{
              textAlign: 'center', padding: 32, color: 'var(--text-muted)',
            }}>
              No results found for "{query}"
            </div>
          )}

          {results.map((result, i) => (
            <div
              key={i}
              style={{
                padding: '12px 20px', cursor: 'pointer',
                borderBottom: '1px solid var(--border-color)',
                transition: 'background 0.15s',
              }}
              onClick={() => {
                if (result.type === 'documentation') {
                  onNavigate(result.section);
                }
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                {result.type === 'documentation' ? (
                  <FileText size={14} style={{ color: '#6c5ce7' }} />
                ) : (
                  <Code2 size={14} style={{ color: '#4caf50' }} />
                )}
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                  {result.section?.replace(/_/g, ' ').toUpperCase()}
                </span>
                <span style={{
                  fontSize: '0.7rem', color: 'var(--text-muted)',
                  background: 'var(--bg-primary)', padding: '1px 6px', borderRadius: 4,
                }}>
                  {result.match_count} match{result.match_count !== 1 ? 'es' : ''}
                </span>
              </div>
              <p style={{
                fontSize: '0.8rem', color: 'var(--text-secondary)',
                overflow: 'hidden', textOverflow: 'ellipsis',
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
              }}>
                {result.snippet}
              </p>

            </div>
          ))}

          {query.length < 2 && (
            <div style={{
              textAlign: 'center', padding: 32, color: 'var(--text-muted)',
              fontSize: '0.85rem',
            }}>
              Type at least 2 characters to search
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
