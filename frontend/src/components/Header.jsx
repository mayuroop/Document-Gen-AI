import { Sun, Moon } from 'lucide-react';

export default function Header({ theme, toggleTheme, minimal = false }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: minimal ? '12px 20px' : '16px 40px',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      backdropFilter: 'blur(12px)',
    }}>
      <a href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'var(--gradient-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '16px', fontWeight: 800, color: 'white',
        }}>D</div>
        <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
          DocGen<span style={{ color: '#6c5ce7' }}>AI</span>
        </span>
      </a>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {!minimal && (
          <a href="/dashboard" className="btn-secondary" style={{ fontSize: '0.85rem', padding: '8px 16px', textDecoration: 'none' }}>
            Dashboard
          </a>
        )}
        <button
          onClick={toggleTheme}
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            width: 38, height: 38, borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', transition: 'all 0.2s',
          }}
          title="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
