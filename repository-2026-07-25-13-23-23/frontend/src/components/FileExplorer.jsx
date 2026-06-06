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

        <span>{name}</span>
      </div>
      {expanded && entries.map(([key, value]) => (
        <TreeNode
          key={key} name={key} data={value} depth={depth + 1}
          analyses={analyses} onSelectFile={onSelectFile}
        />
      ))}
    </div>
  );
}

export default function FileExplorer({ fileTree, fileAnalyses }) {
  const [selectedFile, setSelectedFile] = useState(null);

  const findAnalysis = (filename) => {
    return fileAnalyses.find(a => a.path?.endsWith(filename));
  };

  const analysis = selectedFile ? findAnalysis(selectedFile) : null;

  return (
    <div className="animate-fade-in">
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: 8 }}>
        📁 File Explorer
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: '0.9rem' }}>
        Browse project files and their AI-generated analysis
      </p>

      <div style={{ display: 'flex', gap: 20 }}>
        {/* File Tree */}
        <div style={{
          width: 320, minWidth: 320, background: 'var(--bg-card)',
          border: '1px solid var(--border-color)', borderRadius: 12,
          padding: '12px 0', maxHeight: 600, overflow: 'auto',
        }}>
          {Object.entries(fileTree).map(([key, value]) => (
            <TreeNode
              key={key} name={key} data={value} depth={0}
              analyses={fileAnalyses}
              onSelectFile={setSelectedFile}
            />
          ))}
        </div>


        {/* Analysis Panel */}
        <div style={{ flex: 1 }}>
          {analysis ? (
            <div className="glass-card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 4 }}>
                {analysis.path}
              </h3>
              <span style={{
                fontSize: '0.8rem', color: '#6c5ce7',
                background: 'rgba(108, 92, 231, 0.12)',
                padding: '2px 8px', borderRadius: 4,
              }}>
                {analysis.language}
              </span>

              <div style={{ marginTop: 20 }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>
                  Summary
                </h4>
                <p style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>
                  {analysis.summary || 'No summary available'}
                </p>
              </div>

              {analysis.functions?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>
                    Functions ({analysis.functions.length})
                  </h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {analysis.functions.map((fn, i) => (
                      <code key={i} style={{
                        fontSize: '0.8rem', padding: '3px 10px',
                        background: 'rgba(108, 92, 231, 0.08)',
                        borderRadius: 6, color: '#a78bfa',
                        fontFamily: "'JetBrains Mono', monospace",
                      }}>{fn}</code>
                    ))}
                  </div>
                </div>
              )}

              {analysis.classes?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>
                    Classes ({analysis.classes.length})
                  </h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {analysis.classes.map((cls, i) => (
                      <code key={i} style={{
                        fontSize: '0.8rem', padding: '3px 10px',
                        background: 'rgba(76, 175, 80, 0.08)',
                        borderRadius: 6, color: '#4caf50',
                        fontFamily: "'JetBrains Mono', monospace",
                      }}>{cls}</code>

                    ))}
                  </div>
                </div>
              )}

              {analysis.key_logic && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>
                    Key Logic
                  </h4>
                  <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                    {analysis.key_logic}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              height: 300, color: 'var(--text-muted)', flexDirection: 'column', gap: 8,
            }}>
              <Code2 size={32} />
              <p>Select a file to view its analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
