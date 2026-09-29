import { useEffect, useRef, useState } from 'react';
import { grammar, libraries, highlight, type Completion } from './dslLanguage';
export function DslDocs({ builtins, error, onClose }: { builtins: Completion[]; error: string; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [section, setSection] = useState('syntax');
  const [query, setQuery] = useState('');
  useEffect(() => { ref.current?.showModal(); }, []);
  const match = (text: string) => text.toLowerCase().includes(query.toLowerCase());
  return <dialog ref={ref} className="dsl-docs" onCancel={onClose}>
    <header><strong>DSL 文档</strong><button onClick={onClose}>关闭文档</button></header>
    <nav>{[['syntax', '语法规则'], ['builtins', 'Builtin 函数'], ['library', '规则库']].map(([id, label]) => <button key={id} aria-pressed={section === id} onClick={() => setSection(id)}>{label}</button>)}</nav>
    <input aria-label="搜索文档" placeholder="搜索语法、函数或规则库…" value={query} onChange={e => setQuery(e.target.value)} />
    <div className="dsl-doc-content">
      {section === 'syntax' && grammar.split(/(?=^## )/m).filter(match).map((text, i) => <pre key={i}>{text}</pre>)}
      {section === 'builtins' && <>{error && <p role="alert">{error}</p>}{builtins.filter(item => match(`${item.name} ${item.doc} ${item.signature}`)).map(item => <article key={item.name}><strong>{item.signature || item.name}</strong><small>{item.category}</small><p>{item.doc}</p></article>)}</>}
      {section === 'library' && Object.entries(libraries).filter(([name, text]) => match(name + text)).map(([name, text]) => <details key={name}><summary>{name} · import "{name}"</summary><pre>{highlight(text)}</pre></details>)}
    </div>
  </dialog>;
}
