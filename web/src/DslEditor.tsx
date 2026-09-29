/**
 * Right-hand DSL source pane. Solve posts this text as `source`, so authors
 * can try a rule without editing `impls/*.dsl` on disk.
 */

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { completionKind, completions, highlight, libraries, type Completion, type CompletionKind } from './dslLanguage';
import { DslDocs } from './DslDocs';
import { createPortal } from 'react-dom';

export interface DslEditorProps {
  source: string;
  original: string;
  errorLine?: number;
  errorMessage?: string;
  onChange: (source: string) => void;
  onSolve?: () => void;
  variables?: string[];
}

const KIND_GLYPH: Record<CompletionKind, string> = { keyword: '≡', function: 'ƒ', variable: 'x', constant: 'π', module: '{}' };
const KIND_LABEL: Record<CompletionKind, string> = { keyword: '关键字', function: '函数', variable: '变量', constant: '常量', module: '规则库' };

function CompletionPopup({ listRef, style, items, chosen, typed, onAccept }: {
  listRef: React.RefObject<HTMLDivElement>;
  style: React.CSSProperties;
  items: Completion[];
  chosen: number;
  typed: number;
  onAccept: (item: Completion) => void;
}) {
  const current = items[chosen];
  const currentKind = current ? completionKind(current) : 'variable';
  return <div className="dsl-completion" style={style} onMouseDown={e => e.preventDefault()}>
    <div ref={listRef} className="dsl-completion-list" role="listbox" aria-label="DSL 补全" aria-activedescendant={`dsl-completion-${chosen}`}>
      {items.map((item, i) => {
        const kind = completionKind(item);
        const signature = item.signature || item.name;
        const params = signature.startsWith(item.name) ? signature.slice(item.name.length) : '';
        return <div key={item.name} id={`dsl-completion-${i}`} role="option" aria-selected={i === chosen} aria-label={signature} title={item.doc} className="dsl-completion-item" onClick={() => onAccept(item)}>
          <span className={`dsl-kind kind-${kind}`} aria-hidden="true">{KIND_GLYPH[kind]}</span>
          <span className="dsl-completion-label"><mark>{item.name.slice(0, typed)}</mark>{item.name.slice(typed)}{params && <span className="dsl-completion-params">{params}</span>}</span>
          {item.source && <span className="dsl-completion-source">{item.source}</span>}
        </div>;
      })}
    </div>
    {current && <div className="dsl-completion-detail">
      <div className="dsl-completion-signature"><span className={`dsl-kind kind-${currentKind}`} aria-hidden="true">{KIND_GLYPH[currentKind]}</span><code>{current.signature || current.name}</code><small>{KIND_LABEL[currentKind]}</small></div>
      {current.doc && <p>{current.doc}</p>}
    </div>}
  </div>;
}

