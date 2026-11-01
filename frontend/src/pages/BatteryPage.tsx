import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import CalcResultTable, { type CalcRow } from '../components/CalcResultTable'
import { parseOptionalNumber } from '../mechanical/input'
import { batteryApi, type BatteryAnalysis, type BatteryAnalysisInput } from '../battery/api'

type FieldKey = Exclude<keyof BatteryAnalysisInput, 'estimated_power_assumptions'>

const FIELDS: { key: FieldKey; group: 'cell' | 'usable' | 'load' }[] = [
  { key: 'cell_voltage_v', group: 'cell' },
  { key: 'series_count', group: 'cell' },
  { key: 'cell_capacity_ah', group: 'cell' },
  { key: 'parallel_count', group: 'cell' },
  { key: 'depth_of_discharge', group: 'usable' },
  { key: 'efficiency', group: 'usable' },
  { key: 'average_power_w', group: 'load' },
  { key: 'estimated_average_power_w', group: 'load' },
  { key: 'measured_duration_s', group: 'load' },
]

const GROUPS = ['cell', 'usable', 'load'] as const
const INITIAL_VALUES: Record<FieldKey, string> = {
  cell_voltage_v: '',
  series_count: '',
  cell_capacity_ah: '',
  parallel_count: '',
  depth_of_discharge: '',
  efficiency: '',
  average_power_w: '',
  estimated_average_power_w: '',
  measured_duration_s: '',
}

export default function BatteryPage() {
  const { t } = useTranslation()
  const [values, setValues] = useState(INITIAL_VALUES)
  const [assumptions, setAssumptions] = useState('')
  const [result, setResult] = useState<BatteryAnalysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const invalid: string[] = []
    const parsed = {} as Record<FieldKey, number | null>
    for (const field of FIELDS) {
      const value = parseOptionalNumber(values[field.key])
      if (
        value === undefined ||
        ((field.key === 'series_count' || field.key === 'parallel_count') &&
          value !== null && !Number.isInteger(value))
      ) {
        invalid.push(t(`battery.fields.${field.key}`))
      } else {
        parsed[field.key] = value
      }
    }
    if (invalid.length > 0) {
      setError(`${t('battery.invalidInput')} ${invalid.join(', ')}`)
      return
    }

    const payload: BatteryAnalysisInput = {
      cell_voltage_v: parsed.cell_voltage_v,
      series_count: parsed.series_count,
      cell_capacity_ah: parsed.cell_capacity_ah,
      parallel_count: parsed.parallel_count,
      depth_of_discharge: parsed.depth_of_discharge,
      efficiency: parsed.efficiency,
      average_power_w: parsed.average_power_w,
      estimated_average_power_w: parsed.estimated_average_power_w,
      estimated_power_assumptions: assumptions.split('\n').map((item) => item.trim()).filter(Boolean),
      measured_duration_s: parsed.measured_duration_s,
    }

    setBusy(true)
    try {
      setResult(await batteryApi.analyze(payload))
    } catch {
      setError(t('battery.apiError'))
    } finally {
      setBusy(false)
    }
  }

  const rows: CalcRow[] = result
    ? [
        { labelKey: 'battery.resultName.pack_voltage', result: result.pack_voltage },
        { labelKey: 'battery.resultName.pack_capacity_ah', result: result.pack_capacity_ah },
        { labelKey: 'battery.resultName.pack_capacity_c', result: result.pack_capacity_c },
        { labelKey: 'battery.resultName.nominal_energy_wh', result: result.nominal_energy_wh },
        { labelKey: 'battery.resultName.nominal_energy_j', result: result.nominal_energy_j },
        { labelKey: 'battery.resultName.usable_energy_wh', result: result.usable_energy_wh },
        { labelKey: 'battery.resultName.usable_energy_j', result: result.usable_energy_j },
        { labelKey: 'battery.resultName.theoretical_autonomy_h', result: result.theoretical_autonomy_h },
        { labelKey: 'battery.resultName.theoretical_autonomy_s', result: result.theoretical_autonomy_s },
        { labelKey: 'battery.resultName.estimated_autonomy_h', result: result.estimated_autonomy_h },
        { labelKey: 'battery.resultName.estimated_autonomy_s', result: result.estimated_autonomy_s },
        { labelKey: 'battery.resultName.measured_autonomy_h', result: result.measured_autonomy_h },
        { labelKey: 'battery.resultName.measured_autonomy_s', result: result.measured_autonomy_s },
      ]
    : []

  return (
    <section className="mx-auto max-w-5xl space-y-5" aria-labelledby="battery-title">
      <div>
        <h1 id="battery-title" className="text-2xl font-semibold text-slate-900">
          {t('nav.power')}
        </h1>
        <p className="mt-1 text-sm text-slate-600">{t('battery.intro')}</p>
      </div>

      <div role="note" className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
        <p className="font-medium">{t('battery.limitsTitle')}</p>
        <p className="mt-1">{t('battery.limits')}</p>
      </div>

      <form onSubmit={(event) => void analyze(event)} className="space-y-5">
        {GROUPS.map((group) => (
          <fieldset key={group} className="grid gap-3 rounded-lg border bg-white p-4 sm:grid-cols-2">
            <legend className="px-1 font-semibold">{t(`battery.groups.${group}`)}</legend>
            {FIELDS.filter((field) => field.group === group).map((field) => (
              <label key={field.key} className="text-sm text-slate-700">
                {t(`battery.fields.${field.key}`)}
                <input
                  aria-label={t(`battery.fields.${field.key}`)}
                  inputMode="decimal"
                  value={values[field.key]}
                  onChange={(event) => setValues((current) => ({
                    ...current,
                    [field.key]: event.target.value,
                  }))}
                  className="mt-1 block w-full rounded border border-slate-300 bg-white px-3 py-2"
                />
              </label>
            ))}
          </fieldset>
        ))}

        <label className="block text-sm text-slate-700">
          {t('battery.estimatedAssumptions')}
          <textarea
            aria-label={t('battery.estimatedAssumptions')}
            value={assumptions}
            onChange={(event) => setAssumptions(event.target.value)}
            rows={3}
            className="mt-1 block w-full rounded border border-slate-300 bg-white px-3 py-2"
          />
          <span className="mt-1 block text-xs text-slate-500">{t('battery.assumptionsHint')}</span>
        </label>

        <button type="submit" disabled={busy}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {busy ? t('battery.analyzing') : t('battery.analyze')}
        </button>
      </form>

      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {result && (
        <section className="space-y-3" aria-labelledby="battery-results">
          <h2 id="battery-results" className="text-lg font-semibold">{t('battery.results')}</h2>
          <CalcResultTable rows={rows} />
        </section>
      )}
    </section>
  )
}
