import grammar from '../../puzzle/dsl/GRAMMAR.md?raw';
export { grammar };
export const libraries = Object.fromEntries(Object.entries(import.meta.glob('../../puzzle/lib/*.dsl', { query: '?raw', import: 'default', eager: true })).map(([path, source]) => [path.split('/').pop()!.replace(/\.dsl$/, ''), String(source)]));
export type CompletionKind = 'keyword' | 'function' | 'variable' | 'constant' | 'module';
export type Completion = { name: string; signature: string; doc: string; category?: string; kind?: CompletionKind; source?: string };
export function completionKind(item: Completion): CompletionKind {
  if (item.kind) return item.kind;
  if (item.category === 'Keyword') return 'keyword';
  if (item.category === 'Constant') return 'constant';
  return item.signature.includes('(') ? 'function' : 'variable';
}
export const keywords = ['let', 'for', 'in', 'if', 'else', 'def', 'return', 'import', 'use', 'and', 'or', 'not', 'xor', 'true', 'false'];
export function highlight(source: string) {
  const tokens = source.split(/(#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z_0-9]*\b)/g);
  return tokens.map((token, i) => <span key={i} className={token.startsWith('#') ? 'tok-comment' : /^['"]/.test(token) ? 'tok-string' : /^\d/.test(token) ? 'tok-number' : keywords.includes(token) ? 'tok-keyword' : /^\s*\(/.test(tokens[i + 1] ?? '') ? 'tok-function' : undefined}>{token}</span>);
}
export function completions(source: string, variables: string[], builtins: Completion[]): Completion[] {
  const entries = new Map<string, Completion>();
  for (const name of keywords) entries.set(name, { name, signature: name, doc: 'DSL 关键字', kind: 'keyword', source: 'keyword' });
  for (const item of builtins) if (/^[A-Za-z_]\w*$/.test(item.name)) entries.set(item.name, { ...item, kind: completionKind(item), source: 'builtin' });
  const modules = [...source.matchAll(/^\s*import\s+["']([^"']+)["']/gm)].map(m => m[1].replace(/\.dsl$/, ''));
  const visited = new Set<string>();
  function addFunctions(text: string, origin: string, source: string) {
    for (const m of text.matchAll(/^\s*def\s+(\w+)\s*\(([^)]*)\)/gm)) entries.set(m[1], { name: m[1], signature: `${m[1]}(${m[2]})`, doc: origin, kind: 'function', source });
  }
  function load(name: string) {
    if (visited.has(name) || !libraries[name]) return;
    visited.add(name); addFunctions(libraries[name], `库：${name}`, name);
    for (const m of libraries[name].matchAll(/^\s*import\s+["']([^"']+)["']/gm)) load(m[1]);
  }
  modules.forEach(load); addFunctions(source, '当前规则', 'local');
  for (const name of variables) entries.set(name, { name, signature: name, doc: '题目变量', kind: 'variable', source: 'puzzle' });
  for (const name of [...source.matchAll(/\b(?:let|for)\s+(\w+)/g)].map(m => m[1])) if (!variables.includes(name)) entries.set(name, { name, signature: name, doc: '局部名称', kind: 'variable', source: 'local' });
  return [...entries.values()];
}
