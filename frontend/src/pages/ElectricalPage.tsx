import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import CalcResultTable, { type CalcRow } from '../components/CalcResultTable'
import { parseOptionalNumber } from '../mechanical/input'
import { electricalApi, type ElectricalAnalysis, type ElectricalAnalysisInput } from '../electrical/api'

type FieldKey =
  | 'voltage_v'
  | 'current_a'
  | 'power_w'
  | 'resistance_ohm'
  | 'regulator_input_voltage_v'
  | 'regulator_output_voltage_v'
  | 'regulator_output_current_a'
  | 'regulator_efficiency'
  | 'rail_voltage_v'
  | 'rail_measured_current_a'
  | 'rail_voltage_min_v'
  | 'rail_voltage_max_v'
  | 'rail_current_limit_a'

interface LoadRow {
  id: number
  name: string
  current: string
  power: string
}

let nextLoadId = 1
const emptyLoad = (): LoadRow => ({ id: nextLoadId++, name: '', current: '', power: '' })

const GROUPS: { key: string; fields: { key: FieldKey }[] }[] = [
  {
    key: 'basic',
    fields: [
      { key: 'voltage_v' },
      { key: 'current_a' },
      { key: 'power_w' },
      { key: 'resistance_ohm' },
    ],
  },
  {
    key: 'regulator',
    fields: [
      { key: 'regulator_input_voltage_v' },
      { key: 'regulator_output_voltage_v' },
      { key: 'regulator_output_current_a' },
      { key: 'regulator_efficiency' },
    ],
  },
  {
    key: 'rail',
    fields: [
      { key: 'rail_voltage_v' },
      { key: 'rail_measured_current_a' },
      { key: 'rail_voltage_min_v' },
      { key: 'rail_voltage_max_v' },
      { key: 'rail_current_limit_a' },
    ],
  },
]

const INITIAL_VALUES: Record<FieldKey, string> = {
  voltage_v: '',
  current_a: '',
  power_w: '',
  resistance_ohm: '',
  regulator_input_voltage_v: '',
  regulator_output_voltage_v: '',
  regulator_output_current_a: '',
  regulator_efficiency: '',
  rail_voltage_v: '',
  rail_measured_current_a: '',
  rail_voltage_min_v: '',
  rail_voltage_max_v: '',
  rail_current_limit_a: '',
}

