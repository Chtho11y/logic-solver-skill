import { useEffect, useRef, useState } from 'react';
import { grammar, libraries, highlight, type Completion } from './dslLanguage';
import { MarkdownDocs } from './MarkdownDocs';

const repositoryDocs = import.meta.glob('../../docs/*.md', { query: '?raw', import: 'default', eager: true }) as Record<string, string>;
const syntaxSections = grammar.split(/(?=^## )/m).map((text, index) => ({ text, id: `syntax-section-${index}`, title: text.match(/^#{1,2} (.+)/m)?.[1] ?? '概览' }));

export function DslDocs({ builtins, error, onClose }: { builtins: Completion[]; error: string; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [section, setSection] = useState('syntax');
  const [query, setQuery] = useState('');
  const [linkedDoc, setLinkedDoc] = useState<{ title: string; source: string } | null>(null);
  const [linkError, setLinkError] = useState('');
  useEffect(() => { ref.current?.showModal(); }, []);
  useEffect(() => { contentRef.current?.scrollTo(0, 0); }, [section, query, linkedDoc]);
  const match = (text: string) => text.toLowerCase().includes(query.trim().toLowerCase());
  const syntax = syntaxSections.filter(item => match(item.text));
  const functions = builtins.filter(item => match(`${item.name} ${item.doc} ${item.signature}`));
  const modules = Object.entries(libraries).filter(([name, text]) => match(name + text));
  const count = section === 'syntax' ? syntax.length : section === 'builtins' ? functions.length : modules.length;
  function openLocalLink(href: string) {
    const filename = href.split('#')[0].split('/').pop();
    const entry = Object.entries(repositoryDocs).find(([path]) => path.split('/').pop() === filename);
    if (entry) { setLinkedDoc({ title: filename!, source: entry[1] }); setLinkError(''); }
    else setLinkError(`此链接指向仓库文件：${href}。请在仓库中查看。`);
  }
  return <dialog ref={ref} className="dsl-docs" aria-labelledby="dsl-doc-title" onCancel={onClose}>
    <header><strong id="dsl-doc-title">DSL 文档</strong><button onClick={onClose}>关闭文档</button></header>
    <nav aria-label="文档分类">{[['syntax', '语法规则'], ['builtins', 'Builtin 函数'], ['library', '规则库']].map(([id, label]) => <button key={id} aria-pressed={section === id && !linkedDoc} onClick={() => { setSection(id); setLinkedDoc(null); setLinkError(''); }}>{label}</button>)}</nav>
    {linkedDoc ? <div className="dsl-doc-search"><button onClick={() => setLinkedDoc(null)}>返回语法文档</button><span>{linkedDoc.title}</span></div> : <div className="dsl-doc-search"><input aria-label="搜索文档" placeholder="搜索当前分类的语法、函数或规则库…" value={query} onChange={e => setQuery(e.target.value)} /><span role="status">{count} 项</span></div>}
    <div className="dsl-doc-content" ref={contentRef}>
      {linkError && <p role="status">{linkError}</p>}
      {linkedDoc ? <MarkdownDocs source={linkedDoc.source} onLocalLink={openLocalLink} /> : <>
        {count === 0 && <p className="dsl-doc-empty">没有找到“{query}”。请尝试其他关键词或切换分类。</p>}
        {section === 'syntax' && <>
          {syntax.length > 1 && <nav className="dsl-doc-toc" aria-label="语法目录">{syntax.map(item => <button key={item.id} onClick={() => ref.current?.querySelector(`#${item.id}`)?.scrollIntoView({ block: 'start' })}>{item.title}</button>)}</nav>}
          {syntax.map(item => <section id={item.id} key={item.id}><MarkdownDocs source={item.text} onLocalLink={openLocalLink} /></section>)}
        </>}
        {section === 'builtins' && <>{error && <p role="alert">{error}</p>}{functions.map(item => <article key={item.name}><h2><code>{item.signature || item.name}</code></h2><small>{item.category}</small><MarkdownDocs source={item.doc} onLocalLink={openLocalLink} /></article>)}</>}
        {section === 'library' && modules.map(([name, text]) => <details key={name} open={query.trim() ? true : undefined}><summary>{name} · import "{name}"</summary><pre><code>{highlight(text)}</code></pre></details>)}
      </>}
    </div>
  </dialog>;
}
