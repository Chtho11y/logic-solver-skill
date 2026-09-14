/**
 * Penpa-style tool rail. Every drawing tool is always available; a selected
 * puzzle only badges the tools it indexes and fills the right-hand DSL pane.
 */

import { cycleValuesFor, EDITOR_OF, REGION_BRUSHES, regionColor } from "./editors";
import {
  GROUPS,
  MORE_TOOLS,
  PRIMARY_TOOLS,
  SURFACE_COLORS,
  TOOL_BY_ID,
  indexedTools,
  labelsForTool,
  type DrawTool,
} from "./drawing";
import { GlyphPreview } from "./glyphs";
import type { Brush, LayerSpec, PuzzleSpec } from "./types";

export interface PaletteProps {
  spec: PuzzleSpec | null;
  visible: Record<string, boolean>;
  setVisible: (next: Record<string, boolean>) => void;
  activeTool: DrawTool;
  setActiveTool: (tool: DrawTool) => void;
  brush: Brush;
  setBrush: (brush: Brush) => void;
  surfaceColor: number;
  setSurfaceColor: (value: number) => void;
  onClearTool: (tool: DrawTool) => void;
  onRegionsFromEdges?: () => void;
}

function toolIcon(tool: DrawTool): JSX.Element {
  if (tool === "shade") {
    return <GlyphPreview element="shade" value={1} color="#cfcfcf" size={20} />;
  }
  if (tool === "outside") {
    return <GlyphPreview element="number" value={4} size={20} />;
  }
  const value = cycleValuesFor(tool)[0] ?? 1;
  return <GlyphPreview element={tool} value={tool === "number" || tool === "text" ? 1 : value} size={20} />;
}

function Chip(props: {
  tool: DrawTool;
  active: boolean;
  hidden: boolean;
  indexed: boolean;
  labels: string[];
  onToggle: () => void;
  onSelect: () => void;
}) {
  const def = TOOL_BY_ID[props.tool];
  const title = props.labels.length
    ? `${def.hint} · 本题: ${props.labels.join(" / ")}`
    : def.hint;
  return (
    <div className={`chip ${props.active ? "active" : ""} ${props.hidden ? "hidden-layer" : ""} ${props.indexed ? "indexed" : ""}`}>
      <button className="chip-eye" title={props.hidden ? "显示" : "隐藏"} onClick={props.onToggle}>
        {props.hidden ? "–" : "👁"}
      </button>
      <button className="chip-main" onClick={props.onSelect} title={title}>
        {toolIcon(props.tool)}
        <span>{def.label}</span>
        {props.indexed && <span className="chip-badge">本题</span>}
      </button>
    </div>
  );
}