export function DslEditor(props: DslEditorProps) {
  const { source, original, errorLine, errorMessage, onChange, onSolve } = props;
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const gutterRef = useRef<HTMLPreElement>(null);
  const highlightRef = useRef<HTMLPreElement>(null);
  const pendingCaret = useRef<number | null>(null);
  useLayoutEffect(() => {
    if (pendingCaret.current !== null) { textareaRef.current?.focus(); textareaRef.current?.setSelectionRange(pendingCaret.current, pendingCaret.current); pendingCaret.current = null; }
  }, [source]);
  const [builtins, setBuiltins] = useState<Completion[]>([]);
  const [docsError, setDocsError] = useState('');
  const [docsOpen, setDocsOpen] = useState(false);
  const [suggest, setSuggest] = useState<{ start: number; end: number; items: Completion[] } | null>(null);
  const [chosen, setChosen] = useState(0);
  const completionRef = useRef<HTMLDivElement>(null);
  const [popup, setPopup] = useState<{ left: number; top?: number; bottom?: number; width: number; maxHeight: number }>({ left: 0, top: 0, width: 360, maxHeight: 260 });
  useLayoutEffect(() => {
    if (!suggest) return;
    const position = () => {
      const el = textareaRef.current;
      if (!el) return;
      const style = getComputedStyle(el);
      const mirror = document.createElement('div');
      Object.assign(mirror.style, { position: 'fixed', left: '-10000px', top: '0', visibility: 'hidden', whiteSpace: 'pre', font: style.font, letterSpacing: style.letterSpacing, tabSize: style.tabSize, padding: style.padding, border: '0', margin: '0' });
      mirror.textContent = el.value.slice(0, el.selectionStart);
      const marker = document.createElement('span'); marker.textContent = '\u200b'; mirror.append(marker); document.body.append(mirror);
      const origin = mirror.getBoundingClientRect(), caret = marker.getBoundingClientRect(), bounds = el.getBoundingClientRect();
      const x = bounds.left + caret.left - origin.left - el.scrollLeft;
      const y = bounds.top + caret.top - origin.top - el.scrollTop;
      mirror.remove();
      const lineHeight = parseFloat(style.lineHeight) || 18;
      const width = Math.min(380, Math.max(220, bounds.width - 16), innerWidth - 16);
      const below = Math.min(bounds.bottom, innerHeight) - y - lineHeight - 4;
      const above = y - Math.max(0, bounds.top) - 4;
      const downward = below >= Math.min(160, above);
      const height = Math.min(260, Math.max(64, downward ? below : above));
      const left = Math.max(8, Math.min(x - 22, innerWidth - width - 8));
      setPopup(downward ? { left, top: Math.max(8, y + lineHeight + 2), width, maxHeight: height } : { left, bottom: Math.max(8, innerHeight - y + 2), width, maxHeight: height });
    };
    position();
    const observer = new ResizeObserver(position); observer.observe(textareaRef.current!);
    window.addEventListener('resize', position); window.addEventListener('scroll', position, true);
    return () => { observer.disconnect(); window.removeEventListener('resize', position); window.removeEventListener('scroll', position, true); };
  }, [suggest, source]);
  useLayoutEffect(() => {
    const menu = completionRef.current, item = menu?.children[chosen] as HTMLElement | undefined;
    if (menu && item) { if (item.offsetTop < menu.scrollTop) menu.scrollTop = item.offsetTop; else if (item.offsetTop + item.offsetHeight > menu.scrollTop + menu.clientHeight) menu.scrollTop = item.offsetTop + item.offsetHeight - menu.clientHeight; }
  }, [chosen]);
  useEffect(() => {
    fetch('/api/builtins').then(r => { if (!r.ok) throw new Error('Builtin 文档加载失败'); return r.json(); }).then(data => setBuiltins(data.entries)).catch(e => setDocsError(String(e)));
  }, []);
  function updateSuggestions(text: string, caret: number, force = false) {
    const line = text.slice(0, caret).split('\n').pop() ?? '';
    const importing = line.match(/^\s*import\s+["']([^"']*)$/);
    const prefix = importing?.[1] ?? line.match(/[A-Za-z_]\w*$/)?.[0] ?? '';
    if ((!prefix && !force) || (!importing && /#[^\n]*$|["'][^"']*$/.test(line))) { setSuggest(null); return; }
    const candidates = importing ? Object.keys(libraries).map((name): Completion => ({ name, signature: name, doc: `可导入规则库 import "${name}"`, kind: 'module', source: 'lib' })) : completions(text, props.variables ?? [], builtins);
    const items = candidates.filter(item => item.name.startsWith(prefix)).slice(0, 30);
    setChosen(0); setSuggest(items.length ? { start: caret - prefix.length, end: caret, items } : null);
  }
  function accept(item: Completion) {
    if (!suggest) return;
    const next = source.slice(0, suggest.start) + item.name + source.slice(suggest.end);
    const caret = suggest.start + item.name.length;
    pendingCaret.current = caret; onChange(next); setSuggest(null);
  }
  const dirty = source !== original;
  const lines = useMemo(() => source.split("\n"), [source]);
  const lineCount = Math.max(1, lines.length);

  useEffect(() => {
    if (!errorLine || errorLine < 1) return;
    const el = textareaRef.current;
    if (!el) return;
    const start = lines.slice(0, errorLine - 1).reduce((sum, line) => sum + line.length + 1, 0);
    const end = start + (lines[errorLine - 1]?.length ?? 0);
    el.focus();
    el.setSelectionRange(start, end);
    const lineHeight = 18;
    el.scrollTop = Math.max(0, (errorLine - 3) * lineHeight);
  }, [errorLine, lines]);

  function syncScroll() {
    const el = textareaRef.current;
    if (gutterRef.current && el) gutterRef.current.scrollTop = el.scrollTop;
    if (highlightRef.current && el) { highlightRef.current.scrollTop = el.scrollTop; highlightRef.current.scrollLeft = el.scrollLeft; }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.nativeEvent.isComposing) return;
    if ((e.ctrlKey || e.metaKey) && e.code === 'Space') { e.preventDefault(); updateSuggestions(source, e.currentTarget.selectionStart, true); return; }
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      onSolve?.();
      return;
    }
    if (suggest) {
      if (e.key === 'Escape') { e.preventDefault(); setSuggest(null); return; }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); setChosen(i => (i + (e.key === 'ArrowDown' ? 1 : suggest.items.length - 1)) % suggest.items.length); return; }
      if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); accept(suggest.items[chosen]); return; }
      if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(e.key)) setSuggest(null);
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const el = e.currentTarget;
      const before = source.slice(0, el.selectionStart);
      const line = before.split('\n').pop() ?? '';
      const indent = (line.match(/^\s*/)?.[0] ?? '') + (line.trimEnd().endsWith(':') ? '    ' : '');
      pendingCaret.current = el.selectionStart + 1 + indent.length;
      onChange(before + '\n' + indent + source.slice(el.selectionEnd)); return;
    }
    if (e.key !== "Tab") return;
    e.preventDefault();
    const el = e.currentTarget;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const next = source.slice(0, start) + "  " + source.slice(end);
    onChange(next);
    requestAnimationFrame(() => {
      el.selectionStart = el.selectionEnd = start + 2;
    });
  }

  return (
    <aside className="dsl-pane">
      <div className="dsl-toolbar">
        <strong>规则 DSL</strong>
        <button onClick={() => { setSuggest(null); setDocsOpen(true); }}>Doc 文档</button>
        {dirty && <span className="dsl-dirty">已修改</span>}
        <span className="dsl-hint">{lineCount} 行 · Ctrl+Enter 求解</span>
        <button
          className="ghost"
          disabled={!dirty}
          onClick={() => onChange(original)}
          title="恢复题型自带的 DSL"
        >
          重置规则
        </button>
      </div>
      <div className="dsl-editor">
        <pre className="dsl-gutter" ref={gutterRef} aria-hidden>
          {Array.from({ length: lineCount }, (_, i) => {
            const n = i + 1;
            return (
              <span key={n} className={n === errorLine ? "err" : undefined}>
                {n}
              </span>
            );
          })}
        </pre>
        <div className="dsl-code-area">
        <pre className="dsl-highlight" ref={highlightRef} aria-hidden="true">{highlight(source)}{'\n'}</pre>
        <textarea
          aria-label="规则 DSL"
          ref={textareaRef}
          className="dsl-textarea"
          spellCheck={false}
          value={source}
          onChange={(e) => { onChange(e.target.value); updateSuggestions(e.target.value, e.target.selectionStart); }}
          onClick={() => setSuggest(null)}
          onBlur={() => setSuggest(null)}
          onScroll={syncScroll}
          onKeyDown={onKeyDown}
          placeholder="在此编写规则，或导入预设作为起点"
        />
        {suggest && createPortal(<CompletionPopup listRef={completionRef} style={popup} items={suggest.items} chosen={chosen} typed={suggest.end - suggest.start} onAccept={accept} />, document.body)}
        </div>
      </div>
      <div className="dsl-shortcuts">Ctrl+Space 补全 · ↑↓ 选择 · Tab/Enter 接受 · Esc 关闭</div>
      {docsOpen && <DslDocs builtins={builtins} error={docsError} onClose={() => setDocsOpen(false)} />}
      {errorMessage && (
        <div className="dsl-error">
          {errorLine ? `第 ${errorLine} 行 · ` : ""}
          {errorMessage}
        </div>
      )}
    </aside>
  );
}
