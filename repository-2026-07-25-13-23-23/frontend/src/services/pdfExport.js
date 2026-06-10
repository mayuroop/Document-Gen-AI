import mermaid from 'mermaid';
import { sanitizeMermaidCode } from '../utils/mermaidSanitizer';

/**
 * Export all documentation + visual diagrams as a PDF.
 * Uses window.print() with a custom print view — most reliable method
 * for capturing mermaid SVGs and styled markdown content.
 */

const SECTION_LABELS = {
  readme: 'README',
  architecture: 'Architecture',
  api_docs: 'API Documentation',
  database: 'Database',
  setup: 'Setup Guide',
  deployment: 'Deployment',
  troubleshooting: 'Troubleshooting',
  changelog: 'Changelog',
  security: 'Security',
  performance: 'Performance',
  scalability: 'Scalability',
  testing: 'Testing',
  roadmap: 'Roadmap',
  license: 'License',
};

/**
 * Convert markdown to HTML (simple but effective for PDF)
 */
function md2html(md) {
  if (!md) return '';
  let h = md;

  // Fenced code blocks
  h = h.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
    `<pre style="background:#1a1a2e;color:#cdd6f4;padding:16px;border-radius:8px;font-size:12px;overflow-x:auto;line-height:1.6;font-family:monospace;border:1px solid #333;margin:12px 0;white-space:pre-wrap;word-break:break-word"><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
  );

  // Inline code
  h = h.replace(/`([^`]+)`/g,
    '<code style="background:#2a2a4a;color:#a78bfa;padding:2px 6px;border-radius:4px;font-size:0.85em;font-family:monospace">$1</code>'
  );

  // Headings
  h = h.replace(/^#### (.+)$/gm, '<h4 style="font-size:14px;margin:16px 0 8px;color:#333;font-weight:600">$1</h4>');
  h = h.replace(/^### (.+)$/gm, '<h3 style="font-size:16px;margin:20px 0 10px;color:#333;font-weight:600">$1</h3>');
  h = h.replace(/^## (.+)$/gm, '<h2 style="font-size:20px;margin:24px 0 12px;color:#222;border-bottom:2px solid #6c5ce7;padding-bottom:6px;font-weight:700">$1</h2>');
  h = h.replace(/^# (.+)$/gm, '<h1 style="font-size:26px;margin:28px 0 14px;color:#111;font-weight:800">$1</h1>');

  // Bold & italic
  h = h.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Horizontal rules
  h = h.replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid #ddd;margin:20px 0">');

  // Blockquotes
  h = h.replace(/^> (.+)$/gm,
    '<blockquote style="border-left:4px solid #6c5ce7;padding:8px 16px;margin:12px 0;color:#555;background:#f8f7ff;border-radius:0 8px 8px 0">$1</blockquote>'
