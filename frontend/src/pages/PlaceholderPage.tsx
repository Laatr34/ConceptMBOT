import { useTranslation } from 'react-i18next'

export default function PlaceholderPage({ labelKey, step }: { labelKey: string; step: number }) {
  const { t } = useTranslation()
  return (
    <section aria-labelledby="page-title">
      <h1 id="page-title" className="text-2xl font-semibold text-slate-900">
        {t(labelKey)}
      </h1>
      <div
        role="status"
        className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-4 text-amber-900"
      >
        <p className="font-medium">{t('common.notImplemented')}</p>
        <p className="mt-1 text-sm">{t('common.notImplementedHint')}</p>
        <p className="mt-2 text-sm">
          {t('common.plannedStep')}: {step}
        </p>
      </div>
    </section>
  )
}
