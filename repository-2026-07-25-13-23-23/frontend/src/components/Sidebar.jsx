import {
  FileText, BarChart3, Code2, FolderTree,
  ChevronDown, ChevronRight, Folder, File,
  GitBranch, Network, Workflow, Database
} from 'lucide-react';
import { useState } from 'react';

const VIEW_ITEMS = [
  { key: 'docs', label: 'Documentation', icon: <FileText size={16} /> },
  { key: 'diagrams', label: 'Diagrams', icon: <BarChart3 size={16} /> },
  { key: 'api', label: 'API Explorer', icon: <Code2 size={16} /> },
  { key: 'files', label: 'File Explorer', icon: <FolderTree size={16} /> },
];

const DIAGRAM_ITEMS = [
  { key: 'architecture', label: 'Architecture', icon: <Network size={14} /> },
  { key: 'sequence', label: 'Sequence', icon: <GitBranch size={14} /> },
  { key: 'flowchart', label: 'Flowchart', icon: <Workflow size={14} /> },
  { key: 'er', label: 'ER Diagram', icon: <Database size={14} /> },
];

function FileTreeNode({ name, data, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isFile = data?.type === 'file';

  if (isFile) {
    return (
      <div className="file-tree-item" style={{ paddingLeft: `${depth * 16 + 8}px` }}>
        <File size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {name}
        </span>
      </div>
    );
  }

  const entries = Object.entries(data || {});

  return (
    <div>
      <div
        className="file-tree-item"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <Folder size={14} style={{ color: '#6c5ce7', flexShrink: 0 }} />
        <span style={{ fontWeight: 500 }}>{name}</span>
      </div>
      {expanded && entries.map(([key, value]) => (
        <FileTreeNode key={key} name={key} data={value} depth={depth + 1} />
