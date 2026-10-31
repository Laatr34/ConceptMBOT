import type en from './en'

type Translations<T> = { [K in keyof T]: T[K] extends string ? string : Translations<T[K]> }

type Dict = Translations<typeof en>

const fr: Dict = {
  app: { name: 'RobotLab Web', tagline: "Atelier virtuel de conception robotique" },
  nav: {
    dashboard: 'Tableau de bord',
    projects: 'Mes projets',
    robotStudio: 'Robot Studio',
    mechanical: 'Conception mécanique',
    electrical: 'Conception électrique',
    power: 'Alimentation & batterie',
    motorization: 'Motorisation',
    sensors: 'Capteurs & électronique',
    simulation: 'Simulation 2D',
    diagnostics: 'Diagnostics',
    library: 'Bibliothèque de composants',
    reports: 'Rapports',
    settings: 'Paramètres',
  },
  common: {
    language: 'Langue',
    notImplemented: 'Pas encore implémenté',
    notImplementedHint:
      "Ce module est prévu mais n'a pas encore de fonctionnalité opérationnelle. Rien sur cette page n'est une donnée réelle.",
    plannedStep: 'Étape de développement prévue',
  },
  disclaimer:
    "Les résultats sont des aides à la conception, pas des calculs certifiés industriellement. Le prototypage et la mesure physiques restent nécessaires.",
}

export default fr
