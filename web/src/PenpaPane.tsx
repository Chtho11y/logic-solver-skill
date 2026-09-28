/**
 * Hosts the vendored Penpa+ editor (MIT: Opt-Pan 2019, Swaroop Guggilam 2020).
 * The iframe is the middle pane; occupancy / load / export go through StudioBridge.
 */

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type { DrawTool, Drawing } from "./drawing";
import type { LayerCounts } from "./layers";

export type PenpaOccupancy = {
  rows: number;
  cols: number;
  counts: LayerCounts;
  mode: string;
  revision: number;
};

export type PenpaHandle = {
  stamp: (drawing: Drawing) => boolean;
  resize: (rows: number, cols: number) => boolean;
  getRevision: () => number;
  isEmpty: () => boolean;
  setTool: (tool: DrawTool) => void;
  setHidden: (keys: string[], hide: boolean) => void;
  applySolution: (element: string, values: Record<string, number>) => void;
  clearSolution: () => void;
  exportUrl: () => string;
};

type Bridge = {
  stamp: (drawing: Drawing) => boolean;
  resize: (rows: number, cols: number) => boolean;
  getRevision: () => number;
  isEmpty: () => boolean;
  setTool: (tool: string) => void;
  setHidden: (keys: string[], hide: boolean) => void;
  applySolution: (element: string, values: Record<string, number>) => void;
  clearSolution: () => void;
  exportUrl: () => string;
};

interface PenpaPaneProps {
  onOccupancy: (occupancy: PenpaOccupancy) => void;
}

export const PenpaPane = forwardRef<PenpaHandle, PenpaPaneProps>(function PenpaPane(
  { onOccupancy },
  ref,
) {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const occupancyRef = useRef(onOccupancy);
  occupancyRef.current = onOccupancy;

  function bridge(): Bridge | null {
    const win = frameRef.current?.contentWindow as (Window & { StudioBridge?: Bridge }) | null;
    return win?.StudioBridge ?? null;
  }

  useImperativeHandle(ref, () => ({
    stamp(drawing) {
      return bridge()?.stamp(drawing) ?? false;
    },
    resize(rows, cols) { return bridge()?.resize(rows, cols) ?? false; },
    getRevision() { return bridge()?.getRevision() ?? -1; },
    isEmpty() { return bridge()?.isEmpty() ?? true; },
    setTool(tool) {
      bridge()?.setTool(tool);
    },
    setHidden(keys, hide) {
      bridge()?.setHidden(keys, hide);
    },
    applySolution(element, values) {
      bridge()?.applySolution(element, values);
    },
    clearSolution() {
      bridge()?.clearSolution();
    },
    exportUrl() {
      return bridge()?.exportUrl() ?? "";
    },
  }));

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.source !== frameRef.current?.contentWindow || event.origin !== location.origin) return;
      const data = event.data as { type?: string; rows?: number; cols?: number; counts?: LayerCounts; mode?: string; revision?: number };
      if (data?.type === "penpa-ready" || data?.type === "penpa-occupancy") {
        occupancyRef.current({
          rows: data.rows ?? 10,
          cols: data.cols ?? 10,
          counts: data.counts ?? {},
          mode: data.mode ?? "surface",
          revision: data.revision ?? -1,
        });
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  return (
    <div className="penpa-pane">
      <iframe
        ref={frameRef}
        className="penpa-frame"
        title="Penpa+"
        src="/penpa-edit/index.html"
      />
    </div>
  );
});
