export interface NavItem {
  path: string
  labelKey: string
  /** Development step (docs/PLAN.md) in which the module becomes functional. */
  step: number
}

export const NAV_ITEMS: readonly NavItem[] = [
  { path: '/', labelKey: 'nav.dashboard', step: 12 },
  { path: '/projects', labelKey: 'nav.projects', step: 1 },
  { path: '/robot-studio', labelKey: 'nav.robotStudio', step: 12 },
  { path: '/mechanical', labelKey: 'nav.mechanical', step: 6 },
  { path: '/electrical', labelKey: 'nav.electrical', step: 8 },
  { path: '/power', labelKey: 'nav.power', step: 4 },
  { path: '/motorization', labelKey: 'nav.motorization', step: 5 },
  { path: '/sensors', labelKey: 'nav.sensors', step: 9 },
  { path: '/simulation', labelKey: 'nav.simulation', step: 10 },
  { path: '/diagnostics', labelKey: 'nav.diagnostics', step: 7 },
  { path: '/library', labelKey: 'nav.library', step: 2 },
  { path: '/documentation', labelKey: 'nav.documentation', step: 0 },
  { path: '/reports', labelKey: 'nav.reports', step: 11 },
  { path: '/settings', labelKey: 'nav.settings', step: 12 },
]
