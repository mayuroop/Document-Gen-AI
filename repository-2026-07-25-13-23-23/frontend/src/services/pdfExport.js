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

  );

  // Unordered lists
  h = h.replace(/^[\-\*] (.+)$/gm, '<li style="margin:4px 0">$1</li>');
  h = h.replace(/((?:<li[^>]*>.*<\/li>\n?)+)/g, '<ul style="padding-left:24px;margin:10px 0">$1</ul>');

  // Links
  h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" style="color:#6c5ce7">$1</a>');

  // Simple tables
  h = h.replace(/^\|(.+)\|$/gm, (match, content) => {
    const cells = content.split('|').map(c => c.trim());
    if (cells.every(c => /^[-:]+$/.test(c))) return '';
    const cellHtml = cells.map(c =>
      `<td style="padding:8px 12px;border:1px solid #ddd">${c}</td>`
    ).join('');
    return `<tr>${cellHtml}</tr>`;
  });
  h = h.replace(/((?:<tr>.*<\/tr>\n?)+)/g,
    '<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:13px">$1</table>'
  );

  // Paragraphs
  h = h.replace(/^(?!<[a-z/])((?!^\s*$).+)$/gm, '<p style="margin:8px 0;line-height:1.7;color:#333">$1</p>');

  return h;
}

/**
 * Render mermaid code to SVG string — uses the shared sanitizer
 */
async function renderMermaidSvg(code, id) {
  if (!code) return '';

  // Use the same sanitizer as DiagramViewer
  const sanitized = sanitizeMermaidCode(code);
  if (!sanitized) return '';

  try {
    const uniqueId = `pdf-m-${id}-${Date.now()}`;
    const { svg } = await mermaid.render(uniqueId, sanitized);
    return svg;
  } catch (err) {
    console.warn(`PDF diagram ${id} render failed:`, err?.message);
    // Fallback: show sanitized code as text
    return `<pre style="background:#f5f5f5;color:#6c5ce7;padding:16px;border-radius:8px;font-size:11px;white-space:pre-wrap;border:1px solid #ddd">${sanitized.replace(/</g, '&lt;')}</pre>`;
  }
}

/**
 * Generate and download PDF using a print window approach.
 * Opens a new window with styled content and triggers print dialog.
 */
export async function exportToPdf(projectName, documentation, diagrams) {
  // ── Build the complete HTML document ──
  let sections = '';

  // Documentation sections
  for (const [key, content] of Object.entries(documentation || {})) {

    const label = SECTION_LABELS[key] || key;
    sections += `
      <div class="section">
        <div class="section-header">${label}</div>
        <div class="section-content">${md2html(content)}</div>
      </div>
    `;
  }

  // Diagrams
  let diagramsHtml = '';
  if (diagrams && diagrams.length > 0) {
    for (let i = 0; i < diagrams.length; i++) {
      const d = diagrams[i];
      const title = d.title || d.type || `Diagram ${i + 1}`;
      const svg = await renderMermaidSvg(d.mermaid_code, i);
      diagramsHtml += `
        <div class="diagram-block">
          <h3 style="color:#6c5ce7;margin-bottom:12px;font-size:18px">${title}</h3>
          <div class="diagram-svg">${svg}</div>
        </div>
      `;
    }
  }

  const dateStr = new Date().toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  const fullHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${projectName} — Documentation</title>
  <style>
    @page {
      size: A4;
      margin: 20mm 15mm;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #222;
      background: #fff;
      font-size: 13px;
      line-height: 1.6;
    }

    /* Cover page */
    .cover {
      text-align: center;
      padding: 120px 40px 80px;
      page-break-after: always;
    }
    .cover .brand {
