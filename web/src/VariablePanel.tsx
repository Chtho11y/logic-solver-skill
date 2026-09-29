import type { ReactNode } from 'react';

export type VariableRow = { id: string; label: string; detail: string; output?: boolean };

const Icon = ({ children, off }: { children: ReactNode; off?: boolean }) => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}{off && <path d="m3 3 18 18" />}</svg>;
const Eye = ({ off }: { off?: boolean }) => <Icon off={off}><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></Icon>;
const Clue = ({ off }: { off?: boolean }) => <Icon off={off}><path d="M4 20h4L19 9l-4-4L4 16v4Z" /><path d="m13.5 6.5 4 4" /></Icon>;
const Answer = ({ off }: { off?: boolean }) => <Icon off={off}><circle cx="12" cy="12" r="9" /><path d="m8 12.5 2.8 2.8L16.5 9" /></Icon>;
const Solo = () => <Icon><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" /><circle cx="12" cy="12" r="2.5" fill="currentColor" /></Icon>;

export function VariablePanel({ rows, active, hidden, onSelect, onHide, parts, onPart, onEdit }: {
  rows: VariableRow[];
  active: string;
  hidden: Record<string, boolean>;
  onSelect: (id: string) => void;
  onHide: (ids: string[], hide: boolean) => void;
  parts: Record<string, boolean>;
  onPart: (key: string, hide: boolean) => void;
  onEdit: (id: string) => void;
}) {
  const ids = rows.map(r => r.id);
  const part = (row: VariableRow, prefix: 'in' | 'out', name: string, title: string, icon: (off: boolean) => ReactNode) => {
    const key = `${prefix}:${row.id}`, shown = !hidden[row.id] && !parts[key];
    return <button className={`variable-toggle ${prefix === 'out' ? 'answer' : 'clue'}`} aria-label={`${row.label} ${name}`} aria-pressed={shown} title={`${shown ? '隐藏' : '显示'}${title}`} onClick={() => onPart(key, shown)}>{icon(!shown)}</button>;
  };
  return <aside className="variables-panel" aria-label="变量总览">
    <div className="variables-heading">
      <strong>变量</strong><span className="variables-count">{rows.length}</span>
      <div className="variables-actions">
        <button className="variable-toggle" aria-label="全部显示" title="全部显示" onClick={() => onHide(ids, false)}><Eye /></button>
        <button className="variable-toggle" aria-label="全部隐藏" title="全部隐藏" onClick={() => onHide(ids, true)}><Eye off /></button>
      </div>
    </div>
    {!rows.length && <p className="variables-empty">选择绘制工具后新增变量，或导入预设。</p>}
    <div className="variables-list">
      {rows.map(row => {
        const solo = !hidden[row.id] && rows.every(r => r.id === row.id || hidden[r.id]);
        return <div key={row.id} className={`variable-row ${active === row.id ? 'active' : ''} ${hidden[row.id] ? 'hidden' : ''}`}>
          <button className="variable-toggle variable-eye" aria-label={`${hidden[row.id] ? '显示' : '隐藏'}变量 ${row.label}`} aria-pressed={!hidden[row.id]} title="显示/隐藏该变量的线索和求解结果" onClick={() => onHide([row.id], !hidden[row.id])}><Eye off={hidden[row.id]} /></button>
          <button className="variable-main" disabled={row.id === '__manual'} aria-pressed={active === row.id} title={row.detail} onClick={() => onSelect(row.id)}><strong>{row.label}</strong><small>{row.detail}</small></button>
          <div className="variable-tools">
            {row.id !== '__manual' ? part(row, 'in', '题目线索', '题目线索', off => <Clue off={off} />) : <span className="variable-toggle-spacer" />}
            {row.id !== '__manual' && row.output ? part(row, 'out', '求解答案', '求解答案', off => <Answer off={off} />) : <span className="variable-toggle-spacer" />}
            <button className="variable-toggle variable-solo" aria-label={`仅显示 ${row.label}`} aria-pressed={solo} title={solo ? '恢复显示全部变量' : '仅显示该变量'} onClick={() => solo ? onHide(ids, false) : (onHide(ids.filter(id => id !== row.id), true), onHide([row.id], false))}><Solo /></button>
            {!row.id.startsWith('__') && <button className="variable-toggle" aria-label={`编辑变量 ${row.label}`} title="编辑名称、值域、说明或删除" onClick={() => onEdit(row.id)}>⋯</button>}
          </div>
        </div>;
      })}
    </div>
    <p className="variables-hint">“绘制到”决定新笔画归属，切换变量不会移动已有笔画。图标依次控制：整体显隐、题目线索、求解答案、仅显示；隐藏不影响求解。</p>
  </aside>;
}
