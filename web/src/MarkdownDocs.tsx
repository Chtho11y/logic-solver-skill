import type { ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function markdownHeadingId(text: string) {
  return text.toLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, '').trim().replace(/\s+/g, '-');
}
function plainText(children: ReactNode): string {
  if (Array.isArray(children)) return children.map(plainText).join('');
  if (children && typeof children === 'object' && 'props' in children) return plainText(children.props.children);
  return typeof children === 'string' || typeof children === 'number' ? String(children) : '';
}

/** Markdown is rendered as React elements. HTML and unsafe URL schemes stay inert. */
export function MarkdownDocs({ source, onLocalLink }: { source: string; onLocalLink?: (href: string) => void }) {
  const heading = (Tag: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6') => ({ children }: { children?: ReactNode }) => <Tag id={markdownHeadingId(plainText(children))}>{children}</Tag>;
  return <div className="dsl-markdown"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
    h1: heading('h1'), h2: heading('h2'), h3: heading('h3'), h4: heading('h4'), h5: heading('h5'), h6: heading('h6'),
    table: ({ children }) => <div className="dsl-table-scroll" tabIndex={0}><table>{children}</table></div>,
    a: ({ href, children }) => {
      if (!href) return <span>{children}</span>;
      if (href.startsWith('#')) return <a href={href} onClick={e => { e.preventDefault(); let id: string; try { id = decodeURIComponent(href.slice(1)); } catch { return; } const dialog = e.currentTarget.closest('dialog'); const target = Array.from(dialog?.querySelectorAll('[id]') ?? []).find(el => el.id === id); target?.scrollIntoView({ block: 'start' }); }}>{children}</a>;
      if (/^https?:\/\//i.test(href)) return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
      return onLocalLink ? <a href={href} onClick={e => { e.preventDefault(); onLocalLink(href); }}>{children}</a> : <span title={href}>{children}</span>;
    },
    img: ({ alt }) => <span>{alt}</span>,
  }}>{source}</ReactMarkdown></div>;
}
