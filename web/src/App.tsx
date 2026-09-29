/** Penpa owns editing; the workspace supplies editable variables and rules. */
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { drawingParams, instanceToDrawing } from "./bind";
import { emptyDrawing, drawingFromGenericLayers, TOOL_BY_ID, type DrawTool, type Drawing } from "./drawing";
import { DslEditor } from "./DslEditor";
import { PenpaPane, type PenpaHandle, type PenpaOccupancy } from "./PenpaPane";
import type { Instance, LayerSpec, PuzzleSpec, SolveResult, SolverBackend } from "./types";

const blankSpec = (): PuzzleSpec => ({ key: "custom", en: "Custom", zh: "自定义工作区", category: "", subcategory: "", rule: "", aliases: [], defaultRows: 6, defaultCols: 6, usesRegions: false, variables: [], layers: [], params: {}, notes: "" });
const compatible = (element: string, tool: DrawTool) => element === tool || (tool === "number" && ["outside", "text"].includes(element)) || (tool === "edgeline" && element === "region");
function editableSpec(spec: PuzzleSpec): PuzzleSpec {
  const layers = [...spec.layers];
  for (const layer of spec.layers.filter(l => l.role === "output")) {
    if (!layers.some(l => l.role === "input" && l.var === layer.var && l.element === layer.element))
      layers.push({ ...layer, id: `given_${layer.id}`, role: "input" });
  }
  return { ...spec, layers };
}
function documentsFor(spec: PuzzleSpec, instance: Instance) {
  instance = { ...instance, clues: instance.clues ?? {}, regions: instance.regions ?? {}, params: instance.params ?? {}, title: instance.title ?? "" };
  const items = spec.variables.map(variable => {
    const drawing = instanceToDrawing(instance, { ...spec, layers: spec.layers.filter(l => l.var === variable.name) });
    drawing.regions = {};
    return { id: variable.name, drawing };
  });
  if (spec.layers.some(l => l.target === "outside")) {
    const drawing = instanceToDrawing(instance, { ...spec, layers: spec.layers.filter(l => l.target === "outside") });
    drawing.regions = {};
    items.push({ id: "__outside", drawing });
  }
  if (spec.usesRegions) items.push({ id: "__regions", drawing: { ...emptyDrawing(instance.rows, instance.cols), regions: instance.regions ?? {} } });
  return items.length ? items : [{ id: "__unbound", drawing: emptyDrawing(instance.rows, instance.cols) }];
}

