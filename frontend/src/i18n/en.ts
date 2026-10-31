const en = {
  app: { name: 'RobotLab Web', tagline: 'Virtual robotics design studio' },
  nav: {
    dashboard: 'Dashboard',
    projects: 'My projects',
    robotStudio: 'Robot Studio',
    mechanical: 'Mechanical Design',
    electrical: 'Electrical Design',
    power: 'Power & Battery',
    motorization: 'Motorization',
    sensors: 'Sensors & Electronics',
    simulation: '2D Simulation',
    diagnostics: 'Diagnostics',
    library: 'Component Library',
    reports: 'Reports',
    settings: 'Settings',
  },
  common: {
    language: 'Language',
    notImplemented: 'Not implemented yet',
    notImplementedHint:
      'This module is planned but has no working feature yet. Nothing on this page is real data.',
    plannedStep: 'Planned development step',
  },
  disclaimer:
    'Results are design aids, not industrially certified calculations. Physical prototyping and measurement remain necessary.',
} as const

export default en
