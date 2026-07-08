import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Copy, Check } from 'lucide-react';

function CodeBlock({ children, className }) {
  const [copied, setCopied] = useState(false);
  const code = String(children).replace(/\n$/, '');

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [code]);

  return (
    <div style={{ position: 'relative' }}>
      <button className="copy-btn" onClick={handleCopy} style={{ opacity: 1 }}>
        {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
      </button>
      <pre>
        <code className={className}>{code}</code>
      </pre>
    </div>
  );
}

export default function DocViewer({ content, sectionName }) {
  if (!content) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: 300, flexDirection: 'column', gap: 12,
      }}>
        <p style={{ color: 'var(--text-muted)' }}>No content available for this section.</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid var(--border-color)' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>{sectionName}</h1>
      </div>

      <div className="markdown-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
          components={{
            code({ node, inline, className, children, ...props }) {
              if (!inline && className) {
                return <CodeBlock className={className}>{children}</CodeBlock>;
              }
              if (!inline) {
                return <CodeBlock>{children}</CodeBlock>;
              }
              return <code className={className} {...props}>{children}</code>;
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
