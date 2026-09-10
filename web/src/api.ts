/** Typed client for the Python solver API (see puzzle/server.py). */

import type {
  ElementType,
  Instance,
  PuzzleSpec,
  RuleEntry,
  SolveResult,
  SolverHealth,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok && response.status >= 500) {
    throw new Error(`POST ${path} failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => get<{ ok: boolean; solver: SolverHealth }>("/health"),

  rules: () => get<{ rules: RuleEntry[] }>("/rules").then((r) => r.rules),

  searchRules: (query: string, limit = 10) =>
    get<{ query: string; byName: RuleEntry[]; byRule: RuleEntry[] }>(
      `/rules/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ),

  elements: () => get<{ elements: ElementType[] }>("/elements").then((r) => r.elements),

  puzzles: () => get<{ puzzles: PuzzleSpec[] }>("/puzzles").then((r) => r.puzzles),

  puzzle: (key: string) =>
    get<{ puzzle: PuzzleSpec; sample: Instance | null; rule: RuleEntry | null }>(
      `/puzzles/${encodeURIComponent(key)}`,
    ),

  /**
   * Solve an instance. `source` overrides the bundled DSL program, which is
   * what the in-app rule editor uses to try out a custom rule.
   */
  solve: (
    instance: Instance,
    options: {
      source?: string;
      timeoutMs?: number | null;
      backend?: string;
    } = {},
  ) =>
    post<SolveResult>("/solve", {
      instance,
      source: options.source,
      timeoutMs: options.timeoutMs === undefined ? 60000 : options.timeoutMs,
      backend: options.backend ?? "auto",
    }),
};
