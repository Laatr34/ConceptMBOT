import { useTranslation } from 'react-i18next'
import type { CalcResult } from '../mechanical/api'

const NUMBER = new Intl.NumberFormat(undefined, { maximumSignificantDigits: 6 })

export interface CalcRow {
  /** i18n key of the human label */
  labelKey: string
  result: CalcResult
}

/** Shows every CalcResult with its value, unit, status, formula, assumptions, limits and gaps. */
export default function CalcResultTable({ rows }: { rows: CalcRow[] }) {
  const { t } = useTranslation()
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-slate-300 text-slate-600">
            <th className="p-2">{t('mechanical.colName')}</th>
            <th className="p-2">{t('mechanical.colValue')}</th>
            <th className="p-2">{t('mechanical.colStatus')}</th>
            <th className="p-2">{t('mechanical.colFormula')}</th>
            <th className="p-2">{t('mechanical.colDetails')}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ labelKey, result }) => {
            const unknown = result.value === null
            return (
              <tr key={result.name} className="border-b border-slate-200 align-top">
                <td className="p-2 font-medium">{t(labelKey)}</td>
                <td className="p-2 whitespace-nowrap">
                  {unknown ? (
                    <span className="text-amber-800">{t('mechanical.notEvaluable')}</span>
                  ) : (
                    `${NUMBER.format(result.value as number)} ${result.unit}`
                  )}
                </td>
                <td className="p-2">{t(`mechanical.resultStatus.${result.status}`)}</td>
                <td className="p-2 font-mono text-xs">{result.formula}</td>
                <td className="p-2 text-xs text-slate-700">
                  {result.missing_inputs.length > 0 && (
                    <p className="text-amber-800">
                      {t('mechanical.missing')}: {result.missing_inputs.join(', ')}
                    </p>
                  )}
                  {result.assumptions.map((a) => (
                    <p key={a}>• {a}</p>
                  ))}
                  {result.limits.map((l) => (
                    <p key={l}>⚠ {l}</p>
                  ))}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
