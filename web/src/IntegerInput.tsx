import { useEffect, useState } from 'react';

/** Keep intermediate typing (empty, -, 1 of 12) away from destructive resizes. */
export function IntegerInput({ value, onCommit, label, min, max }: { value: number; onCommit: (value: number) => void; label: string; min?: number; max?: number }) {
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  return <input aria-label={label} type="number" min={min} max={max} value={draft} onChange={e => setDraft(e.target.value)} onBlur={() => {
    const next = Number(draft);
    if (draft.trim() && Number.isSafeInteger(next) && (min === undefined || next >= min) && (max === undefined || next <= max)) {
      if (next !== value) onCommit(next);
    } else setDraft(String(value));
  }} onKeyDown={e => {
    if (e.key === 'Enter') { e.preventDefault(); e.currentTarget.blur(); }
    if (e.key === 'Escape') { e.preventDefault(); setDraft(String(value)); }
  }} />;
}
