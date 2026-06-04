import { useEffect, useRef, useState, Component } from 'react';
import mermaid from 'mermaid';
import { Copy, Check, Maximize2, Minimize2, AlertTriangle } from 'lucide-react';

let mermaidInitialized = false;

function initMermaid() {
  if (mermaidInitialized) return;
  try {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'Inter, sans-serif',
      suppressErrors: true,
      themeVariables: {
        primaryColor: '#6c5ce7',
        primaryTextColor: '#e8e8f0',
        primaryBorderColor: '#4c38b8',
        lineColor: '#a78bfa',
        secondaryColor: '#1a1a3e',
        tertiaryColor: '#22224a',
      },
    });
    mermaidInitialized = true;
  } catch (e) {
    console.warn('Mermaid init error:', e);
  }
}

/**
 * React Error Boundary — catches crashes from mermaid rendering
 * so the whole app doesn't go blank.
 */
class DiagramErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.warn('DiagramErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (

        <div style={{
          padding: 24, background: 'var(--bg-card)',
          border: '1px solid var(--border-color)', borderRadius: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <AlertTriangle size={18} style={{ color: '#ff9800' }} />
            <span style={{ fontWeight: 600, color: '#ff9800' }}>Diagram rendering failed</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
            The diagram code has syntax issues that couldn't be auto-fixed.
          </p>
          {this.props.code && (
            <pre style={{
              background: '#0d1117', padding: 16, borderRadius: 8,
              fontSize: '0.8rem', color: '#a78bfa', overflow: 'auto',
              whiteSpace: 'pre-wrap',
            }}>
              <code>{this.props.code}</code>
            </pre>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}


// Sanitizer imported from shared utility
import { sanitizeMermaidCode } from '../utils/mermaidSanitizer';



function MermaidChart({ code, id }) {
  const containerRef = useRef(null);
  const [rendered, setRendered] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [svgContent, setSvgContent] = useState('');

  const sanitized = sanitizeMermaidCode(code);

  useEffect(() => {
    initMermaid();

