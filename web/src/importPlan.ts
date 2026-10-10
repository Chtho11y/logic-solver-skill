/** Plan an import without mutating the live workspace. Each drawing keeps one binding. */
import { drawingFromGenericLayers, type Drawing, type DrawTool, DRAW_TOOLS } from './drawing';
import { instanceToDrawing } from './bind';
import type { GenericLayer, ImportResult, LayerSpec, PuzzleSpec, VarSpec } from './types';

export type ImportPlan = {
  spec: PuzzleSpec;
  documents: { id: string; drawing: Drawing }[];
  bindings: string[];
  created: string[];
  review: string[];
};

const reserved = new Set('let for in if elif else def return import use and or not xor true false rows cols regions UP DOWN LEFT RIGHT UP_LEFT UP_RIGHT DOWN_LEFT DOWN_RIGHT'.split(' '));
const special = (layer: GenericLayer) => ['cage_regions', 'cage_totals', 'corner_numbers'].includes(layer.id) || ['cage-region', 'cage-total'].includes(String(layer.options?.semantic)) || layer.options?.placement === 'corner';
const specialInput = (layer: LayerSpec) => ['cage_regions', 'cage_totals', 'corner_numbers'].includes(String(layer.options?.importLayer)) || ['cage-region', 'cage-total'].includes(String(layer.options?.semantic)) || layer.options?.placement === 'corner';
const bindingIdentity = (layer: GenericLayer) => layer.id === 'corner_numbers' || layer.options?.semantic === 'cage-total' ? 'cage_totals' : layer.options?.semantic === 'cage-region' ? 'cage_regions' : layer.id;
const inputMatches = (input: LayerSpec, layer: GenericLayer) => input.role === 'input' && input.element === layer.element && input.target === layer.target;

