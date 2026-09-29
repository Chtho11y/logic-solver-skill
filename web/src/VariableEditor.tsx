import { useEffect, useRef, useState } from 'react';
import type { VarSpec } from './types';

export function VariableEditor({ variable, onSave, onDelete, onClose }: {
  variable: VarSpec; onSave: (next: VarSpec) => string | undefined; onDelete: () => void; onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [name, setName] = useState(variable.name);
  const [doc, setDoc] = useState(variable.doc);
  const [domain, setDomain] = useState(variable.domain !== null);
  const [lo, setLo] = useState(String(variable.domain?.[0] ?? 0));
  const [hi, setHi] = useState(String(variable.domain?.[1] ?? 9));
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog ref={ref} className="variable-editor" aria-label={`编辑变量 ${variable.name}`} onCancel={onClose}>
    <form onSubmit={e => {
      e.preventDefault();
      if (domain && (!lo.trim() || !hi.trim() || !Number.isSafeInteger(+lo) || !Number.isSafeInteger(+hi) || +lo > +hi)) { setError('请填写有效的整数值域，最小值不能大于最大值。'); return; }
      setError(onSave({ ...variable, name: name.trim(), doc, domain: variable.type === 'cc' || !domain ? null : [+lo, +hi] }) ?? '');
    }}>
      <header><strong>编辑变量 · {variable.name}</strong><button type="button" onClick={onClose}>关闭</button></header>
      <label>名称<input aria-label="编辑变量名" value={name} onChange={e => setName(e.target.value)} required /></label>
      <p>类型：{variable.type === 'cc' ? '区域划分' : variable.type === 'constant' ? '题目线索' : '待求解变量'} · {variable.kind}</p>
      {variable.type !== 'cc' && <><label className="variable-domain"><input type="checkbox" checked={domain} onChange={e => setDomain(e.target.checked)} />限定值域</label>{domain && <div className="variable-range"><label>最小值<input aria-label="编辑最小值" type="number" value={lo} onChange={e => setLo(e.target.value)} /></label><label>最大值<input aria-label="编辑最大值" type="number" value={hi} onChange={e => setHi(e.target.value)} /></label></div>}</>}
      <label>说明<textarea aria-label="变量说明" value={doc} onChange={e => setDoc(e.target.value)} /></label>
      <p>改名会同步更新规则中的同名标识符、图层和样例绑定；注释和字符串保持原样。</p>
      {error && <p role="alert">{error}</p>}
      <footer><button type="submit">保存变量</button><button type="button" onClick={() => setDeleting(true)}>删除变量</button></footer>
      {deleting && <div className="variable-delete-confirm"><p>删除 {variable.name} 及其全部笔画？此操作不可撤销。DSL 中的引用会保留，需要手动修改相关规则。</p><button type="button" onClick={onDelete}>确认删除</button><button type="button" onClick={() => setDeleting(false)}>取消删除</button></div>}
    </form>
  </dialog>;
}
