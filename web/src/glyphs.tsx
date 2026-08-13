/**
 * SVG glyphs for every cell-marker element, shared by the board renderer and
 * the palette previews. A glyph is drawn centred at (cx, cy) inside a cell of
 * side `s`; `color` (from the layer palette) overrides the default look.
 */

const INK = "#2b2b2b";

function trianglePoints(cx: number, cy: number, s: number, value: number): string {
  const h = s / 2;
  const x0 = cx - h, x1 = cx + h, y0 = cy - h, y1 = cy + h;
  switch (value) {
    case 1: return `${x0},${y0} ${x1},${y0} ${x0},${y1}`; // ◤
    case 2: return `${x0},${y0} ${x1},${y0} ${x1},${y1}`; // ◥
    case 3: return `${x1},${y0} ${x1},${y1} ${x0},${y1}`; // ◢
    default: return `${x0},${y0} ${x1},${y1} ${x0},${y1}`; // ◣
  }
}

function starPoints(cx: number, cy: number, r: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const radius = i % 2 === 0 ? r : r * 0.42;
    const angle = -Math.PI / 2 + (i * Math.PI) / 5;
    pts.push(`${cx + radius * Math.cos(angle)},${cy + radius * Math.sin(angle)}`);
  }
  return pts.join(" ");
}

const ARROW_GLYPHS = ["↑", "↓", "←", "→", "↖", "↗", "↙", "↘"];

/** Circle/square/dot fills for the white/black/grey value convention. */
function bwFill(value: number, color?: string): { fill: string; stroke: string } {
  if (color) return { fill: color, stroke: INK };
  if (value === 2) return { fill: INK, stroke: INK };
  if (value === 3) return { fill: "#9aa4ad", stroke: "#9aa4ad" };
  return { fill: "#ffffff", stroke: INK };
}

