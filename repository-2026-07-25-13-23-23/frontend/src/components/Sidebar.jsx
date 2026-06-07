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

      ))}
    </div>
  );
}

export default function Sidebar({
  sections, activeSection, setActiveSection,
  activeView, setActiveView, fileTree,
  activeDiagram, setActiveDiagram,
}) {
  const [docsExpanded, setDocsExpanded] = useState(true);
  const [diagramsExpanded, setDiagramsExpanded] = useState(true);
  const [filesExpanded, setFilesExpanded] = useState(false);

  return (
    <div style={{
      width: 280,
      minWidth: 280,
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-color)',
      overflowY: 'auto',
      flexShrink: 0,
    }}>
      {/* View Tabs */}
      <div style={{ padding: '12px 8px', borderBottom: '1px solid var(--border-color)' }}>
        <p style={{
          fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px',
          color: 'var(--text-muted)', padding: '0 8px', marginBottom: 8, fontWeight: 600,
        }}>Views</p>
        {VIEW_ITEMS.map(item => (
          <div
            key={item.key}
            className={`sidebar-item ${activeView === item.key ? 'active' : ''}`}
            onClick={() => setActiveView(item.key)}
          >
            {item.icon}
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      {/* Documentation Sections */}
      <div style={{ padding: '12px 0', borderBottom: '1px solid var(--border-color)' }}>
        <div
          style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '0 16px',
            cursor: 'pointer', marginBottom: 8,
          }}
          onClick={() => setDocsExpanded(!docsExpanded)}
        >
          {docsExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <p style={{
            fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px',
