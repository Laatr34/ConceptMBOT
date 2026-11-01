import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'
import { projectsApi, type ProjectDocument, type ProjectHistoryEntry } from '../projects/api'

type SaveState = 'saved' | 'saving' | 'invalid' | 'error'

export default function ProjectDetailPage() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const [project, setProject] = useState<ProjectDocument | null>(null)
  const [history, setHistory] = useState<ProjectHistoryEntry[]>([])
  const [draft, setDraft] = useState('')
  const [savedDraft, setSavedDraft] = useState('')
  const [saveState, setSaveState] = useState<SaveState>('saved')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!projectId) return
    let active = true
    void Promise.all([projectsApi.get(projectId), projectsApi.history(projectId)]).then(
      ([result, revisions]) => {
        if (!active) return
        const initialDraft = JSON.stringify(result.data, null, 2)
        setProject(result)
        setHistory(revisions)
        setDraft(initialDraft)
        setSavedDraft(initialDraft)
      },
      () => {
        if (active) setError(t('common.projectError'))
      },
    )
    return () => { active = false }
  }, [projectId, t])

  useEffect(() => {
    if (!projectId || !project || draft === savedDraft) return
    const timeout = window.setTimeout(() => {
      let parsed: unknown
      try {
        parsed = JSON.parse(draft)
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          throw new Error('Project data must be a JSON object')
        }
      } catch {
        setSaveState('invalid')
        return
      }
      setSaveState('saving')
      void projectsApi.autosave(projectId, parsed as Record<string, unknown>).then(
        async (updated) => {
          setProject(updated)
          setSavedDraft(draft)
          setSaveState('saved')
          setHistory(await projectsApi.history(projectId))
        },
        () => setSaveState('error'),
      )
    }, 800)
    return () => window.clearTimeout(timeout)
  }, [draft, savedDraft, project, projectId])

  return (
    <section className="mx-auto max-w-5xl" aria-labelledby="project-title">
      <Link to="/projects" className="text-sm text-slate-600 hover:underline">
        ← {t('common.backToProjects')}
      </Link>
      {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}
      {!project && !error && <p role="status" className="mt-4">{t('common.loading')}</p>}
      {project && (
        <>
          <h1 id="project-title" className="mt-4 text-2xl font-semibold">{project.name}</h1>
          {project.description && <p className="mt-1 text-slate-600">{project.description}</p>}
          <Link
            to={`/mechanical?projectId=${project.id}`}
            className="mt-4 inline-flex rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700"
          >
            {t('mechanical.openProject')}
          </Link>
          <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
            <div className="rounded-lg border bg-white p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">{t('common.projectContent')}</h2>
                <span role="status" className="text-xs text-slate-500">
                  {saveState === 'saving' ? t('common.saving')
                    : saveState === 'invalid' ? t('common.invalidJson')
                    : saveState === 'error' ? t('common.saveError')
                    : t('common.projectSaved')}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{t('common.projectDataHint')}</p>
              <textarea
                aria-label={t('common.projectData')}
                spellCheck={false}
                rows={20}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                className="mt-4 block w-full resize-y rounded border border-slate-300 bg-slate-950 p-3 font-mono text-sm text-slate-100"
              />
              <p className="mt-2 text-xs text-slate-500">
                {t('common.schemaVersion')}: {project.schema_version}
              </p>
            </div>
            <aside className="rounded-lg border bg-white p-4">
              <h2 className="font-semibold">{t('common.revisionHistory')}</h2>
              {history.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">{t('common.noHistory')}</p>
              ) : (
                <ol className="mt-3 space-y-3">
                  {history.map((entry) => (
                    <li key={entry.revision} className="border-l-2 border-slate-200 pl-3">
                      <p className="text-sm font-medium">#{entry.revision} · {entry.action}</p>
                      <time className="text-xs text-slate-500" dateTime={entry.created_at}>
                        {new Date(entry.created_at).toLocaleString()}
                      </time>
                    </li>
                  ))}
                </ol>
              )}
            </aside>
          </div>
        </>
      )}
    </section>
  )
}
