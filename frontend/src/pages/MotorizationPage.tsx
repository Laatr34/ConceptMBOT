import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import CalcResultTable, { type CalcRow } from '../components/CalcResultTable'
import { parseOptionalNumber } from '../mechanical/input'
import { motorizationApi, type MotorizationAnalysis, type MotorizationAnalysisInput } from '../motorization/api'

type FieldKey = keyof MotorizationAnalysisInput

const GROUPS: { key: string; fields: { key: FieldKey; label: string }[] }[] = [
  {
    key: 'kinematics',
    fields: [
      { key: 'linear_speed_m_s', label: 'linear_speed_m_s' },
      { key: 'angular_speed_rad_s', label: 'angular_speed_rad_s' },
      { key: 'track_width_m', label: 'track_width_m' },
      { key: 'wheel_radius_m', label: 'wheel_radius_m' },
    ],
  },
  {
    key: 'terrain',
    fields: [
      { key: 'mass_kg', label: 'mass_kg' },
      { key: 'slope_angle_rad', label: 'slope_angle_rad' },
      { key: 'rolling_resistance_coefficient', label: 'rolling_resistance_coefficient' },
      { key: 'friction_coefficient', label: 'friction_coefficient' },
      { key: 'driven_normal_load_n', label: 'driven_normal_load_n' },
      { key: 'driven_wheel_count', label: 'driven_wheel_count' },
    ],
  },
  {
    key: 'motor',
    fields: [
      { key: 'motor_torque_nm', label: 'motor_torque_nm' },
      { key: 'gear_ratio', label: 'gear_ratio' },
      { key: 'gearbox_efficiency', label: 'gearbox_efficiency' },
      { key: 'torque_constant_nm_per_a', label: 'torque_constant_nm_per_a' },
    ],
  },
]

const INITIAL_VALUES: Record<FieldKey, string> = {
  linear_speed_m_s: '',
  angular_speed_rad_s: '',
  track_width_m: '',
  wheel_radius_m: '',
  mass_kg: '',
  slope_angle_rad: '',
  rolling_resistance_coefficient: '',
  driven_wheel_count: '',
  motor_torque_nm: '',
  gear_ratio: '',
  gearbox_efficiency: '',
  friction_coefficient: '',
  driven_normal_load_n: '',
  torque_constant_nm_per_a: '',
}

export default function MotorizationPage() {
  const { t } = useTranslation()
  const [values, setValues] = useState(INITIAL_VALUES)
  const [result, setResult] = useState<MotorizationAnalysis | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const invalid: string[] = []
    const payload = {} as MotorizationAnalysisInput
    for (const group of GROUPS) {
      for (const field of group.fields) {
        const parsed = parseOptionalNumber(values[field.key])
        if (
          parsed === undefined ||
          (field.key === 'driven_wheel_count' && parsed !== null && !Number.isInteger(parsed))
        ) {
          invalid.push(t(`motorization.fields.${field.key}`))
        } else {
          Object.assign(payload, { [field.key]: parsed })
        }
      }
    }
    if (invalid.length > 0) {
      setError(`${t('motorization.invalidNumber')} ${invalid.join(', ')}`)
      return
    }

    setBusy(true)
    try {
      setResult(await motorizationApi.analyze(payload))
    } catch {
      setError(t('motorization.apiError'))
    } finally {
      setBusy(false)
    }
  }

  const rows: CalcRow[] = result
    ? [
        { labelKey: 'motorization.resultName.left_linear_speed', result: result.differential_drive.left_linear_speed },
        { labelKey: 'motorization.resultName.right_linear_speed', result: result.differential_drive.right_linear_speed },
        { labelKey: 'motorization.resultName.left_wheel_angular_speed', result: result.differential_drive.left_wheel_angular_speed },
        { labelKey: 'motorization.resultName.right_wheel_angular_speed', result: result.differential_drive.right_wheel_angular_speed },
        { labelKey: 'motorization.resultName.slope_force', result: result.slope_force },
        { labelKey: 'motorization.resultName.required_wheel_torque', result: result.required_wheel_torque },
        { labelKey: 'motorization.resultName.gearbox_output_torque', result: result.gearbox_output_torque },
        { labelKey: 'motorization.resultName.max_traction_force', result: result.max_traction_force },
        { labelKey: 'motorization.resultName.traction_margin', result: result.traction_margin },
        { labelKey: 'motorization.resultName.torque_current', result: result.torque_current },
      ]
    : []

  return (
    <section className="mx-auto max-w-5xl space-y-5" aria-labelledby="motorization-title">
      <div>
        <h1 id="motorization-title" className="text-2xl font-semibold text-slate-900">
          {t('nav.motorization')}
        </h1>
        <p className="mt-1 text-sm text-slate-600">{t('motorization.intro')}</p>
      </div>

      <div role="note" className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
        <p className="font-medium">{t('motorization.currentWarningTitle')}</p>
        <p className="mt-1">{t('motorization.currentWarning')}</p>
      </div>

      <form onSubmit={(event) => void analyze(event)} className="space-y-5">
        {GROUPS.map((group) => (
          <fieldset key={group.key} className="grid gap-3 rounded-lg border bg-white p-4 sm:grid-cols-2">
            <legend className="px-1 font-semibold">{t(`motorization.groups.${group.key}`)}</legend>
            {group.fields.map((field) => (
              <label key={field.key} className="text-sm text-slate-700">
                {t(`motorization.fields.${field.key}`)}
                <input
                  aria-label={t(`motorization.fields.${field.key}`)}
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
        <button type="submit" disabled={busy}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {busy ? t('motorization.analyzing') : t('motorization.analyze')}
        </button>
      </form>

      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {result && (
        <section className="space-y-3" aria-labelledby="motorization-results">
          <h2 id="motorization-results" className="text-lg font-semibold">{t('motorization.results')}</h2>
          <CalcResultTable rows={rows} />
        </section>
      )}
    </section>
  )
}
