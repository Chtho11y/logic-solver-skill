/**
 * Application shell: Penpa-like drawing tools, board, and puzzle-indexed DSL.
 * The canvas is a generic drawing; a puzzle only badges tools and binds clues.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { bindDrawing, instanceToDrawing } from "./bind";
import { Board } from "./Board";
import { EDITOR_OF } from "./editors";
import { makeViewport } from "./geometry";
import {
  clearTool,
  drawingFromGenericLayers,
  emptyDrawing,
  indexedTools,
  isEmptyDrawing,
  outsideEntry,
  outsideText,
  regionsFromEdges,
  resizeDrawing,
  setMark,
  setOutsideEntry,
  SIDES,
  TOOL_BY_ID,
  type DrawTool,
  type Drawing,
} from "./drawing";
import { DslEditor } from "./DslEditor";
import { Palette } from "./Palette";
import type {
  Brush,
  ImportResult,
  Instance,
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
  const [drawing, setDrawing] = useState<Drawing>(() => emptyDrawing());
  const [result, setResult] = useState<SolveResult | null>(null);
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [activeTool, setActiveTool] = useState<DrawTool>("number");
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

  const brush: Brush = brushes[activeTool] ?? "cycle";

  async function loadPuzzleMeta(key: string) {
    const data = await api.puzzle(key);
    setSpec(data.puzzle);
    setRule(data.rule);
    setSample(data.sample);
    setResult(null);
    setSelection(null);
    setDraft("");
    const source = data.puzzle.source ?? "";
    setDslSource(source);
    setOriginalSource(source);
    setActiveTool(indexedTools(data.puzzle)[0] ?? "number");
    return data;
  }

  async function choose(key: string) {
    if (!key) return;
    const data = await loadPuzzleMeta(key);
    setDrawing((prev) => {
      if (!isEmptyDrawing(prev)) return prev;
      if (data.sample) return instanceToDrawing(data.sample, data.puzzle);
      return emptyDrawing(data.puzzle.defaultRows, data.puzzle.defaultCols);
    });
  }

  const edit = useCallback((tool: DrawTool, key: string, value: number | null) => {
    setDrawing((prev) => setMark(prev, tool, key, value));
    setResult(null);
  }, []);

  const commit = useCallback(
    (sel: Selection | null, text: string) => {
      if (!sel) return;
      if (sel.kind === "point") {
        const tool = sel.tool as DrawTool;
        if (tool === "text") {
          const letter = text.trim().slice(-1).toUpperCase();
          const code = letter ? letter.charCodeAt(0) - 64 : 0;
          edit(tool, sel.key, code >= 1 && code <= 26 ? code : null);
        } else {
          const parsed = parseInt(text.trim(), 10);
          edit(tool, sel.key, Number.isNaN(parsed) ? null : parsed);
        }
        return;
      }
      const tokens = text.split(/[\s,]+/).filter(Boolean).map(Number).filter((n) => !Number.isNaN(n));
      const value = tokens.length === 0 ? null : tokens.length === 1 ? tokens[0] : tokens;
      setDrawing((prev) => setOutsideEntry(prev, sel.side, sel.index, value));
      setResult(null);
    },
    [edit],
  );

  const select = useCallback(
    (next: Selection | null) => {
      commit(selection, draft);
      setSelection(next);
      if (!next) {
        setDraft("");
        return;
      }
      if (next.kind === "point") {
        const current =
          next.tool === "region"
            ? drawing.regions[next.key]
            : drawing.marks[next.tool as DrawTool]?.[next.key];
        setDraft(current === undefined ? "" : String(current));
      } else {
        setDraft(outsideText(outsideEntry(drawing, next.side, next.index)));
      }
    },
    [commit, selection, draft, drawing],
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
    if (data.rows > 0 && data.cols > 0) {
      setDrawing(drawingFromGenericLayers(data.layers, data.rows, data.cols));
      setResult(null);
      setSelection(null);
      const tagged = data.puzzle;
      if (tagged && (!spec || spec.key !== tagged)) {
        await loadPuzzleMeta(tagged);
      }
      const bits = [
        data.kind === "penpa" ? "Penpa+" : "puzz.link",
        `${data.rows}×${data.cols}`,
        data.title,
      ].filter(Boolean);
      const warn = data.warnings.length ? ` · ${data.warnings[0]}` : "";
      const bound = tagged || spec?.key;
      setImportNote(
        bound
          ? `${bits.join(" · ")} 已写入画布${layerIds ? `（${layerIds}）` : ""}${warn}`
          : `${bits.join(" · ")} 已按图层解码（${layerIds}）。选择题型即可绑定求解，无需再次导入。${warn}`,
      );
      return;
    }
    setImportNote(data.warnings.join(" ") || "无法解码该链接");
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
    if (!spec) return;
    commit(selection, draft);
    setSelection(null);
    setBusy(true);
    try {
      const instance = bindDrawing(drawing, spec);
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
    if (rows < 1 || cols < 1 || rows > 40 || cols > 40) return;
    setDrawing((prev) => resizeDrawing(prev, rows, cols));
    setResult(null);
    setSelection(null);
  }

  const viewport = useMemo(() => {
    let pad = 44;
    const wantsOutside =
      activeTool === "outside" ||
      spec?.layers.some((layer) => layer.target === "outside") ||
      Object.values(drawing.outside).some((side) => Object.keys(side).length);
    if (wantsOutside) {
      let maxTokens = 1;
      for (const side of SIDES) {
        const values = drawing.outside[side] ?? {};
        for (const entry of Object.values(values)) {
          if (Array.isArray(entry)) maxTokens = Math.max(maxTokens, entry.length);
        }
      }
      pad = Math.max(44, 20 + maxTokens * 16);
    }
    return makeViewport(drawing.rows, drawing.cols, 40, pad);
  }, [drawing, spec, activeTool]);

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
        <span className="size-box">
          <input type="number" min={1} max={40} value={drawing.rows}
            onChange={(e) => resize(+e.target.value, drawing.cols)} />
          ×
          <input type="number" min={1} max={40} value={drawing.cols}
            onChange={(e) => resize(drawing.rows, +e.target.value)} />
        </span>
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
        {sample && spec && (
          <button
            className="ghost"
            onClick={() => {
              setDrawing(instanceToDrawing(sample, spec));
              setResult(null);
            }}
          >
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
            title="写入通用画布；题型只负责绑定求解"
          />
          <button type="submit" className="ghost" disabled={importBusy || !importUrl.trim()}>
            {importBusy ? "导入中…" : "导入"}
          </button>
        </form>
        <button
          className="ghost"
          onClick={() => {
            setDrawing(emptyDrawing(drawing.rows, drawing.cols));
            setResult(null);
          }}
        >
          清空盘面
        </button>
        <button className="solve" onClick={solve} disabled={busy || !canSolve} title={spec ? undefined : "选择题型以绑定并求解"}>
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

      <div className="workspace">
        <Palette
          spec={spec}
          visible={visible}
          setVisible={setVisible}
          activeTool={activeTool}
          setActiveTool={(tool) => { setActiveTool(tool); select(null); }}
          brush={brush}
          setBrush={(b) => setBrushes({ ...brushes, [activeTool]: b })}
          surfaceColor={drawing.surfaceColor}
          setSurfaceColor={(value) => setDrawing((prev) => ({ ...prev, surfaceColor: value }))}
          onClearTool={(tool) => {
            setDrawing((prev) => clearTool(prev, tool));
            setResult(null);
          }}
          onRegionsFromEdges={() => {
            setDrawing((prev) => ({ ...prev, regions: regionsFromEdges(prev) }));
            setResult(null);
          }}
        />
        <main className="board-area">
          <Board
            spec={spec}
            drawing={drawing}
            result={result}
            viewport={viewport}
            visible={visible}
            activeTool={activeTool}
            brush={brush}
            selection={selection}
            draft={draft}
            onEdit={edit}
            onSelect={select}
          />
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

      <footer className="rulebar">
        <details>
          <summary>
            {rule ? `${rule.zh} / ${rule.en} · ${rule.category}` : "通用绘制"}
            <span className="layer-hint"> — {TOOL_BY_ID[activeTool].label}（{EDITOR_OF[activeTool] ?? "draw"}）</span>
          </summary>
          {rule ? <p>{rule.rule}</p> : <p>左侧工具始终可用。选择题型后，本题用到的元素会标「本题」，右侧载入对应 DSL；求解时只绑定输入层。</p>}
          {spec?.notes && <p className="notes">{spec.notes}</p>}
          {result?.message && result.status !== "sat" && <p className="notes">{result.message}</p>}
        </details>
      </footer>
    </div>
  );
}
