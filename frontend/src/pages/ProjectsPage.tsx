import { useCallback, useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { projectsApi, type ProjectSummary } from '../projects/api'

export default function ProjectsPage() {
  const { t } = useTranslation()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setError('')
    try {
      setProjects(await projectsApi.list())
    } catch {
      setError(t('common.projectError'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    setError('')
    try {
      await projectsApi.create({ name: name.trim(), description: description.trim() || null })
      setName('')
      setDescription('')
      await refresh()
    } catch {
      setError(t('common.projectError'))
    } finally {
      setSaving(false)
    }
  }

  async function duplicate(id: string) {
    try {
      await projectsApi.duplicate(id)
      await refresh()
    } catch {
      setError(t('common.projectError'))
    }
  }

  async function remove(id: string) {
    if (!window.confirm(t('common.confirmDelete'))) return
    try {
      await projectsApi.remove(id)
      await refresh()
    } catch {
      setError(t('common.projectError'))
    }
  }

  async function exportProject(id: string) {
    try {
      const projectDocument = await projectsApi.export(id)
      const blob = new Blob([JSON.stringify(projectDocument, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const anchor = window.document.createElement('a')
      anchor.href = url
      anchor.download = `robotlab-${projectDocument.name.replace(/[^a-z0-9-_]/gi, '-')}.json`
      anchor.click()
      URL.revokeObjectURL(url)
    } catch {
      setError(t('common.projectError'))
    }
  }

  async function importProject(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setError('')
    try {
      const content: unknown = JSON.parse(await file.text())
      await projectsApi.import(content)
      await refresh()
    } catch {
      setError(t('common.importError'))
    } finally {
      event.target.value = ''
    }
  }

  return (
    <section className="mx-auto max-w-5xl" aria-labelledby="projects-title">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 id="projects-title" className="text-2xl font-semibold text-slate-900">
            {t('nav.projects')}
          </h1>
          <p className="mt-1 text-sm text-slate-600">{t('common.noProjectsHint')}</p>
        </div>
        <label className="cursor-pointer rounded border border-slate-300 bg-white px-3 py-2 text-sm">
          {t('common.importProject')}
          <input
            type="file"
            accept=".json,application/json"
            className="sr-only"
            onChange={(event) => void importProject(event)}
          />
        </label>
      </div>

      <form onSubmit={create} className="mb-6 grid gap-3 rounded-lg border bg-white p-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">
          {t('common.projectName')}
          <input
            required
            maxLength={120}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          {t('common.projectDescription')}
          <input
            maxLength={2000}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="mt-1 block w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={!name.trim() || saving}
            className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {saving ? t('common.creatingProject') : t('common.createProject')}
          </button>
        </div>
      </form>

      {error && <p role="alert" className="mb-4 rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      {loading ? <p role="status">{t('common.loading')}</p> : projects.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
          <h2 className="font-medium">{t('common.noProjects')}</h2>
          <p className="mt-1 text-sm text-slate-600">{t('common.noProjectsHint')}</p>
        </div>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {projects.map((project) => (
            <li key={project.id} className="rounded-lg border bg-white p-4">
              <h2 className="truncate font-semibold text-slate-900">{project.name}</h2>
              {project.description && <p className="mt-1 text-sm text-slate-600">{project.description}</p>}
              <p className="mt-2 text-xs text-slate-500">
                {t('common.revision')}: {project.revision}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link to={`/projects/${project.id}`} className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white">
                  {t('common.openProject')}
                </Link>
                <button type="button" onClick={() => void duplicate(project.id)} className="rounded border px-3 py-1.5 text-sm">
                  {t('common.duplicateProject')}
                </button>
                <button type="button" onClick={() => void exportProject(project.id)} className="rounded border px-3 py-1.5 text-sm">
                  {t('common.exportProject')}
                </button>
                <button type="button" onClick={() => void remove(project.id)} className="rounded border border-red-200 px-3 py-1.5 text-sm text-red-700">
                  {t('common.deleteProject')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
