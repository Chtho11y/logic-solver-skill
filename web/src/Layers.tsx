/** VS Code-style occupancy list: only variables/tools that have marks on the board. */

import { occupiedLayers, type OccupiedLayer } from "./layers";
import type { DrawTool, Drawing } from "./drawing";
import type { PuzzleSpec, SolveResult } from "./types";

export interface LayersProps {
  spec: PuzzleSpec | null;
  drawing: Drawing;
  result: SolveResult | null;
  visible: Record<string, boolean>;
  setVisible: (next: Record<string, boolean>) => void;
  activeTool: DrawTool;
  onSelect: (layer: OccupiedLayer) => void;
}

function Eye({ on }: { on: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden>
      {on ? (
        <path
          fill="currentColor"
          d="M8 3C4.5 3 1.6 5.1 0 8c1.6 2.9 4.5 5 8 5s6.4-2.1 8-5c-1.6-2.9-4.5-5-8-5zm0 8.2A3.2 3.2 0 1 1 8 4.8a3.2 3.2 0 0 1 0 6.4zM8 6a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"
        />
      ) : (
        <path
          fill="currentColor"
          d="M1.2 1.2 0 2.4 2.1 4.5C.8 5.5 0 6.7 0 8c1.6 2.9 4.5 5 8 5 1.3 0 2.5-.3 3.6-.8l2 2 1.2-1.2L1.2 1.2zM8 11.5c-1.9 0-3.5-1.6-3.5-3.5 0-.5.1-1 .3-1.4L7 8.8v.7A1.5 1.5 0 0 0 8.5 11h.7l.7.7c-.4.2-.9.3-1.4.3zm8-3.5c-.4.8-1 1.5-1.7 2.2l-1.1-1.1c.4-.3.7-.7.9-1.1C12.4 6.3 10.3 5 8 5c-.3 0-.6 0-.9.1L5.8 3.8C6.5 3.6 7.2 3.5 8 3.5c3.5 0 6.4 2.1 8 4.5z"
        />
      )}
    </svg>
  );
}

function isHidden(layer: OccupiedLayer, visible: Record<string, boolean>): boolean {
  return layer.hideKeys.some((key) => visible[key] === false);
}

export function Layers(props: LayersProps) {
  const rows = occupiedLayers(props.drawing, props.spec, props.result);

  return (
    <aside className="layers" aria-label="图层">
      <div className="layers-head">图层</div>
      {rows.length === 0 && <div className="layers-empty">图上还没有元素</div>}
      {rows.map((layer) => {
        const hidden = isHidden(layer, props.visible);
        const active = layer.hideKeys.includes(props.activeTool) || layer.tool === props.activeTool;
        return (
          <div
            key={layer.id}
            className={`layer-row ${active ? "active" : ""} ${hidden ? "hidden" : ""}`}
          >
            <button
              className="layer-eye"
              title={hidden ? "显示" : "隐藏"}
              onClick={(e) => {
                e.stopPropagation();
                const next = { ...props.visible };
                const on = hidden;
                for (const key of layer.hideKeys) next[key] = on;
                props.setVisible(next);
              }}
            >
              <Eye on={!hidden} />
            </button>
            <button className="layer-main" onClick={() => props.onSelect(layer)} title={layer.detail}>
              <span className="layer-title">{layer.title}</span>
              <span className="layer-count">{layer.count}</span>
            </button>
          </div>
        );
      })}
    </aside>
  );
}
