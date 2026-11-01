import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import CalcResultTable, { type CalcRow } from '../components/CalcResultTable'
import TopView from '../mechanical/TopView'
import {
  mechanicalApi,
  type CalcResult,
  type ContactsAnalysis,
  type MechanicalAnalysis,
  type MechanicalAnalysisInput,
  type StabilityStatus,
} from '../mechanical/api'
import { convexHull } from '../mechanical/geometry'
import { buildContactsInput, buildInput, type ContactRow, type Row } from '../mechanical/input'

let nextId = 1
const emptyRow = (): Row => ({ id: nextId++, name: '', mass: '', x: '', y: '', z: '' })
const emptyContact = (name = ''): ContactRow => ({ id: nextId++, name, x: '', y: '' })
type Mode = 'rectangle' | 'contacts'

export default function MechanicalPage() {
  const { t } = useTranslation()
  const [rows, setRows] = useState<Row[]>(() => [emptyRow()])
  const [wheelbase, setWheelbase] = useState('')
  const [track, setTrack] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>('rectangle')
  const [contacts, setContacts] = useState<ContactRow[]>(() => [
    emptyContact('left_wheel'),
    emptyContact('right_wheel'),
    emptyContact('caster'),
  ])
  const [analysis, setAnalysis] = useState<MechanicalAnalysis | null>(null)
  const [contactsAnalysis, setContactsAnalysis] = useState<ContactsAnalysis | null>(null)
  const [analysedInput, setAnalysedInput] = useState<MechanicalAnalysisInput | null>(null)
  const [polygon, setPolygon] = useState<{ x_m: number; y_m: number }[] | null>(null)
  const [drawn, setDrawn] = useState<{ x_m: number; y_m: number }[]>([])

  const update = (id: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r) => (r.id === id ? { ...r, ...patch } : r)))

  async function run() {
    setBusy(true)
    setError(null)
    try {
      if (mode === 'rectangle') {
        const built = buildInput(rows, wheelbase, track)
        if ('invalid' in built) {
          setError(`${t('mechanical.invalidNumber')} ${built.invalid.join(', ')}`)
          return
        }
        setAnalysis(await mechanicalApi.analyze(built.input))
        setContactsAnalysis(null)
        setAnalysedInput(built.input)
        setPolygon(null)
        setDrawn(
          built.input.mass_points.flatMap((p) =>
            p.x_m !== null && p.y_m !== null ? [{ x_m: p.x_m, y_m: p.y_m }] : [],
          ),
        )
      } else {
        const built = buildContactsInput(rows, contacts)
        if ('invalid' in built) {
          setError(`${t('mechanical.invalidNumber')} ${built.invalid.join(', ')}`)
          return
        }
        setContactsAnalysis(await mechanicalApi.analyzeContacts(built.input))
        setAnalysis(null)
        setPolygon(convexHull(built.input.contacts.map((c) => ({ x_m: c.x_m, y_m: c.y_m }))))
        setDrawn(
          built.input.mass_points.flatMap((p) =>
            p.x_m !== null && p.y_m !== null ? [{ x_m: p.x_m, y_m: p.y_m }] : [],
          ),
        )
      }
    } catch {
      setError(t('mechanical.apiError'))
    } finally {
      setBusy(false)
    }
  }

  const cog = (analysis ?? contactsAnalysis)?.center_of_gravity
  const cogPoint =
    cog && cog.x_m.value !== null && cog.y_m.value !== null
      ? { x_m: cog.x_m.value, y_m: cog.y_m.value }
      : null
  const drawnPoints = drawn
  const status: StabilityStatus | null = analysis
    ? analysis.stability.status
    : contactsAnalysis
      ? contactsAnalysis.stability.status
      : null

  const rectRows: CalcRow[] = analysis
    ? [
        { labelKey: 'mechanical.resultName.total_mass', result: analysis.center_of_gravity.total_mass },
        { labelKey: 'mechanical.resultName.cog_x', result: analysis.center_of_gravity.x_m },
        { labelKey: 'mechanical.resultName.cog_y', result: analysis.center_of_gravity.y_m },
        { labelKey: 'mechanical.resultName.cog_z', result: analysis.center_of_gravity.z_m },
        { labelKey: 'mechanical.resultName.front_left', result: analysis.wheel_loads.front_left_n },
        { labelKey: 'mechanical.resultName.front_right', result: analysis.wheel_loads.front_right_n },
        { labelKey: 'mechanical.resultName.rear_left', result: analysis.wheel_loads.rear_left_n },
        { labelKey: 'mechanical.resultName.rear_right', result: analysis.wheel_loads.rear_right_n },
        { labelKey: 'mechanical.resultName.margin_x', result: analysis.stability.margin_x_m },
        { labelKey: 'mechanical.resultName.margin_y', result: analysis.stability.margin_y_m },
        { labelKey: 'mechanical.resultName.margin', result: analysis.stability.overall_margin_m },
      ]
    : []
  const contactRows: CalcRow[] = contactsAnalysis
    ? [
        { labelKey: 'mechanical.resultName.total_mass', result: contactsAnalysis.center_of_gravity.total_mass },
        { labelKey: 'mechanical.resultName.cog_x', result: contactsAnalysis.center_of_gravity.x_m },
        { labelKey: 'mechanical.resultName.cog_y', result: contactsAnalysis.center_of_gravity.y_m },
        { labelKey: 'mechanical.resultName.cog_z', result: contactsAnalysis.center_of_gravity.z_m },
        ...contactsAnalysis.contact_loads.map((r: CalcResult) => ({
          label: t('mechanical.contactLoad', { name: r.name.replace('mechanical.contact_load.', '') }),
          result: r,
        })),
        { label: t('mechanical.supportMargin'), result: contactsAnalysis.stability.margin_m },
      ]
    : []
  const resultRows = mode === 'rectangle' ? rectRows : contactRows

  const field = 'w-full rounded border border-slate-300 bg-white p-1 text-sm'
  return (
    <section aria-labelledby="mech-title" className="space-y-5">
      <h1 id="mech-title" className="text-2xl font-semibold text-slate-900">
        {t('mechanical.title')}
      </h1>
      <p className="text-sm text-slate-700">{t('mechanical.intro')}</p>
      <fieldset className="flex flex-wrap gap-4 text-sm">
        <legend className="font-medium">{t('mechanical.mode')}</legend>
        {(['rectangle', 'contacts'] as const).map((m) => (
          <label key={m} className="flex items-center gap-2">
            <input type="radio" name="mech-mode" checked={mode === m} onChange={() => setMode(m)} />
            {t(m === 'rectangle' ? 'mechanical.modeRect' : 'mechanical.modeContacts')}
          </label>
        ))}
      </fieldset>
      <div role="note" className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
        <p className="font-medium">{t('mechanical.modelWarningTitle')}</p>
        <p>{t(mode === 'rectangle' ? 'mechanical.modelWarning' : 'mechanical.contactsNote')}</p>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">{t('mechanical.massPoints')}</h2>
        <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] gap-2 text-xs text-slate-600">
          <span>{t('mechanical.name')}</span>
          <span>{t('mechanical.mass')}</span>
          <span>{t('mechanical.x')}</span>
          <span>{t('mechanical.y')}</span>
          <span>{t('mechanical.z')}</span>
          <span />
        </div>
        {rows.map((r, i) => (
          <div key={r.id} className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] items-center gap-2">
            <input aria-label={`${t('mechanical.name')} ${i + 1}`} className={field} value={r.name}
              onChange={(e) => update(r.id, { name: e.target.value })} />
            <input aria-label={`${t('mechanical.mass')} ${i + 1}`} inputMode="decimal" className={field} value={r.mass}
              onChange={(e) => update(r.id, { mass: e.target.value })} />
            <input aria-label={`${t('mechanical.x')} ${i + 1}`} inputMode="decimal" className={field} value={r.x}
              onChange={(e) => update(r.id, { x: e.target.value })} />
            <input aria-label={`${t('mechanical.y')} ${i + 1}`} inputMode="decimal" className={field} value={r.y}
              onChange={(e) => update(r.id, { y: e.target.value })} />
            <input aria-label={`${t('mechanical.z')} ${i + 1}`} inputMode="decimal" className={field} value={r.z}
              onChange={(e) => update(r.id, { z: e.target.value })} />
            <button type="button" className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
              onClick={() => setRows((rs) => rs.filter((x) => x.id !== r.id))}>
              {t('mechanical.removePoint')}
            </button>
          </div>
        ))}
        <button type="button" className="rounded border border-slate-400 px-3 py-1 text-sm hover:bg-slate-100"
          onClick={() => setRows((rs) => [...rs, emptyRow()])}>
          + {t('mechanical.addPoint')}
        </button>
      </div>

      {mode === 'contacts' && (
        <div className="space-y-2">
          <h2 className="text-lg font-medium">{t('mechanical.contacts')}</h2>
          {contacts.map((c, i) => (
            <div key={c.id} className="grid max-w-xl grid-cols-[2fr_1fr_1fr_auto] items-center gap-2">
              <input aria-label={`${t('mechanical.contactName')} ${i + 1}`} className={field} value={c.name}
                onChange={(e) => setContacts((cs) => cs.map((x) => (x.id === c.id ? { ...x, name: e.target.value } : x)))} />
              <input aria-label={`${t('mechanical.x')} ${t('mechanical.contacts')} ${i + 1}`} inputMode="decimal" className={field} value={c.x}
                onChange={(e) => setContacts((cs) => cs.map((x) => (x.id === c.id ? { ...x, x: e.target.value } : x)))} />
              <input aria-label={`${t('mechanical.y')} ${t('mechanical.contacts')} ${i + 1}`} inputMode="decimal" className={field} value={c.y}
                onChange={(e) => setContacts((cs) => cs.map((x) => (x.id === c.id ? { ...x, y: e.target.value } : x)))} />
              <button type="button" className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                onClick={() => setContacts((cs) => cs.filter((x) => x.id !== c.id))}>
                {t('mechanical.removePoint')}
              </button>
            </div>
          ))}
          <button type="button" className="rounded border border-slate-400 px-3 py-1 text-sm hover:bg-slate-100"
            onClick={() => setContacts((cs) => [...cs, emptyContact()])}>
            + {t('mechanical.addContact')}
          </button>
        </div>
      )}

      {mode === 'rectangle' && (
      <div className="grid max-w-md grid-cols-2 gap-3">
        <label className="text-sm">
          {t('mechanical.wheelbase')}
          <input inputMode="decimal" className={field} value={wheelbase} onChange={(e) => setWheelbase(e.target.value)} />
        </label>
        <label className="text-sm">
          {t('mechanical.trackWidth')}
          <input inputMode="decimal" className={field} value={track} onChange={(e) => setTrack(e.target.value)} />
        </label>
      </div>
      )}

      <button type="button" disabled={busy} onClick={run}
        className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">
        {busy ? t('mechanical.analyzing') : t('mechanical.analyze')}
      </button>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}

      {status && (
        <div className="space-y-4">
          <h2 className="text-lg font-medium">{t('mechanical.stability')}: {t(`mechanical.stabilityStatus.${status}`)}</h2>
          <h2 className="text-lg font-medium">{t('mechanical.view2d')}</h2>
          <TopView
            wheelbase_m={analysedInput?.wheelbase_m ?? null}
            track_width_m={analysedInput?.track_width_m ?? null}
            polygon={polygon}
            cog={cogPoint}
            points={drawnPoints}
            status={status}
          />
          <h2 className="text-lg font-medium">{t('mechanical.results')}</h2>
          <CalcResultTable rows={resultRows} />
        </div>
      )}
    </section>
  )
}
