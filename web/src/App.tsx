/** Real Penpa+ owns the board; React owns rule metadata and solve requests. */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { bindDrawing, drawingParams, instanceToDrawing } from "./bind";
import { drawingFromGenericLayers, emptyDrawing, indexedTools, TOOL_BY_ID, SIDES, type DrawTool, type Drawing } from "./drawing";
import { DslEditor } from "./DslEditor";
import { Layers } from "./LayerPanel";
import { PenpaPane, type PenpaHandle, type PenpaOccupancy } from "./PenpaPane";
import type { LayerCounts } from "./layers";
import type { Instance, PuzzleSpec, RuleEntry, SolveResult, SolverBackend } from "./types";

const MODE_TOOL: Record<string, DrawTool> = {
  surface: "shade", number: "number", symbol: "circle", line: "link",
  lineE: "edgeline", combi: "region", sudoku: "number", wall: "diagonal",
};

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
  const [loadingPuzzle, setLoadingPuzzle] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [ready, setReady] = useState(false);
  const penpaRef = useRef<PenpaHandle>(null);
  const pendingStamp = useRef<Drawing | null>(null);
  const penpaRevision = useRef<number | null>(null);
  const revision = useRef(0);
  const loadRequest = useRef(0);
  const solveInFlight = useRef(false);

  const invalidateResult = useCallback(() => {
    revision.current += 1;
    setResult(null);
    penpaRef.current?.clearSolution();
  }, []);

  useEffect(() => () => { revision.current += 1; loadRequest.current += 1; }, []);
  useEffect(() => {
    api.puzzles().then(setPuzzles).catch((error) => setLoadError(`题型载入失败：${error}`));
    api.health().then((h) => {
      setSolverAvailable(h.solver.available);
      setBackends(h.solver.backends);
    }).catch(() => setSolverAvailable(false));
  }, []);

  function pushDrawing(next: Drawing) {
    invalidateResult();
    setDrawing(next);
    setVisible({});
    pendingStamp.current = next;
    if (penpaRef.current?.stamp(next)) {
      pendingStamp.current = null;
      penpaRevision.current = penpaRef.current.getRevision();
    }
  }

  const onOccupancy = useCallback((occ: PenpaOccupancy) => {
    if (occ.revision < 0) return;
    setReady(true);
    if (pendingStamp.current && penpaRef.current?.stamp(pendingStamp.current)) {
      pendingStamp.current = null;
      penpaRevision.current = penpaRef.current.getRevision();
      return; // stamp posts a fresh occupancy; this event describes the old board.
    }
    const current = penpaRef.current?.getRevision() ?? occ.revision;
    if (penpaRevision.current !== null && current !== penpaRevision.current) invalidateResult();
    penpaRevision.current = current;
    setCounts(occ.counts);
    setDrawing((prev) => prev.rows === occ.rows && prev.cols === occ.cols ? prev : { ...prev, rows: occ.rows, cols: occ.cols });
    const tool = MODE_TOOL[occ.mode];
    if (tool) setActiveTool(tool);
  }, [invalidateResult]);

  useEffect(() => {
    const hidden = Object.entries(visible).filter(([, on]) => on === false).map(([key]) => key);
    const shown = Object.entries(visible).filter(([, on]) => on !== false).map(([key]) => key);
    if (shown.length) penpaRef.current?.setHidden(shown, false);
    if (hidden.length) penpaRef.current?.setHidden(hidden, true);
  }, [visible, ready]);

  function applyPuzzleMeta(data: Awaited<ReturnType<typeof api.puzzle>>) {
    invalidateResult();
    setSpec(data.puzzle);
    setRule(data.rule);
    setSample(data.sample);
    const source = data.puzzle.source ?? "";
    setDslSource(source);
    setOriginalSource(source);
    setActiveTool(indexedTools(data.puzzle)[0] ?? "number");
  }

  async function choose(key: string) {
    if (!key) return;
    const request = ++loadRequest.current;
    invalidateResult();
    setLoadingPuzzle(true);
    setLoadError("");
    try {
      const data = await api.puzzle(key);
      if (request !== loadRequest.current) return;
      applyPuzzleMeta(data);
      // The iframe is authoritative: React's last decoded drawing may be stale.
      if (penpaRef.current?.isEmpty() ?? !ready) {
        pushDrawing(data.sample ? instanceToDrawing(data.sample, data.puzzle) : emptyDrawing(data.puzzle.defaultRows, data.puzzle.defaultCols));
      }
    } catch (error) {
      if (request === loadRequest.current) setLoadError(`题型载入失败：${error}`);
    } finally {
      if (request === loadRequest.current) setLoadingPuzzle(false);
    }
  }

  async function importFromUrl() {
    if (importBusy || loadingPuzzle) return;
    const url = importUrl.trim();
    if (!url) return;
    const request = ++loadRequest.current;
    invalidateResult();
    setImportBusy(true);
    setImportNote("");
    try {
      const data = await api.importUrl(url, spec?.key);
      if (request !== loadRequest.current) return;
      if (data.error) throw new Error(data.error);
      if (data.rows <= 0 || data.cols <= 0) throw new Error("无法解码该链接");
      const meta = data.puzzle && data.puzzle !== spec?.key ? await api.puzzle(data.puzzle) : null;
      if (request !== loadRequest.current) return;
      if (meta) applyPuzzleMeta(meta);
      const next = drawingFromGenericLayers(data.layers, data.rows, data.cols);
      next.puzzle = data.instance?.puzzle ?? data.puzzle ?? undefined;
      next.params = structuredClone(data.instance?.params ?? {});
      next.title = data.title;
      pushDrawing(next);
      setImportNote(`${data.kind === "penpa" ? "Penpa+" : "puzz.link"} · ${data.rows}×${data.cols} 已导入${data.warnings.length ? ` · ${data.warnings.join("；")}` : ""}`);
    } catch (error) {
      if (request === loadRequest.current) setImportNote(String(error));
    } finally {
      setImportBusy(false);
    }
  }

  async function solve() {
    if (!spec || !canSolve || solveInFlight.current || loadingPuzzle || importBusy || !ready) return;
    invalidateResult();
    const requestRevision = revision.current;
    const boardRevision = penpaRef.current?.getRevision();
    penpaRevision.current = boardRevision ?? null;
    const current = () => revision.current === requestRevision && penpaRef.current?.getRevision() === boardRevision;
    solveInFlight.current = true;
    setBusy(true);
    try {
      const url = penpaRef.current?.exportUrl();
      if (!url) throw new Error("Penpa+ 尚未就绪");
      const data = await api.importUrl(url, spec.key);
      if (!current()) return;
      if (data.error) throw new Error(data.error);
      const next = drawingFromGenericLayers(data.layers, data.rows, data.cols);
      next.puzzle = drawing.puzzle;
      next.params = drawing.params;
      next.title = drawing.title;
      setDrawing(next);
      const instance = data.instance && data.puzzle === spec.key ? data.instance : bindDrawing(next, spec);
      // Keep decoded outside clues; retain host-only rule parameters such as k.
      const params = drawingParams(next, spec);
      for (const side of SIDES) delete params[side];
      instance.params = { ...instance.params, ...params };
      const solved = await api.solve(instance, {
        backend, timeoutMs: selectedBackend?.supportsTimeout === false ? null : 60000, source: dslSource,
      });
      if (!current()) return;
      setResult(solved);
      if (solved.status === "sat" && solved.values) {
        for (const layer of spec.layers.filter((item) => item.role === "output")) {
          const values = layer.var ? solved.values[layer.var] : undefined;
          if (values) penpaRef.current?.applySolution(layer.element, values);
        }
        for (const [key, on] of Object.entries(visible)) if (!on) penpaRef.current?.setHidden([key], true);
      }
    } catch (error) {
      if (current()) setResult({ status: "error", message: String(error), constraints: 0, debug: [] });
    } finally {
      solveInFlight.current = false;
      setBusy(false);
    }
  }

  function resize(rows: number, cols: number) {
    if (!Number.isInteger(rows) || !Number.isInteger(cols) || rows < 1 || cols < 1 || rows > 40 || cols > 40) return;
    if (penpaRef.current?.resize(rows, cols)) {
      invalidateResult();
      setVisible({});
      setDrawing((prev) => ({ ...prev, rows, cols }));
      penpaRevision.current = penpaRef.current.getRevision();
    }
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
  const parameters = useMemo(() => spec ? Object.entries(drawingParams(drawing, spec))
    .filter(([name, value]) => !["rows", "cols"].includes(name) && typeof value === "number") : [], [spec, drawing]);

  return (
    <div className="app">
      <div className="workspace">
        <Layers spec={spec} drawing={drawing} result={result} visible={visible} setVisible={setVisible}
          activeTool={activeTool} counts={counts} onSelect={(layer) => {
            const next = { ...visible };
            for (const key of layer.hideKeys) next[key] = true;
            setVisible(next);
            setActiveTool(layer.tool);
            penpaRef.current?.setTool(layer.tool);
          }} />
        <main className="penpa-ui" aria-label="Penpa 棋盘工作区">
          <section className="board-controls" aria-label="棋盘操作">
            <div className="board-actions">
              <select aria-label="题型" disabled={loadingPuzzle || importBusy} value={catalogued ? spec!.key : ""} onChange={(e) => choose(e.target.value)}>
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
                <input disabled={!ready} aria-label="行数" type="number" min={1} max={40} value={drawing.rows}
                  onChange={(e) => resize(+e.target.value, drawing.cols)} />
                ×
                <input disabled={!ready} aria-label="列数" type="number" min={1} max={40} value={drawing.cols}
                  onChange={(e) => resize(drawing.rows, +e.target.value)} />
              </span>
              {spec && parameters
                .map(([name, value]) => (
                  <label className="parameter" key={name}>
                    {name === "k" ? "数字/字母种数" : name === "stars" ? "星数" : name}
                    <input aria-label={`参数 ${name}`} type="number" step={1} value={Number(value)}
                      onChange={(e) => {
                        if (!e.target.value.trim() || !Number.isSafeInteger(Number(e.target.value))) return;
                        const next = Number(e.target.value);
                        setDrawing((prev) => ({
                          ...prev, puzzle: spec.key,
                          params: { ...(prev.puzzle === spec.key ? prev.params : {}), [name]: next }
                        }));
                        invalidateResult();
                      }} />
                  </label>
                ))}
              {backends.length > 0 && (
                <select
                  aria-label="求解后端"
                  value={backend}
                  onChange={(e) => {
                    setBackend(e.target.value);
                    invalidateResult();
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
                  disabled={loadingPuzzle || importBusy}
                  onClick={() => {
                    pushDrawing(instanceToDrawing(sample, spec));
                  }}
                >
                  样例
                </button>
              )}
            </div>
            <form
              className="url-import"
              onSubmit={(e) => {
                e.preventDefault();
                void importFromUrl();
              }}
            >
              <input
                aria-label="导入链接"
                type="text"
                inputMode="url"
                autoComplete="off"
                spellCheck={false}
                placeholder="粘贴 Penpa+ 或 puzz.link 链接…"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                title="写入通用画布；题型只负责绑定求解"
              />
              <button type="submit" className="ghost" disabled={loadingPuzzle || importBusy || !importUrl.trim()}>
                {importBusy ? "导入中…" : "导入"}
              </button>
            </form>
            <div className="board-actions">
              <button
                className="ghost"
                onClick={() => {
                  pushDrawing({ ...emptyDrawing(drawing.rows, drawing.cols), puzzle: drawing.puzzle, params: drawing.params });
                }}
              >
                清空盘面
              </button>
              <button className="solve" onClick={solve} disabled={busy || !canSolve || loadingPuzzle || importBusy || !ready} title={spec ? undefined : "选择题型以绑定并求解"}>
                {busy ? "求解中…" : "求解"}
              </button>
            </div>
            <div className="board-status" role="status" aria-live="polite">
              {!ready && <span>载入 Penpa+ 编辑器中…</span>}
              {loadingPuzzle && <span>载入题型中…</span>}
              {loadError && <span className="status-error">{loadError}</span>}
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
              {result?.message && result.status !== "sat" && <span className="result-message">{result.message}</span>}
            </div>
          </section>
          <PenpaPane ref={penpaRef} onOccupancy={onOccupancy} />
          <footer className="rulebar">
            <details>
              <summary>{rule ? `${rule.zh} / ${rule.en} · ${rule.category}` : "通用绘制"}
                <span className="layer-hint"> — {TOOL_BY_ID[activeTool].label}</span>
              </summary>
              <p>{rule?.rule ?? "中间是原版 Penpa+ 编辑器；左侧列出已使用图层，右侧编辑求解规则。"}</p>
              {spec?.notes && <p className="notes">{spec.notes}</p>}
            </details>
          </footer>
        </main>
        <DslEditor source={dslSource} original={originalSource} errorLine={result?.errorLine}
          errorMessage={result?.status === "error" ? result.message : ""}
          onChange={(text) => { setDslSource(text); invalidateResult(); }} onSolve={solve} />
      </div>
    </div>
  );
}
