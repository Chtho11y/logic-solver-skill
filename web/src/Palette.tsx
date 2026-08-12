/**
 * Penpa-style toolbar: one chip per layer (activate + show/hide) and, below,
 * the stamp values of the active layer as preview buttons.
 */

import { cycleValues, editorOf, REGION_BRUSHES, regionColor } from "./editors";
import { GlyphPreview } from "./glyphs";
import type { Brush, LayerSpec, PuzzleSpec } from "./types";

export interface PaletteProps {
  spec: PuzzleSpec;
  visible: Record<string, boolean>;
  setVisible: (next: Record<string, boolean>) => void;
  activeId: string;
  setActiveId: (id: string) => void;
  brush: Brush;
  setBrush: (brush: Brush) => void;
  onClearLayer: (layer: LayerSpec) => void;
}

function layerIcon(layer: LayerSpec): JSX.Element {
  const value = cycleValues(layer)[0] ?? 1;
  const color =
    layer.element === "shade" || layer.element === "region"
      ? layer.palette?.["1"] ?? undefined
      : layer.palette?.[String(value)] ?? layer.palette?.["*"];
  return <GlyphPreview element={layer.element} value={layer.element === "number" ? 1 : value} color={color} size={20} />;
}

export function Palette(props: PaletteProps) {
  const { spec, visible, setVisible, activeId, setActiveId, brush, setBrush } = props;
  const active = spec.layers.find((layer) => layer.id === activeId) ?? null;

  function chips() {
    return spec.layers.map((layer) => {
      const isOn = visible[layer.id] !== false;
      const isActive = layer.id === activeId;
      return (
        <div key={layer.id} className={`chip ${isActive ? "active" : ""} ${isOn ? "" : "hidden-layer"}`}>
          <button
            className="chip-eye"
            title={isOn ? "隐藏图层" : "显示图层"}
            onClick={() => setVisible({ ...visible, [layer.id]: !isOn })}
          >
            {isOn ? "👁" : "–"}
          </button>
          <button className="chip-main" onClick={() => setActiveId(layer.id)} title={`${layer.element} · ${layer.role}`}>
            {layerIcon(layer)}
            <span>{layer.label}</span>
            {layer.role === "output" && <span className="chip-out">解</span>}
          </button>
        </div>
      );
    });
  }

  function swatches() {
    if (!active) return null;
    if (active.role === "output") {
      return <span className="hint">解答图层 — 由求解器填充，不能手动编辑</span>;
    }
    const editor = editorOf(active);

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

    if (active.var === "__regions" || (active.element === "region" && active.role === "input")) {
      for (const id of REGION_BRUSHES) {
        push(id, <span className="swatch-region" style={{ background: regionColor(id) }}>{id}</span>, `区域 ${id}`);
      }
    } else if (active.element === "shade") {
      for (const value of cycleValues(active)) {
        const color = active.palette?.[String(value)] ?? "#2b2b2b";
        push(value, <span className="swatch-region" style={{ background: color }} />, `涂色 ${value}`);
      }
    } else {
      for (const value of cycleValues(active)) {
        const color = active.palette?.[String(value)] ?? active.palette?.["*"];
        push(value, <GlyphPreview element={active.element} value={value} color={color} />, `值 ${value}`);
      }
    }

    push("erase", <span className="swatch-erase">⌫</span>, "橡皮擦（右键同效）");
    buttons.push(
      <button key="clear" className="swatch clear" title="清空此图层" onClick={() => props.onClearLayer(active)}>
        清空
      </button>,
    );
    return buttons;
  }

  return (
    <div className="palette">
      <div className="palette-row chips">{chips()}</div>
      <div className="palette-row swatches">{swatches()}</div>
    </div>
  );
}