export function App() {
  const [puzzles, setPuzzles] = useState<PuzzleSpec[]>([]);
  const [spec, setSpec] = useState<PuzzleSpec>(blankSpec);
  const [preset, setPreset] = useState("");
  const [sample, setSample] = useState<Instance | null>(null);
  const [drawing, setDrawing] = useState<Drawing>(() => emptyDrawing(6, 6));
  const [result, setResult] = useState<SolveResult | null>(null);
  const [activeTool, setActiveTool] = useState<DrawTool>("number");
  const [activeVariable, setActiveVariable] = useState("__unbound");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [backends, setBackends] = useState<SolverBackend[]>([]);
  const [backend, setBackend] = useState("auto");
  const [dslSource, setDslSource] = useState("");
  const [originalSource, setOriginalSource] = useState("");
  const [url, setUrl] = useState("");
  const [note, setNote] = useState("");
  const [ready, setReady] = useState(false);
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [varType, setVarType] = useState<"normal" | "constant" | "cc">("normal");
  const [minimum, setMinimum] = useState(0);
  const [maximum, setMaximum] = useState(9);
  const penpa = useRef<PenpaHandle>(null);
  const revision = useRef(0);
  const boardRevision = useRef<number | null>(null);
  const inFlight = useRef(false);
  const initialized = useRef(false);
  const specRef = useRef(spec);
  specRef.current = spec;

  const invalidate = useCallback(() => {
    revision.current++;
    setResult(null);
    penpa.current?.clearSolution();
  }, []);
  useEffect(() => {
    api.puzzles().then(setPuzzles).catch(e => setNote(String(e)));
    api.health().then(h => setBackends(h.solver.backends)).catch(e => setNote(String(e)));
  }, []);

  const onOccupancy = useCallback((occ: PenpaOccupancy) => {
    if (occ.revision < 0) return;
    setReady(true);
    if (!initialized.current) {
      initialized.current = true;
      penpa.current?.loadDocuments([{ id: "__unbound", drawing: emptyDrawing(6, 6) }]);
      penpa.current?.setTool("number");
      return;
    }
    const current = penpa.current?.getRevision() ?? occ.revision;
    if (boardRevision.current !== null && boardRevision.current !== current) invalidate();
    boardRevision.current = current;
    setDrawing(prev => prev.rows === occ.rows && prev.cols === occ.cols ? prev : { ...prev, rows: occ.rows, cols: occ.cols });
    const selection = penpa.current?.getSelection();
    const tool = selection?.tool ?? occ.tool ?? "number";
    setActiveTool(tool);
    const candidates = specRef.current.layers.filter(l => compatible(l.element, tool));
    const ids = candidates.map(l => l.target === "outside" ? "__outside" : l.var).filter(Boolean);
    if (tool === "edgeline" && specRef.current.usesRegions) ids.push("__regions");
    const selected = selection?.activeVariable ?? occ.activeVariable ?? "__unbound";
    if (ids.length && !ids.includes(selected)) {
      penpa.current?.selectVariable(ids[0]);
      setActiveVariable(ids[0]);
    } else if (!ids.length && selected !== "__unbound") {
      penpa.current?.selectVariable("__unbound"); setActiveVariable("__unbound");
    } else setActiveVariable(selected);
  }, [invalidate]);

  function loadInstance(nextSpec: PuzzleSpec, instance: Instance) {
    invalidate();
    penpa.current?.loadDocuments(documentsFor(nextSpec, instance));
    setDrawing({ ...emptyDrawing(instance.rows, instance.cols), puzzle: nextSpec.key, params: structuredClone(instance.params ?? {}), title: instance.title ?? "" });
    boardRevision.current = penpa.current?.getRevision() ?? null;
  }
  async function importPreset() {
    if (!preset || loading) return;
    setLoading(true); setNote(""); invalidate();
    try {
      const data = await api.puzzle(preset);
      const next = editableSpec(data.puzzle);
      specRef.current = next;
      setSpec(next); setSample(data.sample);
      setDslSource(next.source ?? ""); setOriginalSource(next.source ?? "");
      loadInstance(next, data.sample ?? { puzzle: next.key, rows: next.defaultRows, cols: next.defaultCols, clues: {}, regions: {}, params: {}, title: "" });
      const first = next.layers.find(l => l.role === "input");
      if (first) penpa.current?.setTool(first.element === "outside" ? "number" : first.element as DrawTool);
      setNote(`已导入 ${next.zh || next.en} 预设；可以继续新增变量和修改规则。`);
    } catch (e) { setNote(String(e)); }
    finally { setLoading(false); }
  }

  async function importLink(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || loading) return;
    setLoading(true); invalidate();
    const target = penpa.current?.getSelection().activeVariable ?? activeVariable;
    try {
      const data = await api.importUrl(url.trim());
      if (data.error) throw new Error(data.error);
      if (!penpa.current?.replaceDrawing(target, drawingFromGenericLayers(data.layers, data.rows, data.cols))) throw new Error("链接导入失败");
      setNote(`已导入到 ${target === "__unbound" ? "未绑定画布" : target}${data.warnings.length ? ` · ${data.warnings.join("；")}` : ""}`);
    } catch (e) { setNote(String(e)); }
    finally { setLoading(false); }
  }

  function addVariable(e: React.FormEvent) {
    e.preventDefault();
    if (!/^[A-Za-z_][A-Za-z_0-9]*$/.test(name) || name.startsWith("__") || spec.variables.some(v => v.name === name)) { setNote("变量名须为唯一的英文标识符，不能以 __ 开头。"); return; }
    if (!Number.isSafeInteger(minimum) || !Number.isSafeInteger(maximum) || minimum > maximum) { setNote("请填写有效的整数值域。"); return; }
    const element = varType === "cc" ? "region" : (penpa.current?.getSelection().tool ?? activeTool);
    const target = ["link", "edgeline", "dot"].includes(element) ? "edge" : "cell";
    const layer: LayerSpec = { id: `${name}_input`, label: name, element, target, role: "input", var: name, param: "", palette: {}, options: {} };
    const next: PuzzleSpec = { ...spec, variables: [...spec.variables, { name, kind: target, type: varType, domain: varType === "cc" ? null : [minimum, maximum], doc: "", dense: false }], layers: [...spec.layers, layer, ...(varType === "constant" ? [] : [{ ...layer, id: `${name}_output`, role: "output" as const }])] };
    specRef.current = next; setSpec(next);
    invalidate(); penpa.current?.selectVariable(name); setActiveVariable(name);
    boardRevision.current = penpa.current?.getRevision() ?? null;
    setAdding(false); setNote(`变量 ${name} (${element}) 已添加，可在 DSL 中使用。`); setName("");
  }

  async function solve() {
    if (inFlight.current || loading || !ready) return;
    invalidate(); inFlight.current = true; setBusy(true); setNote("");
    const version = revision.current;
    const board = penpa.current?.getRevision();
    boardRevision.current = board ?? null;
    const current = () => version === revision.current && penpa.current?.getRevision() === board;
    try {
      const instance: Instance = { puzzle: spec.key, rows: drawing.rows, cols: drawing.cols, clues: {}, regions: {}, params: drawingParams(drawing, spec), title: drawing.title };
      const solved = await api.solve(instance, { spec, documents: penpa.current?.exportDocuments(), source: dslSource, backend, timeoutMs: backends.find(b => b.name === backend)?.supportsTimeout === false ? null : 60000 });
      if (!current()) return;
      setResult(solved);
      if (solved.status === "sat") for (const layer of spec.layers.filter(l => l.role === "output")) {
        const values = solved.values?.[layer.var];
        if (values) penpa.current?.applySolution(layer.element, values, layer.palette, layer.var);
      }
    } catch (e) { if (current()) setResult({ status: "error", message: String(e), constraints: 0, debug: [] }); }
    finally { inFlight.current = false; setBusy(false); }
  }

  const targets = new Map<string, string>();
  for (const layer of spec.layers) if (compatible(layer.element, activeTool)) targets.set(layer.target === "outside" ? "__outside" : layer.var, layer.target === "outside" ? "盘外线索" : layer.var);
  if (activeTool === "edgeline" && spec.usesRegions) targets.set("__regions", "区域边界");
  targets.delete("");
  const parameters = Object.entries(drawingParams(drawing, spec)).filter(([key, value]) => !["rows", "cols"].includes(key) && typeof value === "number");
  const controls = <>
    <div className="studio-actions">
      <select aria-label="预设" value={preset} onChange={e => setPreset(e.target.value)}>
        <option value="">选择预设…</option>
        {puzzles.map(p => <option key={p.key} value={p.key}>{p.zh || p.en} · {p.key}</option>)}
      </select>
      <button title="载入预设的变量、规则和样例，替换当前工作区" disabled={!preset || loading || !ready} onClick={importPreset}>导入预设</button>
      <button disabled={!ready || loading} onClick={() => loadInstance(spec, { puzzle: spec.key, rows: drawing.rows, cols: drawing.cols, params: drawing.params, clues: {}, regions: {}, title: "" })}>清空盘面</button>
      <button className="solve" disabled={!ready || busy || loading || !backends.some(b => b.name === backend && b.available)} onClick={solve}>{busy ? "求解中…" : "求解"}</button>
      {sample && <button disabled={loading} onClick={() => loadInstance(spec, sample)}>载入样例</button>}
      <details><summary>导入链接</summary><form className="studio-settings" onSubmit={importLink} onKeyDown={e => e.stopPropagation()}><input aria-label="导入链接" placeholder="Penpa+ / puzz.link" value={url} onChange={e => setUrl(e.target.value)} /><button disabled={loading || !url.trim()}>导入到当前变量</button></form></details>
      <details><summary>尺寸与参数</summary><div className="studio-settings">
        <label>行 <input aria-label="行数" type="number" min={1} max={40} value={drawing.rows} onChange={e => { if (penpa.current?.resize(+e.target.value, drawing.cols)) invalidate(); }} /></label>
        <label>列 <input aria-label="列数" type="number" min={1} max={40} value={drawing.cols} onChange={e => { if (penpa.current?.resize(drawing.rows, +e.target.value)) invalidate(); }} /></label>
        {parameters.map(([key, value]) => <label key={key}>{key} <input aria-label={`参数 ${key}`} type="number" value={Number(value)} onChange={e => { if (e.target.value && Number.isSafeInteger(+e.target.value)) { setDrawing(prev => ({ ...prev, puzzle: spec.key, params: { ...prev.params, [key]: +e.target.value } })); invalidate(); } }} /></label>)}
        <select aria-label="求解后端" value={backend} onChange={e => { setBackend(e.target.value); invalidate(); }}>{backends.map(b => <option key={b.name} value={b.name} disabled={!b.available}>{b.label}</option>)}</select>
      </div></details>
    </div>
    <div className="studio-status" role="status" aria-live="polite">
      {note}
      {result && <span className={`status-${result.status}`}>{result.status === "sat" ? "✓ 有解" : result.status === "unsat" ? "✗ 无解" : result.message || result.status}{result.constraints ? ` · ${result.constraints} 约束` : ""}</span>}
    </div>
  </>;
  const variableControls = <>
    <div className="studio-variable-row" aria-label="绘制变量">
      <strong className="studio-variable-label">绘制到：</strong>
      {[...targets].map(([id, label]) => <button key={id} aria-pressed={activeVariable === id} onClick={() => { penpa.current?.selectVariable(id); setActiveVariable(id); }}>{label}</button>)}
      <button onClick={() => { const tool = penpa.current?.getSelection().tool ?? activeTool; setActiveTool(tool); setAdding(!adding); setVarType("normal"); setMinimum(0); setMaximum(tool === "number" ? 9 : 1); }}>＋ 新增变量</button>
      <span className="studio-hint">{TOOL_BY_ID[activeTool]?.label ?? activeTool}</span>
    </div>
    {adding && <form className="studio-variable-form" onSubmit={addVariable} onKeyDown={e => e.stopPropagation()}>
      <input aria-label="变量名" placeholder="变量名，如 x" value={name} onChange={e => setName(e.target.value)} required />
      <select aria-label="变量类型" value={varType} onChange={e => setVarType(e.target.value as typeof varType)}><option value="normal">待求解变量</option><option value="constant">题目线索</option>{activeTool === "edgeline" && <option value="cc">区域划分</option>}</select>
      {varType !== "cc" && <><input aria-label="最小值" type="number" value={minimum} onChange={e => setMinimum(+e.target.value)} /><span>至</span><input aria-label="最大值" type="number" value={maximum} onChange={e => setMaximum(+e.target.value)} /></>}
      <button type="submit">添加变量</button><button type="button" onClick={() => setAdding(false)}>取消</button>
    </form>}
  </>;
  return <div className="app"><div className="workspace">
    <main className="penpa-ui" aria-label="Penpa 棋盘工作区"><PenpaPane ref={penpa} onOccupancy={onOccupancy} controls={controls} variableControls={variableControls} /></main>
    <DslEditor source={dslSource} original={originalSource} errorLine={result?.errorLine} errorMessage={result?.status === "error" ? result.message : ""} onChange={text => { setDslSource(text); invalidate(); }} onSolve={solve} />
  </div></div>;
}
