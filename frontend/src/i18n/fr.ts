import type en from './en'
type Translations<T> = { [K in keyof T]: T[K] extends string ? string : Translations<T[K]> }
type Dict = Translations<typeof en>
const fr: Dict = {
  app: { name: 'RobotLab Web', tagline: "Atelier virtuel de conception robotique" },
  nav: {
    dashboard: 'Tableau de bord', projects: 'Mes projets', robotStudio: 'Robot Studio',
    mechanical: 'Conception mécanique', electrical: 'Conception électrique',
    power: 'Alimentation & batterie', motorization: 'Motorisation',
    sensors: 'Capteurs & électronique', simulation: 'Simulation 2D',
    diagnostics: 'Diagnostics', library: 'Bibliothèque de composants',
    reports: 'Rapports', settings: 'Paramètres',
  },
  common: {
    language: 'Langue', notImplemented: 'Pas encore implémenté',
    notImplementedHint: "Ce module est prévu mais n'a pas encore de fonctionnalité opérationnelle. Rien sur cette page n'est une donnée réelle.",
    plannedStep: 'Étape de développement prévue', loading: 'Chargement…',
    projectName: 'Nom du projet', projectDescription: 'Description',
    createProject: 'Créer le projet', creatingProject: 'Création…',
    noProjects: 'Aucun projet pour le moment', noProjectsHint: 'Crée ton premier projet pour commencer à concevoir un robot.',
    openProject: 'Ouvrir', duplicateProject: 'Dupliquer', deleteProject: 'Supprimer',
    confirmDelete: 'Supprimer ce projet ? Cette action est irréversible.',
    projectError: "Impossible de charger les projets. Vérifie que l'API fonctionne.",
    importProject: 'Importer JSON', exportProject: 'Exporter JSON',
    importError: "Échec de l'import. Vérifie que le fichier est un document JSON RobotLab valide.",
    backToProjects: 'Retour aux projets', projectContent: 'Espace de travail du projet',
    projectData: 'Données du projet (JSON)', projectDataHint: 'Modifie les données du projet au format JSON. Les changements sont enregistrés automatiquement.',
    projectSaved: 'Enregistré', saving: 'Enregistrement…', invalidJson: 'JSON invalide — non enregistré',
    saveError: 'Échec de la sauvegarde — vérifie ta connexion', revisionHistory: 'Historique des révisions',
    noHistory: 'Aucune révision', projectId: 'Identifiant du projet', revision: 'Révision',
    schemaVersion: 'Version du schéma du document',
    libraryHint: 'Enregistre les composants à partir de leurs fiches techniques ou de tes propres mesures vérifiées. La bibliothèque démarre vide.',
    componentName: 'Nom du composant', componentCategory: 'Catégorie', manufacturer: 'Fabricant',
    modelReference: 'Modèle / référence', componentStatus: 'État des données', datasheetUrl: 'URL de la fiche technique',
    creatingComponent: 'Ajout…', addComponent: 'Ajouter le composant', importComponent: 'Importer JSON',
    exportComponent: 'Exporter JSON', emptyLibrary: 'La bibliothèque de composants est vide',
    emptyLibraryHint: 'Ajoute un composant manuellement ou importe un document JSON. Aucune valeur matérielle n’est préremplie.',
    componentError: 'Impossible de charger ou enregistrer la bibliothèque de composants.',
    componentImportError: "Échec de l'import. Vérifie que le fichier est un document JSON de composant valide.",
    confirmDeleteComponent: 'Supprimer ce composant ? Cette action est irréversible.',
  },
  componentCategory: {
    controller: 'Contrôleur', motor: 'Moteur', battery: 'Batterie', sensor: 'Capteur',
    actuator: 'Actionneur', power: 'Alimentation', display: 'Écran', audio: 'Audio',
    mechanical: 'Mécanique', communication: 'Communication', other: 'Autre',
  },
  componentStatus: {
    verified: 'Fiche vérifiée', custom: 'Données personnalisées', incomplete: 'Incomplet',
  },
  disclaimer: "Les résultats sont des aides à la conception, pas des calculs certifiés industriellement. Le prototypage et la mesure physiques restent nécessaires.",
}
export default fr
