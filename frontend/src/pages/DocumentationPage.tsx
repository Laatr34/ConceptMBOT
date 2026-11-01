import { useTranslation } from 'react-i18next'

const sections = [
  'overview',
  'workflow',
  'architecture',
  'modules',
  'data',
  'calculations',
  'api',
  'limits',
  'roadmap',
  'development',
] as const

export default function DocumentationPage() {
  const { t } = useTranslation()

  return (
    <section aria-labelledby="docs-title" className="mx-auto max-w-6xl space-y-8">
      <header className="rounded-2xl bg-slate-900 p-7 text-white shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
          {t('documentation.eyebrow')}
        </p>
        <h1 id="docs-title" className="mt-2 text-3xl font-bold tracking-tight">
          {t('documentation.title')}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
          {t('documentation.intro')}
        </p>
        <div className="mt-5 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full bg-white/10 px-3 py-1">{t('documentation.version')}</span>
          <span className="rounded-full bg-white/10 px-3 py-1">React · TypeScript · FastAPI</span>
          <span className="rounded-full bg-white/10 px-3 py-1">FR / EN</span>
        </div>
      </header>

      <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)]">
        <nav aria-label={t('documentation.contents')} className="h-fit rounded-xl border border-slate-200 bg-white p-4 lg:sticky lg:top-5">
          <h2 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">
            {t('documentation.contents')}
          </h2>
          <ul className="space-y-2 text-sm">
            {sections.map((section) => (
              <li key={section}>
                <a className="text-slate-600 hover:text-slate-950 hover:underline" href={`#${section}`}>
                  {t(`documentation.nav.${section}`)}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="min-w-0 space-y-8">
          <article id="overview" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.overview.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.overview.body')}</p>
            <div className="grid gap-3 sm:grid-cols-3">
              {(['design', 'calculate', 'verify'] as const).map((item) => (
                <div key={item} className="rounded-xl border border-slate-200 bg-white p-4">
                  <h3 className="font-semibold text-slate-900">{t(`documentation.overview.cards.${item}.title`)}</h3>
                  <p className="mt-1 text-sm leading-5 text-slate-600">{t(`documentation.overview.cards.${item}.body`)}</p>
                </div>
              ))}
            </div>
          </article>

          <article id="workflow" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.workflow.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.workflow.body')}</p>
            <ol className="grid gap-2 sm:grid-cols-2">
              {(['project', 'library', 'design', 'review'] as const).map((item, index) => (
                <li key={item} className="flex gap-3 rounded-lg border border-slate-200 bg-white p-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">{index + 1}</span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">{t(`documentation.workflow.steps.${item}.title`)}</h3>
                    <p className="mt-1 text-sm text-slate-600">{t(`documentation.workflow.steps.${item}.body`)}</p>
                  </div>
                </li>
              ))}
            </ol>
          </article>

          <article id="architecture" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.architecture.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.architecture.body')}</p>
            <div className="overflow-x-auto rounded-xl bg-slate-950 p-5 font-mono text-xs leading-6 text-slate-200">
              <pre>{`RobotLab Web
├── frontend/       React · TypeScript · Vite · Tailwind
│   └── src/
│       ├── pages/      Screens and documentation
│       ├── components/ Shared UI and API clients
│       ├── projects/   Project types and API client
│       ├── mechanical/ Mechanical UI, geometry and API types
│       └── i18n/       French and English translations
├── backend/        Python · FastAPI · Pydantic · SQLAlchemy
│   └── app/
│       ├── api/          HTTP routes and schemas
│       ├── application/  Use cases and services
│       ├── domain/      Domain types and physical units
│       ├── engines/     Pure calculation engines
│       └── infrastructure/ Persistence and adapters
└── docs/           Conventions, plan, ADRs and hardware data`}</pre>
            </div>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.architecture.rule')}</p>
          </article>

          <article id="modules" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.modules.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.modules.body')}</p>
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              {(['projects', 'library', 'mechanical', 'electrical', 'battery', 'motorization', 'diagnostics', 'circuit', 'sensors', 'simulation', 'reports'] as const).map((module) => {
                const state = module === 'projects' || module === 'library' ? 'done' : module === 'mechanical' ? 'partial' : 'planned'
                return (
                  <div key={module} className="flex flex-col gap-2 border-b border-slate-100 p-4 last:border-0 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900">{t(`documentation.modules.items.${module}.title`)}</h3>
                      <p className="mt-1 max-w-2xl text-sm text-slate-600">{t(`documentation.modules.items.${module}.body`)}</p>
                    </div>
                    <span className={`w-fit shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${state === 'done' ? 'bg-emerald-50 text-emerald-800' : state === 'partial' ? 'bg-amber-50 text-amber-800' : 'bg-slate-100 text-slate-600'}`}>
                      {t(`documentation.status.${state}`)}
                    </span>
                  </div>
                )
              })}
            </div>
          </article>

          <article id="data" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.data.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.data.body')}</p>
            <div className="grid gap-3 md:grid-cols-2">
              {(['projects', 'components'] as const).map((item) => (
                <div key={item} className="rounded-xl border border-slate-200 bg-white p-4">
                  <h3 className="font-semibold text-slate-900">{t(`documentation.data.cards.${item}.title`)}</h3>
                  <p className="mt-1 text-sm leading-5 text-slate-600">{t(`documentation.data.cards.${item}.body`)}</p>
                </div>
              ))}
            </div>
          </article>

          <article id="calculations" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.calculations.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.calculations.body')}</p>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
              {(['unknown', 'traceable', 'status', 'limits'] as const).map((item) => (
                <li key={item}>{t(`documentation.calculations.rules.${item}`)}</li>
              ))}
            </ul>
          </article>

          <article id="api" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.api.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.api.body')}</p>
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <code className="text-sm font-semibold text-slate-900">http://localhost:8000/docs</code>
              <p className="mt-1 text-sm text-slate-600">{t('documentation.api.swagger')}</p>
            </div>
          </article>

          <article id="limits" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.limits.title')}</h2>
            <div role="note" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950">
              {t('documentation.limits.warning')}
            </div>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
              {(['notCertified', 'datasheets', 'mechanics', 'notImplemented'] as const).map((item) => (
                <li key={item}>{t(`documentation.limits.items.${item}`)}</li>
              ))}
            </ul>
          </article>

          <article id="roadmap" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.roadmap.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.roadmap.body')}</p>
            <p className="text-sm"><a className="font-medium text-blue-700 underline" href="https://github.com/Laatr34/ConceptMBOT/blob/chatgpt/docs/PLAN.md" target="_blank" rel="noreferrer">{t('documentation.roadmap.link')}</a></p>
          </article>

          <article id="development" className="scroll-mt-6 space-y-3">
            <h2 className="text-xl font-semibold text-slate-900">{t('documentation.development.title')}</h2>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.development.body')}</p>
            <div className="grid gap-3 md:grid-cols-2">
              {(['backend', 'frontend'] as const).map((item) => (
                <div key={item} className="rounded-xl border border-slate-200 bg-white p-4">
                  <h3 className="mb-2 font-semibold text-slate-900">{t(`documentation.development.${item}.title`)}</h3>
                  <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-3 text-xs leading-5 text-slate-100">{t(`documentation.development.${item}.commands`)}</pre>
                </div>
              ))}
            </div>
            <p className="text-sm leading-6 text-slate-700">{t('documentation.development.final')}</p>
          </article>

          <footer className="border-t border-slate-200 pt-4 text-xs text-slate-500">
            {t('documentation.footer')}
          </footer>
        </div>
      </div>
    </section>
  )
}
