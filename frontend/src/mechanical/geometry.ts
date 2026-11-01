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
