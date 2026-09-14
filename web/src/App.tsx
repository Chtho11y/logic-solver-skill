/**
 * Application shell: puzzle picker, penpa-style palette, board and solver.
 * Everything is layer/element driven — no puzzle-specific code lives here.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { Board } from "./Board";
import { editorOf } from "./editors";
import { makeViewport } from "./geometry";
import {
  clearLayer,
  defaultVisibility,
  emptyInstance,
  LAYERS_PREVIEW_KEY,
  layerValues,
  outsideText,
  paramEntry,
  previewFromLayers,
  setClue,
  setParamEntry,
} from "./instance";
import { DslEditor } from "./DslEditor";
import { Palette } from "./Palette";
import type {
  Brush,
  ImportResult,
  Instance,
  LayerSpec,
  PuzzleSpec,
  RuleEntry,
  Selection,
  SolveResult,
  SolverBackend,
} from "./types";

export function App() {
  const [puzzles, setPuzzles] = useState<PuzzleSpec[]>([]);
  const [spec, setSpec] = useState<PuzzleSpec | null>(null);
  const [rule, setRule] = useState<RuleEntry | null>(null);
  const [sample, setSample] = useState<Instance | null>(null);
  const [instance, setInstance] = useState<Instance | null>(null);
  const [result, setResult] = useState<SolveResult | null>(null);
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [activeId, setActiveId] = useState("");
  const [brushes, setBrushes] = useState<Record<string, Brush>>({});
  const [selection, setSelection] = useState<Selection | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [solverAvailable, setSolverAvailable] = useState(false);
  const [backends, setBackends] = useState<SolverBackend[]>([]);
  const [backend, setBackend] = useState("auto");
  const [dslSource, setDslSource] = useState("");
  const [originalSource, setOriginalSource] = useState("");
  const [importUrl, setImportUrl] = useState("");
  const [importBusy, setImportBusy] = useState(false);
  const [importNote, setImportNote] = useState("");

  useEffect(() => {
    api.puzzles().then(setPuzzles).catch(console.error);
    api.health()
      .then((h) => {
        setSolverAvailable(h.solver.available);
        setBackends(h.solver.backends);
      })
      .catch(() => setSolverAvailable(false));
  }, []);

  const activeLayer = spec?.layers.find((layer) => layer.id === activeId) ?? null;
  const brush: Brush = activeLayer ? brushes[activeLayer.id] ?? "cycle" : "cycle";

  async function choose(key: string) {
    const pendingUrl = importUrl.trim();
    const rebindPreview = spec?.key === LAYERS_PREVIEW_KEY && Boolean(pendingUrl);
    const data = await api.puzzle(key);
    const inst = data.sample ?? emptyInstance(data.puzzle);
    setSpec(data.puzzle);
    setRule(data.rule);
    setSample(data.sample);
    setInstance(inst);
    setVisible(defaultVisibility(data.puzzle));
    setResult(null);
    setSelection(null);
    setDraft("");
    const source = data.puzzle.source ?? "";
    setDslSource(source);
    setOriginalSource(source);
    const firstInput = data.puzzle.layers.find((layer) => layer.role === "input");
    setActiveId(firstInput?.id ?? data.puzzle.layers[0]?.id ?? "");
    if (rebindPreview) {
      const imported = await api.importUrl(pendingUrl, key);
      if (!imported.error) {
        await applyImport(imported);
      }
    }
  }

  const edit = useCallback(
    (layer: LayerSpec, key: string, value: number | null) => {
      setInstance((prev) => (prev ? setClue(prev, layer.var, key, value) : prev));
      setResult(null);
    },
    [],
  );

  // -- selection + keyboard editing -------------------------------------------

  const commit = useCallback(
    (sel: Selection | null, text: string) => {
      if (!sel || !spec || !instance) return;
      const layer = spec.layers.find((l) => l.id === sel.layerId);
      if (!layer) return;
      if (sel.kind === "point") {
        if (layer.element === "text") {
          const letter = text.trim().slice(-1).toUpperCase();
          const code = letter ? letter.charCodeAt(0) - 64 : 0;
          edit(layer, sel.key, code >= 1 && code <= 26 ? code : null);
        } else {
          const parsed = parseInt(text.trim(), 10);
          edit(layer, sel.key, Number.isNaN(parsed) ? null : parsed);
        }
        return;
      }
      const tokens = text.split(/[\s,]+/).filter(Boolean).map(Number).filter((n) => !Number.isNaN(n));
      const mode = layer.options?.mode;
      const value = tokens.length === 0 ? null : tokens.length === 1 && mode !== "list" ? tokens[0] : tokens;
      setInstance((prev) => (prev ? setParamEntry(prev, sel.side, sel.index, value) : prev));
      setResult(null);
    },
    [spec, instance, edit],
  );

  const select = useCallback(
    (next: Selection | null) => {
      commit(selection, draft);
      setSelection(next);
      if (!next || !spec || !instance) {
        setDraft("");
        return;
      }
      if (next.kind === "point") {
        const layer = spec.layers.find((l) => l.id === next.layerId);
        const current = layer ? layerValues(layer, instance, null)[next.key] : undefined;
        setDraft(current === undefined ? "" : String(current));
      } else {
        setDraft(outsideText(paramEntry(instance, next.side, next.index)));
      }
    },
    [commit, selection, draft, spec, instance],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!selection) return;
      const el = document.activeElement;
      if (el && (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA")) return;
      if (e.key === "Escape") {
        setSelection(null);
        setDraft("");
        return;
      }
      if (e.key === "Enter") {
        commit(selection, draft);
        setSelection(null);
        setDraft("");
        return;
      }
      if (e.key === "Backspace" || e.key === "Delete") {
        setDraft((d) => d.slice(0, -1));
        e.preventDefault();
        return;
      }
      if (/^[0-9a-zA-Z\- ,]$/.test(e.key)) {
        setDraft((d) => d + (e.key === "," ? " " : e.key));
        e.preventDefault();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selection, draft, commit]);

  async function applyImport(data: ImportResult) {
    const layerIds = data.layers.map((layer) => layer.id).join(", ");
    const key = data.puzzle || (spec && spec.key !== LAYERS_PREVIEW_KEY ? spec.key : "");
    if (data.instance && key) {
      if (!spec || spec.key !== key) {
        const loaded = await api.puzzle(key);
        setSpec(loaded.puzzle);
        setRule(loaded.rule);
        setSample(loaded.sample);
        const source = loaded.puzzle.source ?? "";
        setDslSource(source);
        setOriginalSource(source);
        const firstInput = loaded.puzzle.layers.find((layer) => layer.role === "input");
        setActiveId(firstInput?.id ?? loaded.puzzle.layers[0]?.id ?? "");
        setVisible(defaultVisibility(loaded.puzzle));
      }
      setInstance(data.instance);
      setResult(null);
      setSelection(null);
      const bits = [
        data.kind === "penpa" ? "Penpa+" : "puzz.link",
        `${data.rows}×${data.cols}`,
        data.title,
      ].filter(Boolean);
      const warn = data.warnings.length ? ` · ${data.warnings[0]}` : "";
      setImportNote(`${bits.join(" · ")} 已分层导入${layerIds ? `（${layerIds}）` : ""}${warn}`);
      return;
    }
    if (data.rows > 0 && data.cols > 0) {
      const preview = previewFromLayers(data);
      setSpec(preview.spec);
      setRule(null);
      setSample(null);
      setInstance(preview.instance);
      setVisible(defaultVisibility(preview.spec));
      setActiveId(preview.spec.layers[0]?.id ?? "");
      setDslSource("");
      setOriginalSource("");
      setResult(null);
      setSelection(null);
      setImportNote(
        `${data.kind === "penpa" ? "Penpa+" : "puzz.link"} · ${data.rows}×${data.cols} 已按图层解码（${layerIds}）。选择题型后再次导入即可绑定求解。`,
      );
      return;
    }
    setImportNote(data.warnings.join(" ") || "无法绑定到当前题型");
  }

  async function importFromUrl(raw?: string) {
    const url = (raw ?? importUrl).trim();
    if (!url) {
      setImportNote("请粘贴 Penpa+ 或 puzz.link 链接");
      return;
    }
    setImportUrl(url);
    setImportBusy(true);
    setImportNote("");
    try {
      const data = await api.importUrl(url, spec?.key);
      if (data.error) {
        setImportNote(data.error);
        return;
      }
      await applyImport(data);
    } catch (error) {
      setImportNote(String(error));
    } finally {
      setImportBusy(false);
    }
  }

  async function solve() {
    if (!instance) return;
    commit(selection, draft);
    setSelection(null);
    setBusy(true);
    try {
      const backendInfo = backends.find((item) => item.name === backend);
      setResult(await api.solve(instance, {
        backend,
        timeoutMs: backendInfo?.supportsTimeout === false ? null : 60000,
        source: dslSource.trim() ? dslSource : undefined,
      }));
    } catch (error) {
      setResult({ status: "error", message: String(error), constraints: 0, debug: [] });
    } finally {
      setBusy(false);
    }
  }

  function resize(rows: number, cols: number) {
    if (!spec || rows < 1 || cols < 1 || rows > 40 || cols > 40) return;
    setInstance(emptyInstance(spec, rows, cols));
    setResult(null);
    setSelection(null);
  }

  const viewport = useMemo(() => {
    if (!instance) return makeViewport(8, 8);
    let pad = 44;
    if (spec?.layers.some((layer) => layer.target === "outside")) {
      let maxTokens = 1;
      for (const side of ["top", "bottom", "left", "right"]) {
        const arr = instance.params[side];
        if (!Array.isArray(arr)) continue;
        for (const entry of arr) {
          if (Array.isArray(entry)) maxTokens = Math.max(maxTokens, entry.length);
        }
      }
      pad = Math.max(44, 20 + maxTokens * 16);
    }
    return makeViewport(instance.rows, instance.cols, 40, pad);
  }, [instance, spec]);

  const groups = useMemo(() => {
    const byCategory = new Map<string, PuzzleSpec[]>();
    for (const p of puzzles) {
      const key = p.category || "其他";
      byCategory.set(key, [...(byCategory.get(key) ?? []), p]);
    }
    return [...byCategory.entries()];
  }, [puzzles]);

  const selectedBackend = backends.find((item) => item.name === backend);
  const catalogued = spec ? puzzles.some((item) => item.key === spec.key) : false;
  const canSolve = solverAvailable && (selectedBackend?.available ?? false) && catalogued;

  return (
    <div className="app">
      <header className="topbar">
        <h1>Logic Puzzle Studio</h1>
        <select value={catalogued ? spec!.key : ""} onChange={(e) => choose(e.target.value)}>
          <option value="" disabled>选择谜题…</option>
          {groups.map(([category, items]) => (
            <optgroup key={category} label={category}>
              {items.map((p) => (
                <option key={p.key} value={p.key}>
                  {p.zh || p.en} · {p.key}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {instance && (
          <span className="size-box">
            <input type="number" min={1} max={40} value={instance.rows}
              onChange={(e) => resize(+e.target.value, instance.cols)} />
            ×
            <input type="number" min={1} max={40} value={instance.cols}
              onChange={(e) => resize(instance.rows, +e.target.value)} />
          </span>
        )}
        {backends.length > 0 && (
          <select
            value={backend}
            onChange={(e) => {
              setBackend(e.target.value);
              setResult(null);
            }}
            title={selectedBackend?.reason || "选择 cspuz 求解后端"}
          >
            {backends.map((item) => (
              <option key={item.name} value={item.name} disabled={!item.available}>
                {item.label}{item.available ? "" : "（不可用）"}
              </option>
            ))}
          </select>
        )}
        {sample && (
          <button className="ghost" onClick={() => { setInstance(sample); setResult(null); }}>
            样例
          </button>
        )}
        <form
          className="url-import"
          onSubmit={(e) => {
            e.preventDefault();
            const field = e.currentTarget.querySelector("input");
            const typed = field instanceof HTMLInputElement ? field.value : importUrl;
            void importFromUrl(typed);
          }}
        >
          <input
            type="text"
            inputMode="url"
            autoComplete="off"
            spellCheck={false}
            placeholder="粘贴 Penpa+ 或 puzz.link 链接…"
            value={importUrl}
            onChange={(e) => setImportUrl(e.target.value)}
            title="Penpa+ 按图层解码；puzz.link 按题型解码"
          />
          <button type="submit" className="ghost" disabled={importBusy || !importUrl.trim()}>
            {importBusy ? "导入中…" : "导入"}
          </button>
        </form>
        {spec && (
          <button className="ghost" onClick={() => instance && resize(instance.rows, instance.cols)}>
            清空盘面
          </button>
        )}
        <button className="solve" onClick={solve} disabled={!instance || busy || !canSolve}>
          {busy ? "求解中…" : "求解"}
        </button>
        {importNote && <span className="import-note">{importNote}</span>}
        {dslSource !== originalSource && spec && (
          <span className="dsl-dirty">使用编辑器中的 DSL</span>
        )}
        {result && (
          <span className={`status status-${result.status}`}>
            {result.status === "sat" ? "✓ 有解" : result.status === "unsat" ? "✗ 无解" : result.status}
            {result.constraints ? ` · ${result.constraints} 约束` : ""}
            {result.backend ? ` · ${result.backend}` : ""}
          </span>
        )}
        {!solverAvailable && <span className="status status-error">求解后端不可用</span>}
      </header>

      {spec ? (
        <div className="workspace">
          <Palette
            spec={spec}
            visible={visible}
            setVisible={setVisible}
            activeId={activeId}
            setActiveId={(id) => { setActiveId(id); select(null); }}
            brush={brush}
            setBrush={(b) => activeLayer && setBrushes({ ...brushes, [activeLayer.id]: b })}
            onClearLayer={(layer) => {
              setInstance((prev) => (prev ? clearLayer(prev, layer) : prev));
              setResult(null);
            }}
          />
          <main className="board-area">
            {instance ? (
              <Board
                spec={spec}
                instance={instance}
                result={result}
                viewport={viewport}
                visible={visible}
                activeLayer={activeLayer}
                brush={brush}
                selection={selection}
                draft={draft}
                onEdit={edit}
                onSelect={select}
              />
            ) : (
              <div className="empty">从上方选择一个谜题开始</div>
            )}
          </main>
          <DslEditor
            source={dslSource}
            original={originalSource}
            errorLine={result?.errorLine}
            errorMessage={result?.status === "error" ? result.message : ""}
            onChange={(text) => {
              setDslSource(text);
              setResult(null);
            }}
            onSolve={solve}
          />
        </div>
      ) : (
        <main className="board-area">
          <div className="empty">从上方选择一个谜题开始</div>
        </main>
      )}

      {rule && (
        <footer className="rulebar">
          <details>
            <summary>
              {rule.zh} / {rule.en} · {rule.category}
              {activeLayer && editorOf(activeLayer) && (
                <span className="layer-hint"> — 当前图层: {activeLayer.label}</span>
              )}
            </summary>
            <p>{rule.rule}</p>
            {spec?.notes && <p className="notes">{spec.notes}</p>}
            {result?.message && result.status !== "sat" && <p className="notes">{result.message}</p>}
          </details>
        </footer>
      )}
    </div>
  );
}
