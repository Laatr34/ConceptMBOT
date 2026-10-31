const en = {
  app: { name: 'RobotLab Web', tagline: 'Virtual robotics design studio' },
  nav: {
    dashboard: 'Dashboard', projects: 'My projects', robotStudio: 'Robot Studio',
    mechanical: 'Mechanical Design', electrical: 'Electrical Design',
    power: 'Power & Battery', motorization: 'Motorization',
    sensors: 'Sensors & Electronics', simulation: '2D Simulation',
    diagnostics: 'Diagnostics', library: 'Component Library',
    reports: 'Reports', settings: 'Settings',
  },
  common: {
    language: 'Language', notImplemented: 'Not implemented yet',
    notImplementedHint: 'This module is planned but has no working feature yet. Nothing on this page is real data.',
    plannedStep: 'Planned development step', loading: 'Loading…',
    projectName: 'Project name', projectDescription: 'Description',
    createProject: 'Create project', creatingProject: 'Creating…',
    noProjects: 'No project yet', noProjectsHint: 'Create your first project to start designing a robot.',
    openProject: 'Open', duplicateProject: 'Duplicate', deleteProject: 'Delete',
    confirmDelete: 'Delete this project? This action cannot be undone.',
    projectError: 'Unable to load projects. Check that the API is running.',
    backToProjects: 'Back to projects', projectContent: 'Project workspace',
    emptyWorkspace: 'This project has no design data yet.',
    projectId: 'Project ID', revision: 'Revision',
  },
  disclaimer: 'Results are design aids, not industrially certified calculations. Physical prototyping and measurement remain necessary.',
} as const
export default en
