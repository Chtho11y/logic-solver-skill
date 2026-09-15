/**
 * Right-hand DSL source pane. Solve posts this text as `source`, so authors
 * can try a rule without editing `impls/*.dsl` on disk.
 */

import { useEffect, useMemo, useRef } from "react";

export interface DslEditorProps {
  source: string;
  original: string;
  errorLine?: number;
  errorMessage?: string;
  onChange: (source: string) => void;
  onSolve?: () => void;
}

export function DslEditor(props: DslEditorProps) {
  const { source, original, errorLine, errorMessage, onChange, onSolve } = props;
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const gutterRef = useRef<HTMLPreElement>(null);
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
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      onSolve?.();
      return;
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
        <textarea
          ref={textareaRef}
          className="dsl-textarea"
          spellCheck={false}
          value={source}
          onChange={(e) => onChange(e.target.value)}
          onScroll={syncScroll}
          onKeyDown={onKeyDown}
          placeholder="选择谜题后会载入 impls/<key>.dsl"
        />
      </div>
      {errorMessage && (
        <div className="dsl-error">
          {errorLine ? `第 ${errorLine} 行 · ` : ""}
          {errorMessage}
        </div>
      )}
    </aside>
  );
}
