import { useEffect, useRef } from 'react';
import type { ImportPlan } from './importPlan';

export function ImportPreview({ plan, onConfirm, onCancel }: { plan: ImportPlan; onConfirm: () => void; onCancel: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog ref={ref} className="variable-editor import-preview" aria-labelledby="import-preview-title" onCancel={onCancel}>
    <header><strong id="import-preview-title">确认导入绑定</strong><button onClick={onCancel}>取消导入</button></header>
    {plan.review.map(reason => <p key={reason}>{reason}</p>)}
    <ul>{plan.bindings.map(binding => <li key={binding}>{binding}</li>)}</ul>
    <p>新建变量只保存题目线索，需要在 DSL 中引用才会约束答案。可以先取消并选择目标变量，再重新导入。</p>
    <footer><button onClick={onCancel}>返回工作区</button><button onClick={onConfirm}>确认导入</button></footer>
  </dialog>;
}
