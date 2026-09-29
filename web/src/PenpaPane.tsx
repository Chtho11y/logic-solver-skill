/**
 * Hosts the vendored Penpa+ editor (MIT: Opt-Pan 2019, Swaroop Guggilam 2020).
 * The iframe is the middle pane; occupancy / load / export go through StudioBridge.
 */

import { forwardRef, useEffect, useImperativeHandle, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { DrawTool, Drawing } from "./drawing";
type LayerCounts = Partial<Record<DrawTool, number>>;

export type PenpaOccupancy = {
  rows: number;
  cols: number;
  counts: LayerCounts;
  mode: string;
  revision: number;
  tool?: DrawTool;
  activeVariable?: string;
};

export type PenpaHandle = {
  renameVariable: (from: string, to: string) => boolean;
  deleteVariable: (id: string) => boolean;
  variableCounts: () => Record<string, number>;
  stamp: (drawing: Drawing) => boolean;
  replaceDrawing: (id: string, drawing: Drawing) => boolean;
  loadDocuments: (items: { id: string; drawing: Drawing }[]) => boolean;
  getSelection: () => { tool: DrawTool; activeVariable: string };
  exportDocuments: () => { id: string; url: string }[];
  selectVariable: (id: string, beginDrawing?: boolean) => boolean;
  resize: (rows: number, cols: number) => boolean;
  getRevision: () => number;
  isEmpty: () => boolean;
  setTool: (tool: DrawTool) => void;
  setHidden: (keys: string[], hide: boolean) => void;
  applySolution: (element: string, values: Record<string, number>, palette?: Record<string, string>, id?: string) => void;
  clearSolution: () => void;
  exportUrl: () => string;
};

type Bridge = {
  renameVariable: (from: string, to: string) => boolean;
  deleteVariable: (id: string) => boolean;
  variableCounts: () => Record<string, number>;
  stamp: (drawing: Drawing) => boolean;
  replaceDrawing: (id: string, drawing: Drawing) => boolean;
  loadDocuments: (items: { id: string; drawing: Drawing }[]) => boolean;
  getSelection: () => { tool: DrawTool; activeVariable: string };
  exportDocuments: () => { id: string; url: string }[];
  selectVariable: (id: string, beginDrawing?: boolean) => boolean;
  resize: (rows: number, cols: number) => boolean;
  getRevision: () => number;
  isEmpty: () => boolean;
  setTool: (tool: string) => void;
  setHidden: (keys: string[], hide: boolean) => void;
  applySolution: (element: string, values: Record<string, number>, palette?: Record<string, string>, id?: string) => void;
  clearSolution: () => void;
  exportUrl: () => string;
};

interface PenpaPaneProps {
  onOccupancy: (occupancy: PenpaOccupancy) => void;
  controls: ReactNode;
  variableControls: ReactNode;
}

export const PenpaPane = forwardRef<PenpaHandle, PenpaPaneProps>(function PenpaPane(
  { onOccupancy, controls, variableControls },
  ref,
) {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const [slots, setSlots] = useState<{ controls: HTMLElement; variables: HTMLElement } | null>(null);
  function mountControls() {
    const doc = frameRef.current?.contentDocument;
    if (!doc || !doc.getElementById('top_button')) return;
    const controls = doc.getElementById('studio-controls') || doc.createElement('div');
    controls.id = 'studio-controls';
    doc.getElementById('top_button')!.prepend(controls);
    const variables = doc.getElementById('studio-variables') || doc.createElement('div');
    variables.id = 'studio-variables';
    doc.getElementById('mode_button')!.after(variables);
    setSlots({ controls, variables });
  }
  const occupancyRef = useRef(onOccupancy);
  occupancyRef.current = onOccupancy;

  function bridge(): Bridge | null {
    const win = frameRef.current?.contentWindow as (Window & { StudioBridge?: Bridge }) | null;
    return win?.StudioBridge ?? null;
  }

  useImperativeHandle(ref, () => ({
    renameVariable(from, to) { return bridge()?.renameVariable(from, to) ?? false; },
    deleteVariable(id) { return bridge()?.deleteVariable(id) ?? false; },
    variableCounts() { return bridge()?.variableCounts?.() ?? {}; },
    replaceDrawing(id, drawing) { return bridge()?.replaceDrawing(id, drawing) ?? false; },
    loadDocuments(items) { return bridge()?.loadDocuments(items) ?? false; },
    getSelection() { return bridge()?.getSelection() ?? { tool: "number", activeVariable: "__unbound" }; },
    exportDocuments() { return bridge()?.exportDocuments() ?? []; },
    selectVariable(id, beginDrawing) { return bridge()?.selectVariable(id, beginDrawing) ?? false; },
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
    applySolution(element, values, palette, id) {
      bridge()?.applySolution(element, values, palette, id);
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
      const data = event.data as { type?: string; rows?: number; cols?: number; counts?: LayerCounts; mode?: string; revision?: number; tool?: DrawTool; activeVariable?: string };
      if (data?.type === "penpa-ready" || data?.type === "penpa-occupancy") {
        occupancyRef.current({
          rows: data.rows ?? 10,
          cols: data.cols ?? 10,
          counts: data.counts ?? {},
          mode: data.mode ?? "surface",
          revision: data.revision ?? -1,
          tool: data.tool, activeVariable: data.activeVariable,
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
        onLoad={mountControls}
        className="penpa-frame"
        title="Penpa+"
        src="/penpa-edit/index.html"
      />
      {slots && createPortal(controls, slots.controls)}
      {slots && createPortal(variableControls, slots.variables)}
    </div>
  );
});
