import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import {
  componentsApi,
  type ComponentCategory,
  type ComponentParameter,
  type ComponentStatus,
  type ComponentSummary,
} from '../components/api'

const CATEGORIES: ComponentCategory[] = [
  'controller', 'motor', 'battery', 'sensor', 'actuator', 'power',
  'display', 'audio', 'mechanical', 'communication', 'other',
]
const STATUSES: ComponentStatus[] = ['incomplete', 'custom', 'verified']

export default function LibraryPage() {
  const { t } = useTranslation()
  const [components, setComponents] = useState<ComponentSummary[]>([])
  const [name, setName] = useState('')
  const [category, setCategory] = useState<ComponentCategory>('other')
  const [status, setStatus] = useState<ComponentStatus>('incomplete')
  const [manufacturer, setManufacturer] = useState('')
  const [model, setModel] = useState('')
  const [datasheetUrl, setDatasheetUrl] = useState('')
  const [parametersJson, setParametersJson] = useState('[]')
  const [missingFieldsJson, setMissingFieldsJson] = useState('[]')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setError('')
    try {
      setComponents(await componentsApi.list())
    } catch {
      setError(t('common.componentError'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!name.trim() || (status === 'verified' && !datasheetUrl.trim())) return
    setSaving(true)
    setError('')
    try {
      const parameters: unknown = JSON.parse(parametersJson)
      const missingFields: unknown = JSON.parse(missingFieldsJson)
      if (!Array.isArray(parameters) || !Array.isArray(missingFields)) {
        throw new Error('The datasheet fields must be JSON arrays')
      }
      await componentsApi.create({
        name: name.trim(),
        category,
        status,
        manufacturer: manufacturer.trim() || null,
        model: model.trim() || null,
        datasheet_url: datasheetUrl.trim() || null,
        parameters: parameters as ComponentParameter[],
        missing_fields: missingFields as string[],
      })
      setName('')
      setManufacturer('')
      setModel('')
      setDatasheetUrl('')
      setParametersJson('[]')
      setMissingFieldsJson('[]')
      setStatus('incomplete')
      setCategory('other')
      await refresh()
    } catch {
      setError(t('common.componentDataJsonError'))
    } finally {
      setSaving(false)
    }
  }

  async function remove(id: string) {
    if (!window.confirm(t('common.confirmDeleteComponent'))) return
    try {
      await componentsApi.remove(id)
      await refresh()
    } catch {
      setError(t('common.componentError'))
    }
  }

  async function exportComponent(id: string) {
    try {
      const document = await componentsApi.export(id)
      const blob = new Blob([JSON.stringify(document, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const anchor = window.document.createElement('a')
      anchor.href = url
      anchor.download = \`robotlab-component-\${document.name.replace(/[^a-z0-9-_]/gi, '-')}.json\`
      anchor.click()
      URL.revokeObjectURL(url)
    } catch {
      setError(t('common.componentError'))
    }
  }

  async function importComponent(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      const document: unknown = JSON.parse(await file.text())
      await componentsApi.import(document)
      await refresh()
    } catch {
      setError(t('common.componentImportError'))
    } finally {
      event.target.value = ''
    }
  }

  return (
    <section className="mx-auto max-w-5xl" aria-labelledby="library-title">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 id="library-title" className="text-2xl font-semibold text-slate-900">{t('nav.library')}</h1>
          <p className="mt-1 text-sm text-slate-600">{t('common.libraryHint')}</p>
        </div>
        <label className="cursor-pointer rounded border border-slate-300 bg-white px-3 py-2 text-sm">
          {t('common.importComponent')}
          <input type="file" accept=".json,application/json" className="sr-only"
            onChange={(event) => void importComponent(event)} />
        </label>
      </div>

      <form onSubmit={create} className="mb-6 grid gap-3 rounded-lg border bg-white p-4 md:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">{t('common.componentName')}
          <input required maxLength={160} value={name} onChange={(event) => setName(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2" />
        </label>
        <label className="text-sm font-medium text-slate-700">{t('common.componentCategory')}
          <select value={category} onChange={(event) => setCategory(event.target.value as ComponentCategory)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2">
            {CATEGORIES.map((item) => <option key={item} value={item}>{t(\`componentCategory.\${item}\`)}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">{t('common.manufacturer')}
          <input maxLength={120} value={manufacturer} onChange={(event) => setManufacturer(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2" />
        </label>
        <label className="text-sm font-medium text-slate-700">{t('common.modelReference')}
          <input maxLength={120} value={model} onChange={(event) => setModel(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2" />
        </label>
        <label className="text-sm font-medium text-slate-700">{t('common.componentStatus')}
          <select value={status} onChange={(event) => setStatus(event.target.value as ComponentStatus)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2">
            {STATUSES.map((item) => <option key={item} value={item}>{t(\`componentStatus.\${item}\`)}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">{t('common.datasheetUrl')}
          <input type="url" required={status === 'verified'} value={datasheetUrl}
            onChange={(event) => setDatasheetUrl(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2" />
        </label>
        <label className="text-sm font-medium text-slate-700 md:col-span-2">{t('common.componentParametersJson')}
          <textarea rows={5} spellCheck={false} value={parametersJson}
            onChange={(event) => setParametersJson(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 p-3 font-mono text-xs" />
          <span className="mt-1 block font-normal text-slate-500">{t('common.componentParametersHint')}</span>
        </label>
        <label className="text-sm font-medium text-slate-700 md:col-span-2">{t('common.missingFieldsJson')}
          <textarea rows={2} spellCheck={false} value={missingFieldsJson}
            onChange={(event) => setMissingFieldsJson(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 p-3 font-mono text-xs" />
        </label>
        <div className="md:col-span-2">
          <button type="submit" disabled={!name.trim() || saving || (status === 'verified' && !datasheetUrl.trim())}
            className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {saving ? t('common.creatingComponent') : t('common.addComponent')}
          </button>
        </div>
      </form>

      {error && <p role="alert" className="mb-4 rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      {loading ? <p role="status">{t('common.loading')}</p> : components.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
          <h2 className="font-medium">{t('common.emptyLibrary')}</h2>
          <p className="mt-1 text-sm text-slate-600">{t('common.emptyLibraryHint')}</p>
        </div>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {components.map((component) => (
            <li key={component.id} className="rounded-lg border bg-white p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h2 className="truncate font-semibold text-slate-900">{component.name}</h2>
                  <p className="mt-1 text-xs text-slate-500">
                    {t(\`componentCategory.\${component.category}\`)}
                    {component.manufacturer ? \` · \${component.manufacturer}\` : ''}
                    {component.model ? \` · \${component.model}\` : ''}
                  </p>
                </div>
                <span className="shrink-0 rounded bg-slate-100 px-2 py-1 text-xs">
                  {t(\`componentStatus.\${component.status}\`)}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{t('common.revision')}: {component.revision}</p>
              <div className="mt-3 flex gap-2">
                <button type="button" onClick={() => void exportComponent(component.id)}
                  className="rounded border px-3 py-1.5 text-sm">{t('common.exportComponent')}</button>
                <button type="button" onClick={() => void remove(component.id)}
                  className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700">{t('common.deleteProject')}</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
