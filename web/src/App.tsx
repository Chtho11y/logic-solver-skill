/**
 * Application shell: VS Code-style occupancy layers, Penpa+ board, DSL pane.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { bindDrawing, instanceToDrawing } from "./bind";
import { EDITOR_OF } from "./editors";
import {
  drawingFromGenericLayers,
  drawingToGenericLayers,
  emptyDrawing,
  indexedTools,
  isEmptyDrawing,
  resizeDrawing,
  TOOL_BY_ID,
  type DrawTool,
  type Drawing,
} from "./drawing";
import { DslEditor } from "./DslEditor";
import { Layers } from "./Layers";
import { PenpaPane, type PenpaHandle, type PenpaOccupancy } from "./PenpaPane";
import type { LayerCounts } from "./layers";
import type {
  ImportResult,
  Instance,
  PuzzleSpec,
  RuleEntry,
  SolveResult,
  SolverBackend,
} from "./types";

const MODE_TOOL: Record<string, DrawTool> = {
  surface: "shade",
  number: "number",
  symbol: "circle",
  line: "link",
  lineE: "edgeline",
  combi: "region",
  sudoku: "number",
  wall: "diagonal",
};

function looksLikePenpa(url: string): boolean {
  const lower = url.toLowerCase();
  return lower.includes("penpa") || lower.includes("swaroopg92") || lower.includes("#m=") || lower.includes("&p=");
}

export function App() {
  const [puzzles, setPuzzles] = useState<PuzzleSpec[]>([]);
  const [spec, setSpec] = useState<PuzzleSpec | null>(null);
  const [rule, setRule] = useState<RuleEntry | null>(null);
  const [sample, setSample] = useState<Instance | null>(null);
  const [drawing, setDrawing] = useState<Drawing>(() => emptyDrawing());
  const [counts, setCounts] = useState<LayerCounts>({});
  const [result, setResult] = useState<SolveResult | null>(null);
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [activeTool, setActiveTool] = useState<DrawTool>("number");
  const [busy, setBusy] = useState(false);
  const [solverAvailable, setSolverAvailable] = useState(false);
  const [backends, setBackends] = useState<SolverBackend[]>([]);
  const [backend, setBackend] = useState("auto");
  const [dslSource, setDslSource] = useState("");
  const [originalSource, setOriginalSource] = useState("");
  const [importUrl, setImportUrl] = useState("");
  const [importBusy, setImportBusy] = useState(false);
  const [importNote, setImportNote] = useState("");
  const penpaRef = useRef<PenpaHandle>(null);
  const pendingUrl = useRef<string | null>(null);
  const penpaReady = useRef(false);

  useEffect(() => {
    api.puzzles().then(setPuzzles).catch(console.error);
    api.health()
      .then((h) => {
        setSolverAvailable(h.solver.available);
        setBackends(h.solver.backends);
      })
      .catch(() => setSolverAvailable(false));
  }, []);

  function loadIntoPenpa(url: string) {
    pendingUrl.current = url;
    if (penpaReady.current) {
      pendingUrl.current = null;
      penpaRef.current?.loadUrl(url);
    }
  }

  async function pushDrawing(next: Drawing, title?: string, tags?: string[]) {
    setDrawing(next);
    const encoded = await api.encodePenpa({
      rows: next.rows,
      cols: next.cols,
      layers: drawingToGenericLayers(next),
      title,
      tags,
    });
    if (encoded.error || !encoded.url) {
      setImportNote(encoded.error || "无法编码盘面");
      return;
    }
    loadIntoPenpa(encoded.url);
  }

  const onOccupancy = useCallback((occ: PenpaOccupancy) => {
    penpaReady.current = true;
    if (pendingUrl.current) {
      const url = pendingUrl.current;
      pendingUrl.current = null;
      penpaRef.current?.loadUrl(url);
    }
    setCounts(occ.counts);
    setDrawing((prev) => (
      prev.rows === occ.rows && prev.cols === occ.cols ? prev : { ...prev, rows: occ.rows, cols: occ.cols }
    ));
    const tool = MODE_TOOL[occ.mode];
    if (tool) {
      setActiveTool((prev) => {
        if (occ.mode === "symbol" && ["circle", "square", "triangle", "star", "cross", "tree", "tent", "ship", "wave", "bulb", "arrow"].includes(prev)) {
          return prev;
        }
        return tool;
      });
    }
  }, []);

  useEffect(() => {
    const hiddenKeys = Object.entries(visible)
      .filter(([, on]) => on === false)
      .map(([key]) => key);
    if (!penpaReady.current) return;
    const shown = Object.entries(visible)
      .filter(([, on]) => on !== false)
      .map(([key]) => key);
    if (hiddenKeys.length) penpaRef.current?.setHidden(hiddenKeys, true);
    if (shown.length) penpaRef.current?.setHidden(shown, false);
  }, [visible]);

  async function loadPuzzleMeta(key: string) {
    const data = await api.puzzle(key);
    setSpec(data.puzzle);
    setRule(data.rule);
    setSample(data.sample);
    setResult(null);
    const source = data.puzzle.source ?? "";
    setDslSource(source);
    setOriginalSource(source);
    setActiveTool(indexedTools(data.puzzle)[0] ?? "number");
    return data;
  }

  async function choose(key: string) {
    if (!key) return;
    const data = await loadPuzzleMeta(key);
    if (!isEmptyDrawing(drawing)) return;
    const next = data.sample
      ? instanceToDrawing(data.sample, data.puzzle)
      : emptyDrawing(data.puzzle.defaultRows, data.puzzle.defaultCols);
    await pushDrawing(next, data.puzzle.key, [data.puzzle.key]);
  }

  async function applyImport(data: ImportResult, sourceUrl?: string) {
    const layerIds = data.layers.map((layer) => layer.id).join(", ");
    if (data.rows > 0 && data.cols > 0) {
      const next = drawingFromGenericLayers(data.layers, data.rows, data.cols);
      setDrawing(next);
      setResult(null);
      const tagged = data.puzzle;
      if (tagged && (!spec || spec.key !== tagged)) {
        await loadPuzzleMeta(tagged);
      }
      if (sourceUrl && looksLikePenpa(sourceUrl)) {
        loadIntoPenpa(sourceUrl);
      } else {
        await pushDrawing(next, tagged ?? "", tagged ? [tagged] : data.tags);
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
      await applyImport(data, url);
    } catch (error) {
      setImportNote(String(error));
    } finally {
      setImportBusy(false);
    }
  }

  async function solve() {
    if (!spec) return;
    setBusy(true);
    try {
      const url = penpaRef.current?.exportUrl() ?? "";
      if (!url) {
        setResult({ status: "error", message: "Penpa+ 尚未就绪", constraints: 0, debug: [] });
        return;
      }
      const data = await api.importUrl(url, spec.key);
      if (data.error) {
        setResult({ status: "error", message: data.error, constraints: 0, debug: [] });
        return;
      }
      const next = drawingFromGenericLayers(data.layers, data.rows || drawing.rows, data.cols || drawing.cols);
      setDrawing(next);
      const instance =
        data.instance && data.puzzle === spec.key ? data.instance : bindDrawing(next, spec);
      const backendInfo = backends.find((item) => item.name === backend);
      const solved = await api.solve(instance, {
        backend,
        timeoutMs: backendInfo?.supportsTimeout === false ? null : 60000,
        source: dslSource.trim() ? dslSource : undefined,
      });
      setResult(solved);
      if (solved.status === "sat" && solved.values) {
        for (const layer of spec.layers.filter((item) => item.role === "output")) {
          const values = layer.var ? solved.values[layer.var] : undefined;
          if (values && Object.keys(values).length) {
            penpaRef.current?.applySolution(layer.element, values);
          }
        }
      } else {
        penpaRef.current?.clearSolution();
      }
    } catch (error) {
      setResult({ status: "error", message: String(error), constraints: 0, debug: [] });
    } finally {
      setBusy(false);
    }
  }

  function resize(rows: number, cols: number) {
    if (rows < 1 || cols < 1 || rows > 40 || cols > 40) return;
    const next = resizeDrawing(drawing, rows, cols);
    void pushDrawing(next, spec?.key, spec ? [spec.key] : undefined);
    setResult(null);
  }

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
              const next = instanceToDrawing(sample, spec);
              void pushDrawing(next, spec.key, [spec.key]);
              setResult(null);
              penpaRef.current?.clearSolution();
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
            title="写入 Penpa+ 画布；题型只负责绑定求解"
          />
          <button type="submit" className="ghost" disabled={importBusy || !importUrl.trim()}>
            {importBusy ? "导入中…" : "导入"}
          </button>
        </form>
        <button
          className="ghost"
          onClick={() => {
            void pushDrawing(emptyDrawing(drawing.rows, drawing.cols), spec?.key, spec ? [spec.key] : undefined);
            setResult(null);
            penpaRef.current?.clearSolution();
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
        <Layers
          spec={spec}
          drawing={drawing}
          result={result}
          visible={visible}
          setVisible={setVisible}
          activeTool={activeTool}
          counts={counts}
          onSelect={(layer) => {
            const next = { ...visible };
            for (const key of layer.hideKeys) next[key] = true;
            setVisible(next);
            setActiveTool(layer.tool);
            penpaRef.current?.setTool(layer.tool);
          }}
        />
        <PenpaPane ref={penpaRef} onOccupancy={onOccupancy} />
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
          {rule ? <p>{rule.rule}</p> : <p>中间是原版 Penpa+ 编辑器。左侧只列出盘面上已有元素的变量图层。选择题型后右侧载入 DSL，求解时从画布导出并绑定。</p>}
          {spec?.notes && <p className="notes">{spec.notes}</p>}
          {result?.message && result.status !== "sat" && <p className="notes">{result.message}</p>}
        </details>
      </footer>
    </div>
  );
}
