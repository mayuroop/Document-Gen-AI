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