export function glyph(
  element: string,
  value: number,
  cx: number,
  cy: number,
  s: number,
  color?: string,
): JSX.Element | null {
  if (!value && element !== "number" && element !== "text") return null;

  switch (element) {
    case "circle": {
      const { fill, stroke } = bwFill(value, color);
      return <circle cx={cx} cy={cy} r={s * 0.33} fill={fill} stroke={stroke} strokeWidth={s * 0.055} />;
    }
    case "square": {
      const { fill, stroke } = bwFill(value, color);
      const side = s * 0.56;
      return (
        <rect x={cx - side / 2} y={cy - side / 2} width={side} height={side}
          fill={fill} stroke={stroke} strokeWidth={s * 0.055} />
      );
    }
    case "dot": {
      const { fill, stroke } = bwFill(value, color);
      return <circle cx={cx} cy={cy} r={s * 0.16} fill={fill} stroke={stroke} strokeWidth={s * 0.05} />;
    }
    case "triangle":
      return <polygon points={trianglePoints(cx, cy, s * 0.96, value)} fill={color ?? INK} />;
    case "star":
      return (
        <polygon points={starPoints(cx, cy, s * 0.36)} fill={color ?? "#f6b73c"}
          stroke="#8a6d1a" strokeWidth={s * 0.03} />
      );
    case "cross": {
      const d = s * 0.22;
      const stroke = color ?? "#c0392b";
      return (
        <g stroke={stroke} strokeWidth={s * 0.09} strokeLinecap="round">
          <line x1={cx - d} y1={cy - d} x2={cx + d} y2={cy + d} />
          <line x1={cx - d} y1={cy + d} x2={cx + d} y2={cy - d} />
        </g>
      );
    }
    case "diagonal": {
      const h = s * 0.5;
      const [x1, y1, x2, y2] =
        value === 2 ? [cx - h, cy + h, cx + h, cy - h] : [cx - h, cy - h, cx + h, cy + h];
      return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color ?? INK} strokeWidth={s * 0.08} strokeLinecap="round" />;
    }
    case "arrow":
      return (
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
          fontSize={s * 0.62} fontWeight={700} fill={color ?? INK}>
          {ARROW_GLYPHS[value] ?? "?"}
        </text>
      );
    case "tree":
      return (
        <g>
          <rect x={cx - s * 0.055} y={cy + s * 0.05} width={s * 0.11} height={s * 0.3} fill="#7a5230" />
          <polygon points={`${cx},${cy - s * 0.36} ${cx - s * 0.21},${cy - 0.02 * s} ${cx + s * 0.21},${cy - 0.02 * s}`} fill="#2e7d32" />
          <polygon points={`${cx},${cy - s * 0.2} ${cx - s * 0.27},${cy + s * 0.14} ${cx + s * 0.27},${cy + s * 0.14}`} fill="#43a047" />
        </g>
      );
    case "tent":
      return (
        <g>
          <polygon
            points={`${cx},${cy - s * 0.3} ${cx - s * 0.33},${cy + s * 0.26} ${cx + s * 0.33},${cy + s * 0.26}`}
            fill={color ?? "#f2a33c"} stroke="#7a5230" strokeWidth={s * 0.04} />
          <polygon
            points={`${cx},${cy - s * 0.02} ${cx - s * 0.1},${cy + s * 0.26} ${cx + s * 0.1},${cy + s * 0.26}`}
            fill="#7a5230" />
        </g>
      );
    case "ship": {
      const fill = color ?? "#3d4f5c";
      const h = s * 0.31;
      switch (value) {
        case 1: return <circle cx={cx} cy={cy} r={h} fill={fill} />;
        case 2: return <rect x={cx - h} y={cy - h} width={2 * h} height={2 * h} rx={s * 0.06} fill={fill} />;
        case 3: return <path d={`M ${cx - h} ${cy + h} L ${cx - h} ${cy} A ${h} ${h} 0 0 1 ${cx + h} ${cy} L ${cx + h} ${cy + h} Z`} fill={fill} />;
        case 4: return <path d={`M ${cx - h} ${cy - h} L ${cx - h} ${cy} A ${h} ${h} 0 0 0 ${cx + h} ${cy} L ${cx + h} ${cy - h} Z`} fill={fill} />;
        case 5: return <path d={`M ${cx + h} ${cy - h} L ${cx} ${cy - h} A ${h} ${h} 0 0 0 ${cx} ${cy + h} L ${cx + h} ${cy + h} Z`} fill={fill} />;
        default: return <path d={`M ${cx - h} ${cy - h} L ${cx} ${cy - h} A ${h} ${h} 0 0 1 ${cx} ${cy + h} L ${cx - h} ${cy + h} Z`} fill={fill} />;
      }
    }
    case "wave": {
      const w = s * 0.3, q = s * 0.15, a = s * 0.13;
      const wavePath = (y: number) => `M ${cx - w} ${y} q ${q / 2} ${-a} ${q} 0 q ${q / 2} ${a} ${q} 0 q ${q / 2} ${-a} ${q} 0 q ${q / 2} ${a} ${q} 0`;
      return (
        <g stroke={color ?? "#2f80c2"} strokeWidth={s * 0.055} fill="none" strokeLinecap="round">
          <path d={wavePath(cy - s * 0.1)} />
          <path d={wavePath(cy + s * 0.14)} />
        </g>
      );
    }
    case "bulb":
      return (
        <g>
          <circle cx={cx} cy={cy - s * 0.04} r={s * 0.21} fill={color ?? "#f8d24a"} stroke="#b8860b" strokeWidth={s * 0.04} />
          <rect x={cx - s * 0.085} y={cy + s * 0.15} width={s * 0.17} height={s * 0.1} rx={s * 0.02} fill="#8a929a" />
          <g stroke="#b8860b" strokeWidth={s * 0.035} strokeLinecap="round">
            <line x1={cx - s * 0.3} y1={cy - s * 0.28} x2={cx - s * 0.22} y2={cy - s * 0.2} />
            <line x1={cx + s * 0.3} y1={cy - s * 0.28} x2={cx + s * 0.22} y2={cy - s * 0.2} />
            <line x1={cx} y1={cy - s * 0.4} x2={cx} y2={cy - s * 0.3} />
          </g>
        </g>
      );
    default: {
      const { fill, stroke } = bwFill(value, color);
      return (
        <g>
          <circle cx={cx} cy={cy} r={s * 0.28} fill={fill} stroke={stroke} strokeWidth={s * 0.05} />
          <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
            fontSize={s * 0.28} fontWeight={700} fill={value === 2 ? "#fff" : INK}>
            {value}
          </text>
        </g>
      );
    }
  }
}

/** A standalone mini-preview (for palette buttons). */
export function GlyphPreview({
  element,
  value,
  color,
  size = 26,
}: {
  element: string;
  value: number;
  color?: string;
  size?: number;
}) {
  const c = size / 2;
  let node: JSX.Element | null;
  if (element === "number") {
    node = <text x={c} y={c} textAnchor="middle" dominantBaseline="central" fontSize={size * 0.62} fill={color ?? INK}>{value}</text>;
  } else if (element === "text") {
    node = <text x={c} y={c} textAnchor="middle" dominantBaseline="central" fontSize={size * 0.6} fill={color ?? INK}>A</text>;
  } else if (element === "shade" || element === "region") {
    node = <rect x={3} y={3} width={size - 6} height={size - 6} rx={3} fill={color ?? INK} />;
  } else if (element === "edgeline" || element === "link") {
    node = <line x1={4} y1={c} x2={size - 4} y2={c} stroke={color ?? INK} strokeWidth={3.5} strokeLinecap="round" />;
  } else {
    node = glyph(element, value, c, c, size * 0.9, color);
  }
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {node}
    </svg>
  );
}

export const INK_COLOR = INK;
