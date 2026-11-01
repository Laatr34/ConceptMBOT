import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { diagnosticsApi, type DiagnosticsReport } from '../diagnostics/api'
import { projectsApi, type ProjectSummary } from '../projects/api'

const severityClass = {
  critical: 'border-red-500 bg-red-50',
  high: 'border-orange-500 bg-orange-50',
  medium: 'border-amber-500 bg-amber-50',
  info: 'border-slate-300 bg-slate-50',
}

export default function DiagnosticsPage() {
  const { t } = useTranslation()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [projectsLoading, setProjectsLoading] = useState(true)
  const [report, setReport] = useState<DiagnosticsReport | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    void projectsApi.list().then(
      (items) => {
        if (!active) return
        setProjects(items)
        setSelectedProjectId(items[0]?.id ?? '')
        setProjectsLoading(false)
      },
      () => {
        if (!active) return
        setError(t('diagnostics.projectsLoadError'))
        setProjectsLoading(false)
      },
    )
    return () => { active = false }
  }, [t])

  async function analyze() {
    if (!selectedProjectId) return
    setBusy(true)
    setError(null)
    setReport(null)
    try {
      setReport(await diagnosticsApi.analyzeProject(selectedProjectId))
    } catch {
      setError(t('diagnostics.apiError'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-5xl space-y-5" aria-labelledby="diagnostics-title">
      <div>
        <h1 id="diagnostics-title" className="text-2xl font-semibold text-slate-900">
          {t('nav.diagnostics')}
        </h1>
        <p className="mt-1 text-sm text-slate-600">{t('diagnostics.intro')}</p>
      </div>

      <div role="note" className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
        <p className="font-medium">{t('diagnostics.scopeTitle')}</p>
        <p className="mt-1">{t('diagnostics.scope')}</p>
      </div>

      <div className="flex flex-col gap-3 rounded-lg border bg-white p-4 sm:flex-row sm:items-end">
        <label className="flex-1 text-sm text-slate-700">
          {t('diagnostics.project')}
          <select
            aria-label={t('diagnostics.project')}
            value={selectedProjectId}
            onChange={(event) => {
              setSelectedProjectId(event.target.value)
              setReport(null)
            }}
            disabled={projectsLoading || projects.length === 0}
            className="mt-1 block w-full rounded border border-slate-300 bg-white px-3 py-2"
          >
            <option value="">{t('diagnostics.selectProject')}</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.name}</option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => void analyze()}
          disabled={busy || projectsLoading || !selectedProjectId}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {busy ? t('diagnostics.analyzing') : t('diagnostics.analyze')}
        </button>
      </div>

      {projects.length === 0 && !projectsLoading && (
        <p role="status" className="rounded border bg-white p-4 text-sm text-slate-600">
          {t('diagnostics.noProjects')}
        </p>
      )}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}

      {report && (
        <section className="space-y-4" aria-labelledby="diagnostics-report-title">
          <div className="rounded-lg border bg-white p-4">
            <h2 id="diagnostics-report-title" className="text-lg font-semibold">{report.project_name}</h2>
            <p className="mt-1 text-sm text-slate-600">{t(`diagnostics.status.${report.status}`)}</p>
            <p className="mt-1 text-xs text-slate-500">
              {t('diagnostics.scopeLabel')} · {new Date(report.generated_at).toLocaleString()}
            </p>
          </div>

          {report.diagnostics.length === 0 ? (
            <p role="status" className="rounded border bg-white p-4 text-sm text-slate-700">
              {t('diagnostics.noFindings')}
            </p>
          ) : (
            <div className="space-y-3" aria-label={t('diagnostics.findings')}>
              {report.diagnostics.map((diagnostic) => (
                <article key={diagnostic.code} className={`rounded-lg border-l-4 p-4 ${severityClass[diagnostic.severity]}`}>
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="font-semibold text-slate-900">{diagnostic.problem}</p>
                    <span className="text-xs font-semibold uppercase tracking-wide">
                      {t(`diagnostics.severity.${diagnostic.severity}`)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-700">{t('diagnostics.component')}: {diagnostic.component}</p>
                  {(diagnostic.value !== null || diagnostic.limit !== null) && (
                    <p className="mt-2 text-sm text-slate-700">
                      {t('diagnostics.value')}: {diagnostic.value ?? t('diagnostics.unknown')} {diagnostic.unit ?? ''}
                      {' · '}{t('diagnostics.limit')}: {diagnostic.limit ?? t('diagnostics.notConfigured')}
                    </p>
                  )}
                  {diagnostic.limit_source && (
                    <p className="mt-2 text-sm text-slate-700">
                      <strong>{t('diagnostics.limitSource')}:</strong> {diagnostic.limit_source}
                    </p>
                  )}
                  <p className="mt-2 text-sm text-slate-700">{diagnostic.explanation}</p>
                  <p className="mt-2 text-sm text-slate-900">
                    <strong>{t('diagnostics.correction')}:</strong> {diagnostic.correction}
                  </p>
                  {diagnostic.missing_inputs.length > 0 && (
                    <p className="mt-2 text-xs text-slate-600">
                      {t('diagnostics.missingInputs')}: {diagnostic.missing_inputs.join(', ')}
                    </p>
                  )}
                  <p className="mt-2 text-xs text-slate-500">{t('diagnostics.sourceResult')}: {diagnostic.source_result}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </section>
  )
}