export default function ElectricalPage() {
  const { t } = useTranslation()
  const [values, setValues] = useState(INITIAL_VALUES)
  const [loads, setLoads] = useState<LoadRow[]>(() => [emptyLoad()])
  const [result, setResult] = useState<ElectricalAnalysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const invalid: string[] = []
    const parsed = {} as Record<FieldKey, number | null>
    for (const group of GROUPS) {
      for (const field of group.fields) {
        const value = parseOptionalNumber(values[field.key])
        if (value === undefined) invalid.push(t(`electrical.fields.${field.key}`))
        else parsed[field.key] = value
      }
    }

    const parsedLoads = loads.map((load, index) => {
      const current = parseOptionalNumber(load.current)
      const power = parseOptionalNumber(load.power)
      const name = load.name.trim() || `${t('electrical.load')} ${index + 1}`
      if (current === undefined) invalid.push(`${name}: ${t('electrical.current')}`)
      if (power === undefined) invalid.push(`${name}: ${t('electrical.power')}`)
      if (current !== null && current !== undefined && power !== null && power !== undefined) {
        invalid.push(`${name}: ${t('electrical.oneLoadValue')}`)
      }
      return {
        name,
        current_a: current === undefined ? null : current,
        power_w: power === undefined ? null : power,
      }
    })

    if (invalid.length > 0) {
      setError(`${t('electrical.invalidInput')} ${invalid.join(', ')}`)
      return
    }

    const payload: ElectricalAnalysisInput = {
      voltage_v: parsed.voltage_v,
      current_a: parsed.current_a,
      power_w: parsed.power_w,
      resistance_ohm: parsed.resistance_ohm,
      regulator: {
        input_voltage_v: parsed.regulator_input_voltage_v,
        output_voltage_v: parsed.regulator_output_voltage_v,
        output_current_a: parsed.regulator_output_current_a,
        efficiency: parsed.regulator_efficiency,
      },
      rail: {
        voltage_v: parsed.rail_voltage_v,
        measured_current_a: parsed.rail_measured_current_a,
        voltage_min_v: parsed.rail_voltage_min_v,
        voltage_max_v: parsed.rail_voltage_max_v,
        current_limit_a: parsed.rail_current_limit_a,
        loads: parsedLoads,
      },
    }

    setBusy(true)
    try {
      setResult(await electricalApi.analyze(payload))
    } catch {
      setError(t('electrical.apiError'))
    } finally {
      setBusy(false)
    }
  }

  const rows: CalcRow[] = result
    ? [
        { labelKey: 'electrical.resultName.power', result: result.power },
        { labelKey: 'electrical.resultName.current', result: result.current },
        { labelKey: 'electrical.resultName.voltage_drop', result: result.voltage_drop },
        { labelKey: 'electrical.resultName.regulator_output_power', result: result.regulator_output_power },
        { labelKey: 'electrical.resultName.regulator_input_current', result: result.regulator_input_current },
        { labelKey: 'electrical.resultName.regulator_power_loss', result: result.regulator_power_loss },
        { labelKey: 'electrical.resultName.rail_current', result: result.rail_current },
      ]
    : []

  return (
    <section className="mx-auto max-w-5xl space-y-5" aria-labelledby="electrical-title">
      <div>
        <h1 id="electrical-title" className="text-2xl font-semibold text-slate-900">
          {t('nav.electrical')}
        </h1>
        <p className="mt-1 text-sm text-slate-600">{t('electrical.intro')}</p>
      </div>

      <form onSubmit={(event) => void analyze(event)} className="space-y-5">
        {GROUPS.map((group) => (
          <fieldset key={group.key} className="grid gap-3 rounded-lg border bg-white p-4 sm:grid-cols-2">
            <legend className="px-1 font-semibold">{t(`electrical.groups.${group.key}`)}</legend>
            {group.fields.map((field) => (
              <label key={field.key} className="text-sm text-slate-700">
                {t(`electrical.fields.${field.key}`)}
                <input
                  aria-label={t(`electrical.fields.${field.key}`)}
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

        <fieldset className="space-y-3 rounded-lg border bg-white p-4">
          <legend className="px-1 font-semibold">{t('electrical.loads')}</legend>
          <p className="text-sm text-slate-600">{t('electrical.loadsHint')}</p>
          {loads.map((load, index) => (
            <div key={load.id} className="grid gap-2 rounded border border-slate-200 p-3 sm:grid-cols-[1.2fr_1fr_1fr_auto]">
              <label className="text-sm text-slate-700">
                {t('electrical.load')} {index + 1}
                <input
                  aria-label={`${t('electrical.loadName')} ${index + 1}`}
                  value={load.name}
                  onChange={(event) => setLoads((current) => current.map((item) =>
                    item.id === load.id ? { ...item, name: event.target.value } : item,
                  ))}
                  className="mt-1 block w-full rounded border border-slate-300 p-2"
                />
              </label>
              <label className="text-sm text-slate-700">
                {t('electrical.currentA')}
                <input
                  aria-label={`${t('electrical.currentA')} ${index + 1}`}
                  inputMode="decimal"
                  value={load.current}
                  onChange={(event) => setLoads((current) => current.map((item) =>
                    item.id === load.id ? { ...item, current: event.target.value } : item,
                  ))}
                  className="mt-1 block w-full rounded border border-slate-300 p-2"
                />
              </label>
              <label className="text-sm text-slate-700">
                {t('electrical.powerW')}
                <input
                  aria-label={`${t('electrical.powerW')} ${index + 1}`}
                  inputMode="decimal"
                  value={load.power}
                  onChange={(event) => setLoads((current) => current.map((item) =>
                    item.id === load.id ? { ...item, power: event.target.value } : item,
                  ))}
                  className="mt-1 block w-full rounded border border-slate-300 p-2"
                />
              </label>
              <button type="button" onClick={() => setLoads((current) => current.filter((item) => item.id !== load.id))}
                disabled={loads.length === 1} className="self-end rounded border px-3 py-2 text-sm disabled:opacity-40">
                {t('electrical.removeLoad')}
              </button>
            </div>
          ))}
          <button type="button" onClick={() => setLoads((current) => [...current, emptyLoad()])}
            className="rounded border border-slate-400 px-3 py-2 text-sm">
            + {t('electrical.addLoad')}
          </button>
        </fieldset>

        <button type="submit" disabled={busy}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {busy ? t('electrical.analyzing') : t('electrical.analyze')}
        </button>
      </form>

      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {result && (
        <section className="space-y-4" aria-labelledby="electrical-results">
          <h2 id="electrical-results" className="text-lg font-semibold">{t('electrical.results')}</h2>
          <CalcResultTable rows={rows} />
          <div className="rounded-lg border bg-white p-4">
            <h3 className="font-semibold">{t('electrical.anomalies')}</h3>
            {result.anomalies.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600">{t('electrical.noAnomalies')}</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {result.anomalies.map((anomaly) => (
                  <li key={anomaly.code} className="border-l-2 border-slate-300 pl-3 text-sm">
                    <p className="font-medium">
                      {t(`electrical.severity.${anomaly.severity}`)} · {anomaly.code}
                    </p>
                    <p className="text-slate-700">{anomaly.message}</p>
                    {(anomaly.value !== null || anomaly.threshold !== null) && (
                      <p className="text-xs text-slate-500">
                        {anomaly.value === null ? '—' : anomaly.value} / {anomaly.threshold === null ? '—' : anomaly.threshold} {anomaly.unit}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      )}
    </section>
  )
}
