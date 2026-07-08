/**
 * Mermaid code sanitizer — shared utility.
 * Fixes common AI/LLM-generated syntax issues for Mermaid.js v10.
 */

/**
 * Check if a line looks like LLM commentary rather than mermaid code.
 */
function isCommentaryLine(line) {
  const commentaryPatterns = [
    /^(This|The|Here|Above|Below|I |In |It |As |For |Please|You |We )/i,
    /^(This diagram|This represents|The above|The diagram)/i,
    /\b(represents|illustrates|shows how|demonstrates|depicts)\b/i,
    /^(Remember|Important|Tip|Warning|Info):/i,
    /^(Based on|According to|As you can see)/i,
    /^\*\*Note/i,
    /^Note:\s+[A-Z]/,
    /^Note\s+that\b/i,
    /^[A-Z][a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+/,
  ];

  const mermaidPatterns = [
    /^\s*(graph|flowchart|sequenceDiagram|erDiagram|classDiagram|subgraph|end)\b/,
    /^\s*\w+\s*[\[\({]/,
    /^\s*\w+\s*--/,
    /^\s*\w+\s*-[->]/,
    /^\s*\w+\s*==/,
    /^\s*\w+\s*\|\|/,
    /^\s*(participant|alt|else|loop|opt|rect|par)\b/,
    /^\s*Note\s+(over|left of|right of)\b/,
    /^\s*(string|int|float|boolean|datetime)\s+/,
    /^\s*\}/,
    /^\s*\w+\s*\{/,
    /-->|==>|->>|-->>|-.->/, 
  ];

  if (mermaidPatterns.some(p => p.test(line))) return false;
  if (commentaryPatterns.some(p => p.test(line))) return true;
  return false;
}

/**
 * Detect where mermaid diagram code ends and strip LLM commentary after it.
 */
function truncateAfterDiagram(code) {
  const lines = code.split('\n');
  let lastValidLine = lines.length - 1;

  for (let i = lines.length - 1; i >= 0; i--) {
    const trimmed = lines[i].trim();
    if (!trimmed) continue;
    if (isCommentaryLine(trimmed)) {
      lastValidLine = i - 1;
      continue;
    }
    break;
  }

  for (let i = 3; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!trimmed) continue;
    if (isCommentaryLine(trimmed) && trimmed.length > 40) {
      lastValidLine = Math.min(lastValidLine, i - 1);
      break;
    }
  }

  return lines.slice(0, lastValidLine + 1).join('\n').trim();
}

/**
 * Sanitize AI-generated mermaid code to fix common syntax issues.
 */
export function sanitizeMermaidCode(code) {
  if (!code) return '';
  let c = code.trim();

  // 1. Remove markdown fences and leaked LLM special tokens
  c = c.replace(/<[｜|]?(begin|end)?[▁_]?(of)?[▁_]?(sentence|text)[｜|]?>/gi, '');
  c = c.replace(/^```[\w]*\s*\n?/gm, '');
  c = c.replace(/```\s*$/gm, '');
  c = c.replace(/```/g, '');
  c = c.trim();

  // 2. Ensure a valid diagram type declaration exists
  const validStarts = [
    'graph ', 'graph\n', 'flowchart ', 'flowchart\n',
    'sequenceDiagram', 'erDiagram', 'classDiagram',
    'stateDiagram', 'gantt', 'pie', 'gitgraph',
  ];
  const hasValidStart = validStarts.some(s => c.startsWith(s));
  if (!hasValidStart) {
    if (c.includes('->>') || c.includes('participant')) {
      c = 'sequenceDiagram\n' + c;
    } else if ((c.includes('||') || c.includes('}')) && c.includes('{')) {
      c = 'erDiagram\n' + c;
    } else {
      c = 'graph TD\n' + c;
    }
  }

  // 3. Strip trailing LLM commentary
  c = truncateAfterDiagram(c);

  // 4. Collapse excessive blank lines
  c = c.replace(/\n{3,}/g, '\n\n');

  // 5. Fix graph / flowchart diagrams
  if (c.startsWith('graph') || c.startsWith('flowchart')) {
    c = c.replace(/\[([^\]]*)\]/g, (match, inner) => {
      let fixed = inner
        .replace(/\(/g, ' ').replace(/\)/g, '')
        .replace(/,\s*/g, ' ').replace(/\.\.\./g, '')
        .replace(/etc\./gi, 'etc').replace(/"/g, "'")
        .replace(/;/g, ' ').trim();
      fixed = fixed.replace(/^[\s\-–—]+/, '').trim();
      return `[${fixed || 'Node'}]`;
    });
    c = c.replace(/(\w)\s*-+\s*>\s*(\w)/g, '$1 --> $2');
  }

  // 6. Fix sequence diagrams
  if (c.startsWith('sequenceDiagram')) {
    const lines = c.split('\n');
    const fixed = lines.map(line => {
      let l = line;
      l = l.replace(/-+\s*>\s*>/g, '->>');
      l = l.replace(/--\s*>>/g, '-->>');
      l = l.replace(/-\s*>>/g, '->>');
      if (l.trim().startsWith('participant')) {
        l = l.replace(/participant\s+(.+)/, (m, name) =>
          `participant ${name.replace(/[^a-zA-Z0-9_ ]/g, '').trim()}`
        );
      }
      return l;
    });
    c = fixed.join('\n');
  }

  // 7. Fix ER diagrams
  if (c.startsWith('erDiagram')) {
    c = c.replace(/^(\s*)([A-Z][A-Z0-9_-]+)/gm, (match, indent, name) => {
      if (name === 'erDiagram') return match;
      return indent + name.replace(/-/g, '_');
    });

    const lines = c.split('\n');
    const fixedLines = [];
    let inBlock = false;
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.endsWith('{')) {
        if (inBlock) fixedLines.push('    }');
        inBlock = true;
        fixedLines.push(line);
      } else if (trimmed === '}') {
        if (inBlock) {
          inBlock = false;
          fixedLines.push(line);
        }
      } else {
        if (inBlock && trimmed !== '') {
          // Inside an entity block, attributes shouldn't have colons or special chars
          let cleanLine = line.replace(/[:"']/g, '').trim();
          const tokens = cleanLine.split(/\s+/);
          
          if (tokens.length >= 2) {
            const type = tokens[0];
            const nameTokens = [];
            const keyTokens = [];
            
            for (let i = 1; i < tokens.length; i++) {
              const t = tokens[i];
              if (['PK', 'FK', 'UK'].includes(t.toUpperCase())) {
                keyTokens.push(t.toUpperCase());
              } else {
                nameTokens.push(t);
              }
            }
            
            const name = nameTokens.join('_');
            fixedLines.push(`        ${type} ${name} ${keyTokens.join(' ')}`.trim());
          } else {
            fixedLines.push('        ' + cleanLine);
          }
        } else {
          fixedLines.push(line);
        }
      }
    }
    if (inBlock) fixedLines.push('    }');
    c = fixedLines.join('\n');
  }

  // 8. Final cleanup
  c = c.replace(/`+\s*$/g, '').trim();

  return c;
}
