import { useTranslation } from 'react-i18next'
import { isPositiveFinite, makeTransform, type Point2D } from './geometry'
import type { StabilityStatus } from './api'

const STATUS_STYLE: Record<StabilityStatus, { stroke: string; dash?: string }> = {
  stable: { stroke: '#15803d' },
  marginal: { stroke: '#b45309', dash: '6 3' },
  unstable: { stroke: '#b91c1c', dash: '2 3' },
  unknown: { stroke: '#64748b', dash: '8 4' },
}

export interface TopViewProps {
  wheelbase_m: number | null
  track_width_m: number | null
  /** Convex support polygon (contacts mode). Takes precedence over the rectangle. */
  polygon?: Point2D[] | null
  cog: Point2D | null
  points: Point2D[]
  status: StabilityStatus
}

/** 2D top view to scale. Status is conveyed by stroke style AND text, never by colour alone. */
export default function TopView({
  wheelbase_m,
  track_width_m,
  polygon,
  cog,
  points,
  status,
}: TopViewProps) {
  const { t } = useTranslation()
  const hasPolygon = !!polygon && polygon.length >= 3
  if (hasPolygon) {
    wheelbase_m = 2 * Math.max(...polygon.map((p) => Math.abs(p.x_m)), 1e-9)
    track_width_m = 2 * Math.max(...polygon.map((p) => Math.abs(p.y_m)), 1e-9)
  }
  if (!isPositiveFinite(wheelbase_m) || !isPositiveFinite(track_width_m)) {
    return <p className="text-sm text-slate-600">{t('mechanical.viewNeedsDims')}</p>
  }
  const all = [...(cog ? [cog] : []), ...points, ...(hasPolygon ? polygon : [])]
  const tr = makeTransform(all, wheelbase_m, track_width_m)
  const tl = tr.toSvg({ x_m: wheelbase_m / 2, y_m: track_width_m / 2 })
  const br = tr.toSvg({ x_m: -wheelbase_m / 2, y_m: -track_width_m / 2 })
  const style = STATUS_STYLE[status]
  return (
    <figure>
      <svg
        role="img"
        aria-label={t('mechanical.viewLabel')}
        viewBox={`0 0 ${tr.width} ${tr.height}`}
        className="w-full max-w-md rounded border border-slate-300 bg-white"
      >
        {hasPolygon ? (
          <polygon
            data-testid="support-polygon"
            points={polygon
              .map((p) => {
                const s = tr.toSvg(p)
                return `${s.x},${s.y}`
              })
              .join(' ')}
            fill="none"
            stroke={style.stroke}
            strokeWidth={2}
            strokeDasharray={style.dash}
          />
        ) : (
        <rect
          data-testid="support-rect"
          x={tl.x}
          y={tl.y}
          width={br.x - tl.x}
          height={br.y - tl.y}
          fill="none"
          stroke={style.stroke}
          strokeWidth={2}
          strokeDasharray={style.dash}
        />
        )}
        <text x={tr.width / 2} y={14} textAnchor="middle" fontSize={12} fill="#334155">
          ↑ {t('mechanical.front')}
        </text>
        <text x={8} y={tr.height / 2} fontSize={12} fill="#334155">
          ← {t('mechanical.left')}
        </text>
        {points.map((p, i) => {
          const s = tr.toSvg(p)
          return <circle key={i} data-testid="mass-point" cx={s.x} cy={s.y} r={4} fill="#475569" />
        })}
        {cog && (
          <g data-testid="cog">
            {(() => {
              const s = tr.toSvg(cog)
              return (
                <>
                  <circle cx={s.x} cy={s.y} r={7} fill="none" stroke="#0f172a" strokeWidth={2} />
                  <line x1={s.x - 10} y1={s.y} x2={s.x + 10} y2={s.y} stroke="#0f172a" strokeWidth={2} />
                  <line x1={s.x} y1={s.y - 10} x2={s.x} y2={s.y + 10} stroke="#0f172a" strokeWidth={2} />
                </>
              )
            })()}
          </g>
        )}
      </svg>
      <figcaption className="mt-1 text-xs text-slate-600">
        ◯✚ {t('mechanical.legendCog')} · ● {t('mechanical.legendPoint')} · ▭ {t('mechanical.legendSupport')} (
        {t(`mechanical.stabilityStatus.${status}`)})
      </figcaption>
    </figure>
  )
}