export function planImport(spec: PuzzleSpec, imported: ImportResult, selected: string, source = ''): ImportPlan {
  if (!Number.isInteger(imported.rows) || !Number.isInteger(imported.cols) || imported.rows < 1 || imported.cols < 1 || imported.rows > 40 || imported.cols > 40)
    throw new Error('导入尺寸须为 1 至 40 行、列；当前工作区未改变。');
  const next: PuzzleSpec = { ...spec, variables: [...spec.variables], layers: [...spec.layers] };
  const documents = new Map<string, Drawing>();
  const bindings: string[] = [], created: string[] = [], review: string[] = [];
  const used = new Set([...reserved, ...spec.variables.map(v => v.name), ...(source.match(/[A-Za-z_]\w*/g) ?? [])]);
  const bound = imported.puzzle === spec.key ? imported.instance : null;
  const nonempty = imported.layers.filter(layer => Object.keys(layer.values).length).flatMap(layer => {
    if (layer.element !== 'number' || special(layer)) return [layer];
    const numbers: Record<string, number> = {}, texts: Record<string, string> = {}, lists: Record<string, string> = {};
    for (const [point, value] of Object.entries(layer.values)) {
      const text = Array.isArray(value) ? value.map(n => n === -1 ? '?' : String(n)).join(' ') : String(value).trim();
      if (!Array.isArray(value) && /^-?\d+$/.test(text) && Number.isSafeInteger(Number(text))) numbers[point] = Number(text);
      else if (/^[A-Za-z]$/.test(text)) texts[point] = text.toUpperCase();
      else {
        const tokens = text.split(/[\s,]+/);
        if (tokens.length > 0 && tokens.length <= 4 && tokens.every(t => /^(\?|[0-8])$/.test(t)) && (!tokens.includes('0') || tokens.length === 1)) lists[point] = tokens.join(' ');
        else throw new Error(`数字线索 ${JSON.stringify(value)} 无法安全绑定；仅支持整数、单个 A–Z 字母或有效的段长列表。当前工作区未改变。`);
      }
    }
    const layers: GenericLayer[] = [];
    if (Object.keys(numbers).length) layers.push({ ...layer, values: numbers });
    if (Object.keys(texts).length) layers.push({ ...layer, id: 'text', element: 'text', values: texts });
    if (Object.keys(lists).length) layers.push({ ...layer, id: Object.keys(numbers).length ? 'number_lists' : layer.id, values: lists, options: { ...layer.options, mode: 'list' } });
    return layers;
  });
  const hasRegions = nonempty.some(layer => layer.id === 'regions');
  function addDocument(id: string, layer: GenericLayer, drawing?: Drawing) {
    const value = drawing ?? drawingFromGenericLayers([layer], imported.rows, imported.cols);
    const previous = documents.get(id);
    if (previous) {
      for (const [tool, marks] of Object.entries(value.marks)) previous.marks[tool as DrawTool] = { ...previous.marks[tool as DrawTool], ...marks };
      previous.cages = { ...previous.cages, ...value.cages };
      previous.cornerNumbers = { ...previous.cornerNumbers, ...value.cornerNumbers };
      previous.regions = { ...previous.regions, ...value.regions };
      previous.outside = { ...previous.outside, ...value.outside };
    } else documents.set(id, value);
    bindings.push(`${layer.id} → ${id === '__regions' ? '区域边界' : id === '__outside' ? '盘外线索' : id}`);
  }
  for (const layer of nonempty) {
    if (!DRAW_TOOLS.includes(layer.element as DrawTool)) throw new Error(`暂不支持导入 ${layer.element}；当前工作区未改变。`);
    if (layer.target === 'outside' || layer.element === 'outside') {
      const listMode = Object.values(layer.values).some(side => Array.isArray(side) && side.some(Array.isArray));
      const existing = next.layers.filter(l => l.target === 'outside' && l.role === 'input');
      if (!existing.length) next.layers.push({ id: 'import_outside', label: '盘外线索', element: 'outside', target: 'outside', role: 'input', var: '', param: '', palette: {}, options: { sides: ['top', 'bottom', 'left', 'right'], ...(listMode ? { mode: 'list' } : {}) } });
      else if (listMode && existing.some(l => l.options?.mode !== 'list')) {
        review.push('导入包含盘外段长列表，将盘外线索改为列表模式；请确认 DSL 按列表读取这些参数。');
        next.layers = next.layers.map(l => l.target === 'outside' && l.role === 'input' ? { ...l, options: { ...l.options, mode: 'list' } } : l);
      }
      addDocument('__outside', layer);
      continue;
    }
    if (layer.id === 'regions') {
      next.usesRegions = true;
      if (!next.layers.some(l => l.var === '__regions')) next.layers.push({ id: 'import_regions', label: '区域边界', element: 'region', target: 'cell', role: 'input', var: '__regions', param: '', palette: {}, options: {} });
      addDocument('__regions', layer);
      continue;
    }
    // The decoder reports both a wall map and its connected-region map. If no
    // edge variable exists, keep the single fixed-region representation.
    if (layer.element === 'edgeline' && hasRegions && !spec.layers.some(l => inputMatches(l, layer) && l.var && !l.var.startsWith('__'))) continue;
    if (!['cell', 'edge', 'corner'].includes(layer.target)) throw new Error(`无法绑定导入位置 ${layer.target}；当前工作区未改变。`);
    const rawCandidates = next.layers.filter(l => inputMatches(l, layer) && !l.var.startsWith('__') &&
      (special(layer) ? l.options?.importLayer === bindingIdentity(layer) || l.options?.semantic === layer.options?.semantic && !!layer.options?.semantic : !specialInput(l) && (!l.options?.importLayer || l.options.importLayer === layer.id)));
    const accepts = (input: LayerSpec, values: Record<string, unknown>, semanticValues = false) => {
      const variable = next.variables.find(v => v.name === input.var);
      if (!variable || variable.kind !== layer.target || variable.type === 'cc') return false;
      if (variable.dense && Object.keys(values).length !== imported.rows * imported.cols) return false;
      return Object.values(values).every(value => {
        if (Array.isArray(value) || typeof value === 'string' && /[?\s,]/.test(value)) return variable.type === 'constant' && input.options?.mode === 'list';
        let n = Number(value);
        if (!semanticValues) {
          if (layer.element === 'text' && typeof value === 'string' && /^[A-Za-z]$/.test(value)) n = value.toUpperCase().charCodeAt(0) - 64;
          if (['shade', 'edgeline', 'link'].includes(layer.element)) n = n ? 1 : 0;
          if (layer.element === 'circle' && Object.hasOwn(input.palette ?? {}, '0')) n--;
        }
        return Number.isSafeInteger(n) && (variable.type === 'constant' || !variable.domain || n >= variable.domain[0] && n <= variable.domain[1]);
      });
    };
    // A recognized puzzle has authoritative variable names (e.g. two different
    // number variables). Prefer those bindings over guessing by appearance.
    const known = bound && !special(layer) ? [...new Set(rawCandidates.filter(input => Object.hasOwn(bound.clues, input.var) && accepts(input, bound.clues[input.var], true)).map(l => l.var))] : [];
    if (known.length) {
      for (const id of known) {
        const drawing = instanceToDrawing(bound!, { ...next, layers: next.layers.filter(l => l.var === id && inputMatches(l, layer)) });
        drawing.regions = {};
        addDocument(id, layer, drawing);
      }
      continue;
    }
    const candidates = rawCandidates.filter(input => accepts(input, layer.values));
    const names = [...new Set(candidates.map(l => l.var))];
    let id = names.includes(selected) ? selected : names.length === 1 ? names[0] : '';
    if (!id && names.length > 1) review.push(`${layer.id} 同时匹配 ${names.join('、')}，将新建独立线索变量。`);
    if (!id && rawCandidates.some(input => input.var === selected) && !names.includes(selected)) review.push(`${layer.id} 与当前变量 ${selected} 的类型或值域不兼容，将新建独立线索变量。`);
    if (!id) {
      const base = (special(layer) ? bindingIdentity(layer) : `${layer.element}_clues`).replace(/[^A-Za-z_0-9]/g, '_');
      id = base; let suffix = 2;
      while (used.has(id)) id = `${base}_${suffix++}`;
      used.add(id);
      const values = Object.values(layer.values).flatMap(v => typeof v === 'number' ? [['shade', 'edgeline', 'link'].includes(layer.element) ? v ? 1 : 0 : v] : layer.element === 'text' && typeof v === 'string' ? [v.charCodeAt(0) - 64] : []);
      const variable: VarSpec = { name: id, kind: layer.target as VarSpec['kind'], type: 'constant', domain: values.length ? [Math.min(...values), Math.max(...values)] : null, doc: `链接导入的 ${layer.id} 题目线索`, dense: false };
      const listNumbers = layer.element === 'number' && Object.values(layer.values).some(v => typeof v === 'string' && /^[\d?\s,]+$/.test(v) && /[?\s,]/.test(v));
      next.variables.push(variable);
      next.layers.push({ id: `${id}_input`, label: id, element: layer.element as LayerSpec['element'], target: layer.target as LayerSpec['target'], role: 'input', var: id, param: '', palette: {}, options: { ...layer.options, importLayer: bindingIdentity(layer), ...(listNumbers ? { mode: 'list' } : {}) } });
      created.push(id);
    }
    addDocument(id, layer);
  }
  if (!documents.size) throw new Error('链接中没有可导入的题目标记；当前工作区未改变。');
  return { spec: next, documents: [...documents].map(([id, drawing]) => ({ id, drawing })), bindings, created, review };
}
