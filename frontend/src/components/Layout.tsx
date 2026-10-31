import { NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { NAV_ITEMS } from '../navigation'
import { SUPPORTED_LANGUAGES, setLanguage, type Language } from '../i18n'

export default function Layout() {
  const { t, i18n } = useTranslation()
  return (
    <div className="flex min-h-screen bg-slate-100 text-slate-800">
      <aside className="flex w-64 shrink-0 flex-col bg-slate-900 text-slate-100">
        <div className="px-4 py-5">
          <div className="text-lg font-semibold">{t('app.name')}</div>
          <div className="text-xs text-slate-400">{t('app.tagline')}</div>
        </div>
        <nav aria-label="Main" className="flex-1 overflow-y-auto px-2">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `block rounded px-3 py-2 text-sm ${
                      isActive ? 'bg-slate-700 font-medium' : 'hover:bg-slate-800'
                    }`
                  }
                >
                  {t(item.labelKey)}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="border-t border-slate-700 p-3">
          <label htmlFor="lang" className="block text-xs text-slate-400">
            {t('common.language')}
          </label>
          <select
            id="lang"
            value={i18n.language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            className="mt-1 w-full rounded bg-slate-800 p-1 text-sm"
          >
            {SUPPORTED_LANGUAGES.map((l) => (
              <option key={l} value={l}>
                {l.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex-1 p-6">
          <Outlet />
        </main>
        <footer className="border-t border-slate-300 bg-white px-6 py-2 text-xs text-slate-600">
          {t('disclaimer')}
        </footer>
      </div>
    </div>
  )
}
