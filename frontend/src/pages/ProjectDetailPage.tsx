import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'
import { projectsApi, type ProjectDocument } from '../projects/api'
export default function ProjectDetailPage() {
  const { t } = useTranslation()
  const { projectId } = useParams()
  const [project, setProject] = useState<ProjectDocument | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (!projectId) return
    let active = true
    void projectsApi.get(projectId).then(
      (result) => { if (active) setProject(result) },
      () => { if (active) setError(t('common.projectError')) },
    )
    return () => { active = false }
  }, [projectId, t])
  return (
    <section className="mx-auto max-w-5xl" aria-labelledby="project-title">
      <Link to="/projects" className="text-sm text-slate-600 hover:underline">← {t('common.backToProjects')}</Link>
      {error && <p role="alert" className="mt-4 text-red-700">{error}</p>}
      {!project && !error && <p role="status" className="mt-4">{t('common.loading')}</p>}
      {project && <>
        <h1 id="project-title" className="mt-4 text-2xl font-semibold">{project.name}</h1>
        {project.description && <p className="mt-1 text-slate-600">{project.description}</p>}
        <div className="mt-4 rounded-lg border bg-white p-5">
          <h2 className="font-semibold">{t('common.projectContent')}</h2>
          <p className="mt-2 text-sm text-slate-600">{t('common.emptyWorkspace')}</p>
          <dl className="mt-4 grid gap-2 text-xs text-slate-500 sm:grid-cols-2">
            <div><dt className="inline font-medium">{t('common.projectId')}: </dt><dd className="inline break-all">{project.id}</dd></div>
            <div><dt className="inline font-medium">{t('common.revision')}: </dt><dd className="inline">{project.schema_version}</dd></div>
          </dl>
        </div>
      </>}
    </section>
  )
}
