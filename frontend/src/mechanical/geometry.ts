/**
 * Drawing helpers for the 2D top view. They only convert metres to SVG pixels:
 * no technical result is computed here (the backend is the source of truth).
 *
 * Robot frame: x forward, y left, origin at the centre of the support rectangle.
 * SVG frame:   x right,   y down  -> forward is drawn upwards, left is drawn to the left.
 */
export interface Point2D {
  x_m: number
  y_m: number
}

export interface ViewTransform {
  scale: number // pixels per metre
  width: number
  height: number
  toSvg: (p: Point2D) => { x: number; y: number }
}

export function makeTransform(
  points: Point2D[],
  wheelbase_m: number,
  track_width_m: number,
  width = 420,
  height = 420,
  padding = 40,
): ViewTransform {
  let halfX = wheelbase_m / 2
  let halfY = track_width_m / 2
  for (const p of points) {
    if (Number.isFinite(p.x_m)) halfX = Math.max(halfX, Math.abs(p.x_m))
    if (Number.isFinite(p.y_m)) halfY = Math.max(halfY, Math.abs(p.y_m))
  }
  // Forward (x) maps to the vertical axis, left (y) to the horizontal axis.
  const scale = Math.min((width - 2 * padding) / (2 * halfY), (height - 2 * padding) / (2 * halfX))
  return {
    scale,
    width,
    height,
    toSvg: (p) => ({ x: width / 2 - p.y_m * scale, y: height / 2 - p.x_m * scale }),
  }
}

export function isPositiveFinite(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value > 0
}

type XY = [number, number]
const cross = (o: XY, a: XY, b: XY) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

/** Counter-clockwise convex hull, used ONLY to draw the support polygon (the backend computes the margin). */
export function convexHull(points: Point2D[]): Point2D[] {
  const pts: XY[] = [...new Set(points.map((p) => `${p.x_m},${p.y_m}`))]
    .map((k) => k.split(',').map(Number) as XY)
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
  if (pts.length <= 2) return pts.map(([x_m, y_m]) => ({ x_m, y_m }))
  const build = (input: XY[]) => {
    const out: XY[] = []
    for (const p of input) {
      while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], p) <= 0) out.pop()
      out.push(p)
    }
    return out
  }
  const lower = build(pts)
  const upper = build([...pts].reverse())
  return [...lower.slice(0, -1), ...upper.slice(0, -1)].map(([x_m, y_m]) => ({ x_m, y_m }))
}
