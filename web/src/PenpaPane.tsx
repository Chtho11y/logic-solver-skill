/**
 * Penpa+ Classic chrome around the board: mode / sub-mode / style, then the grid.
 * Layout and labels follow penpa-edit (MIT: Opt-Pan 2019, Swaroop Guggilam 2020).
 */

import { Board, type BoardProps } from "./Board";
import { cycleValuesFor, EDITOR_OF, REGION_BRUSHES, regionColor } from "./editors";
import {
  SURFACE_COLORS,
  TOOL_BY_ID,
  type DrawTool,
} from "./drawing";
import { GlyphPreview } from "./glyphs";
import type { Brush } from "./types";

export type PenpaMode = "surface" | "number" | "shape" | "line" | "edge" | "combi";

const MODES: { id: PenpaMode; label: string; tools: DrawTool[] }[] = [
  { id: "surface", label: "Surface", tools: ["shade"] },
  { id: "number", label: "Number", tools: ["number", "text"] },
  { id: "shape", label: "Shape", tools: ["circle", "square", "triangle", "star", "cross", "tree", "tent", "ship", "wave", "bulb", "arrow"] },
  { id: "line", label: "Line", tools: ["link"] },
  { id: "edge", label: "Edge", tools: ["edgeline", "diagonal", "dot"] },
  { id: "combi", label: "Composite", tools: ["region", "outside"] },
];

function modeOf(tool: DrawTool): PenpaMode {
  return MODES.find((mode) => mode.tools.includes(tool))?.id ?? "number";
}

const SHAPE_LABEL: Partial<Record<DrawTool, string>> = {
  circle: "Circle",
  square: "Square",
  triangle: "Triangle",
  star: "Star",
  cross: "Cross",
  tree: "Tree",
  tent: "Tent",
  ship: "Ship",
  wave: "Wave",
  bulb: "Bulb",
  arrow: "Arrow",
};

export interface PenpaPaneProps extends BoardProps {
  brush: Brush;
  setBrush: (brush: Brush) => void;
  setActiveTool: (tool: DrawTool) => void;
  surfaceColor: number;
  setSurfaceColor: (value: number) => void;
  onClearTool: (tool: DrawTool) => void;
  onRegionsFromEdges?: () => void;
}

export function PenpaPane(props: PenpaPaneProps) {
  const {
    activeTool,
    setActiveTool,
    brush,
    setBrush,
    onClearTool,
  } = props;
  const mode = modeOf(activeTool);
  const current = MODES.find((item) => item.id === mode)!;

  function setMode(next: PenpaMode) {
    const tools = MODES.find((item) => item.id === next)!.tools;
    setActiveTool(tools.includes(activeTool) ? activeTool : tools[0]);
  }

  return (
    <main className="penpa-pane">
      <div className="penpa-toolbar">
        <div className="penpa-row">
          <span className="penpa-label">Mode:</span>
          {MODES.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`penpa-mode ${mode === item.id ? "on" : ""}`}
              onClick={() => setMode(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        {current.tools.length > 1 && (
          <div className="penpa-row">
            <span className="penpa-label">Sub:</span>
            {current.tools.map((tool) => (
              <button
                key={tool}
                type="button"
                className={`penpa-sub ${activeTool === tool ? "on" : ""}`}
                title={TOOL_BY_ID[tool].hint}
                onClick={() => setActiveTool(tool)}
              >
                {mode === "shape" ? (
                  <>
                    <GlyphPreview element={tool} value={1} size={16} />
                    <span>{SHAPE_LABEL[tool] ?? TOOL_BY_ID[tool].label}</span>
                  </>
                ) : (
                  TOOL_BY_ID[tool].label
                )}
              </button>
            ))}
          </div>
        )}
        <div className="penpa-row wrap">
          <span className="penpa-label">Style:</span>
          {styleButtons(props)}
          <button type="button" className="penpa-sub" onClick={() => setBrush("erase")} title="橡皮擦（右键同效）">
            Erase
          </button>
          <button type="button" className="penpa-sub" onClick={() => onClearTool(activeTool)} title="清空当前模式">
            Delete
          </button>
        </div>
      </div>
      <div className="board-area">
        <Board
          spec={props.spec}
          drawing={props.drawing}
          result={props.result}
          viewport={props.viewport}
          visible={props.visible}
          activeTool={props.activeTool}
          brush={brush}
          selection={props.selection}
          draft={props.draft}
          onEdit={props.onEdit}
          onSelect={props.onSelect}
        />
      </div>
    </main>
  );
}

function styleButtons(props: PenpaPaneProps): JSX.Element[] {
  const { activeTool, brush, setBrush, surfaceColor, setSurfaceColor } = props;
  const editor = EDITOR_OF[activeTool] ?? "none";
  const out: JSX.Element[] = [];

  if (editor === "int") {
    out.push(
      <span key="hint" className="penpa-hint">
        点击格子后用键盘输入数字
      </span>,
    );
    return out;
  }
  if (editor === "text") {
    out.push(
      <span key="hint" className="penpa-hint">
        点击格子后用键盘输入字母
      </span>,
    );
    return out;
  }
  if (editor === "toggle") {
    out.push(
      <span key="hint" className="penpa-hint">
        拖动画线，右键清除
      </span>,
    );
    return out;
  }
  if (editor === "outside") {
    out.push(
      <span key="hint" className="penpa-hint">
        点击盘外端点，键盘输入（空格分隔）
      </span>,
    );
    return out;
  }

  out.push(
    <button
      key="cycle"
      type="button"
      className={`penpa-sub ${brush === "cycle" ? "on" : ""}`}
      onClick={() => setBrush("cycle")}
    >
      Cycle
    </button>,
  );

  if (activeTool === "region") {
    for (const id of REGION_BRUSHES) {
      out.push(
        <button
          key={id}
          type="button"
          className={`penpa-swatch ${brush === id ? "on" : ""}`}
          style={{ background: regionColor(id) }}
          onClick={() => setBrush(id)}
        >
          {id}
        </button>,
      );
    }
    if (props.onRegionsFromEdges) {
      out.push(
        <button key="from-edges" type="button" className="penpa-sub" onClick={props.onRegionsFromEdges}>
          Edge→Region
        </button>,
      );
    }
    return out;
  }

  if (activeTool === "shade") {
    for (const color of SURFACE_COLORS) {
      const selected = (typeof brush === "number" ? brush : surfaceColor) === color.value;
      out.push(
        <button
          key={color.value}
          type="button"
          className={`penpa-swatch ${selected ? "on" : ""}`}
          title={`${color.label} (${color.value})`}
          style={{ background: color.hex, color: color.value === 4 ? "#fff" : "#222" }}
          onClick={() => {
            setSurfaceColor(color.value);
            setBrush(color.value);
          }}
        >
          {color.value}
        </button>,
      );
    }
    return out;
  }

  for (const value of cycleValuesFor(activeTool)) {
    out.push(
      <button
        key={value}
        type="button"
        className={`penpa-swatch ${brush === value ? "on" : ""}`}
        onClick={() => setBrush(value)}
        title={`值 ${value}`}
      >
        <GlyphPreview element={activeTool} value={value} size={18} />
      </button>,
    );
  }
  return out;
}
