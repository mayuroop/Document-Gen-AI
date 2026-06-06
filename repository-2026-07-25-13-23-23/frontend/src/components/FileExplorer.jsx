import { useState } from 'react';
import {
  Folder, File, ChevronDown, ChevronRight,
  Code2, FileJson, FileText, Settings
} from 'lucide-react';

const EXT_ICONS = {
  '.py': '🐍', '.js': '📜', '.ts': '📘', '.jsx': '⚛️', '.tsx': '⚛️',
  '.java': '☕', '.go': '🔵', '.rs': '🦀', '.json': '📋', '.yaml': '📋',
  '.yml': '📋', '.md': '📝', '.html': '🌐', '.css': '🎨', '.sql': '🗃️',
};

function TreeNode({ name, data, depth, analyses, onSelectFile }) {
  const [expanded, setExpanded] = useState(depth < 1);
  const isFile = data?.type === 'file';

  if (isFile) {
    const ext = data.extension || '';
    const icon = EXT_ICONS[ext] || '📄';

    return (
      <div
        className="file-tree-item"
        style={{ paddingLeft: `${depth * 20 + 12}px` }}
        onClick={() => onSelectFile(name)}
      >
        <span style={{ fontSize: 14, flexShrink: 0 }}>{icon}</span>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {name}
        </span>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {data.size ? `${Math.round(data.size / 1024)}KB` : ''}
        </span>
      </div>
    );
  }

  const entries = Object.entries(data || {}).sort(([, a], [, b]) => {
    const aIsFile = a?.type === 'file';
    const bIsFile = b?.type === 'file';
    if (aIsFile === bIsFile) return 0;
    return aIsFile ? 1 : -1;
  });

  return (
    <div>
      <div
        className="file-tree-item"
        style={{ paddingLeft: `${depth * 20 + 12}px`, fontWeight: 500 }}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <Folder size={14} style={{ color: '#6c5ce7', flexShrink: 0 }} />