export function Palette(props: PaletteProps) {
  const {
    spec,
    visible,
    setVisible,
    activeTool,
    setActiveTool,
    brush,
    setBrush,
    surfaceColor,
    setSurfaceColor,
    onClearTool,
  } = props;
  const indexed = indexedTools(spec);
  const indexedSet = new Set(indexed);
  const outputLayers: LayerSpec[] = spec?.layers.filter((layer) => layer.role === "output") ?? [];

  function renderChip(tool: DrawTool) {
    const isOn = visible[tool] !== false;
    return (
      <Chip
        key={tool}
        tool={tool}
        active={tool === activeTool}
        hidden={!isOn}
        indexed={indexed.includes(tool)}
        labels={labelsForTool(spec, tool)}
        onToggle={() => setVisible({ ...visible, [tool]: !isOn })}
        onSelect={() => setActiveTool(tool)}
      />
    );
  }

  function swatches() {
    const editor = EDITOR_OF[activeTool] ?? "none";
    if (editor === "int") return <span className="hint">点击格子，键盘输入数字（Enter 确认 / 右键清除）</span>;
    if (editor === "text") return <span className="hint">点击格子，键盘输入字母（Enter 确认）</span>;
    if (editor === "toggle") return <span className="hint">点击 / 拖动格线画线，右键或再次点击清除</span>;
    if (editor === "outside") return <span className="hint">点击盘面外的行列端，键盘输入（空格分隔多个数）</span>;

    const buttons: JSX.Element[] = [];
    const push = (value: Brush, node: JSX.Element, title: string) => {
      buttons.push(
        <button
          key={String(value)}
          className={`swatch ${brush === value ? "selected" : ""}`}
          title={title}
          onClick={() => setBrush(value)}
        >
          {node}
        </button>,
      );
    };

    push("cycle", <span className="swatch-cycle">⟳</span>, "点击循环切换");

    if (activeTool === "region") {
      for (const id of REGION_BRUSHES) {
        push(id, <span className="swatch-region" style={{ background: regionColor(id) }}>{id}</span>, `区域 ${id}`);
      }
      if (props.onRegionsFromEdges) {
        buttons.push(
          <button key="from-edges" className="swatch clear" title="用 Edge 墙生成房间" onClick={props.onRegionsFromEdges}>
            从 Edge 生成
          </button>,
        );
      }
    } else if (activeTool === "shade") {
      for (const color of SURFACE_COLORS) {
        const selected = (typeof brush === "number" ? brush : surfaceColor) === color.value;
        buttons.push(
          <button
            key={color.value}
            className={`swatch ${selected ? "selected" : ""}`}
            title={`Surface ${color.label} (${color.value})`}
            onClick={() => {
              setSurfaceColor(color.value);
              setBrush(color.value);
            }}
          >
            <span className="swatch-region" style={{ background: color.hex, outline: color.value === 4 ? "1px solid #ccc" : undefined }} />
          </button>,
        );
      }
    } else {
      for (const value of cycleValuesFor(activeTool)) {
        push(value, <GlyphPreview element={activeTool} value={value} />, `值 ${value}`);
      }
    }

    push("erase", <span className="swatch-erase">⌫</span>, "橡皮擦（右键同效）");
    buttons.push(
      <button key="clear" className="swatch clear" title="清空此工具的标记" onClick={() => onClearTool(activeTool)}>
        清空
      </button>,
    );
    return buttons;
  }

  const moreIndexed = MORE_TOOLS.filter((tool) => indexed.includes(tool));
  const moreRest = MORE_TOOLS.filter((tool) => !indexed.includes(tool));

  return (
    <div className="palette tool-rail">
      {spec && (
        <div className="rail-note">
          {spec.zh || spec.en} 绑定 {indexed.map((tool) => TOOL_BY_ID[tool].label).join(" / ") || "（无输入层）"}
        </div>
      )}
      {outputLayers.length > 0 && (
        <>
          <div className="rail-title">解答</div>
          <div className="palette-row chips">
            {outputLayers.map((layer) => {
              const key = `out:${layer.id}`;
              const isOn = visible[key] !== false;
              return (
                <div key={layer.id} className={`chip ${isOn ? "" : "hidden-layer"}`}>
                  <button
                    className="chip-eye"
                    title={isOn ? "隐藏解答" : "显示解答"}
                    onClick={() => setVisible({ ...visible, [key]: !isOn })}
                  >
                    {isOn ? "👁" : "–"}
                  </button>
                  <button className="chip-main" disabled title={`${layer.element} · output`}>
                    {toolIcon(layer.element as DrawTool)}
                    <span>{layer.label}</span>
                    <span className="chip-out">解</span>
                  </button>
                </div>
              );
            })}
          </div>
        </>
      )}
      {GROUPS.map((group) => {
        const tools = PRIMARY_TOOLS.filter((tool) => TOOL_BY_ID[tool].group === group.id)
          .sort((a, b) => Number(indexedSet.has(b)) - Number(indexedSet.has(a)));
        if (!tools.length) return null;
        return (
          <div key={group.id}>
            <div className="rail-title">{group.label}</div>
            <div className="palette-row chips">{tools.map(renderChip)}</div>
          </div>
        );
      })}
      <details className="more-tools" open={moreIndexed.length > 0}>
        <summary className="rail-title">更多符号</summary>
        <div className="palette-row chips">
          {moreIndexed.map(renderChip)}
          {moreRest.map(renderChip)}
        </div>
      </details>
      <div className="rail-title">画笔</div>
      <div className="palette-row swatches">{swatches()}</div>
    </div>
  );
}
