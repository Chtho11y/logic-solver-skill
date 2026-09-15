/**
 * Hosts the vendored Penpa+ editor (MIT: Opt-Pan 2019, Swaroop Guggilam 2020).
 * The iframe is the middle pane; occupancy / load / export go through StudioBridge.
 */

import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type { DrawTool } from "./drawing";
import type { LayerCounts } from "./layers";

export type PenpaOccupancy = {
  rows: number;
  cols: number;
  counts: LayerCounts;
  mode: string;
};

export type PenpaHandle = {
  loadUrl: (url: string) => void;
  setSize: (rows: number, cols: number) => void;
  setTool: (tool: DrawTool) => void;
  setHidden: (keys: string[], hide: boolean) => void;
  applySolution: (element: string, values: Record<string, number>) => void;
  clearSolution: () => void;
  exportUrl: () => string;
};

type Bridge = {
  loadUrl: (url: string) => boolean;
  setSize: (rows: number, cols: number) => void;
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
    loadUrl(url) {
      bridge()?.loadUrl(url);
    },
    setSize(rows, cols) {
      bridge()?.setSize(rows, cols);
    },
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
      if (event.source !== frameRef.current?.contentWindow) return;
      const data = event.data as { type?: string; rows?: number; cols?: number; counts?: LayerCounts; mode?: string };
      if (data?.type === "penpa-ready" || data?.type === "penpa-occupancy") {
        occupancyRef.current({
          rows: data.rows ?? 10,
          cols: data.cols ?? 10,
          counts: data.counts ?? {},
          mode: data.mode ?? "surface",
        });
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  return (
    <main className="penpa-pane">
      <iframe
        ref={frameRef}
        className="penpa-frame"
        title="Penpa+"
        src="/penpa-edit/index.html"
      />
    </main>
  );
});
