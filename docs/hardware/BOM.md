# Robot Musée Interactif — Hardware list / Liste matériel

Source: [`liste-materiel-robot-musee.pdf`](liste-materiel-robot-musee.pdf) (v1.0, 2026-09-11, 35 references). Machine-readable copy: `backend/app/data/museum_robot_bom.json`.

> **EN** — The PDF is an *inventory only*: it contains **no** electrical/mechanical specifications (voltage, current, mass, torque…). These are intentionally left unknown in RobotLab; calculations depending on them report *not evaluable* until a datasheet is entered in the component library.
>
> **FR** — Le PDF est un *inventaire seul* : il ne contient **aucune** caractéristique électrique/mécanique. Elles restent volontairement inconnues dans RobotLab ; les calculs qui en dépendent renvoient *non évaluable* tant qu'une fiche technique n'est pas saisie dans la bibliothèque.

Document note / Note du document: plan 10–15 % margin on consumables (cables, screws, fuses) and verify voltage/current compatibility between battery, DC-DC converters and drivers.

## Unité de calcul & traitement / Compute & processing

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 1 | Raspberry Pi 5 – 8 Go | 1 | Cerveau principal du robot (IA, navigation, gestion globale) | `sbc` |
| 2 | ESP32 | 1 | Contrôle des moteurs et capteurs en temps réel | `microcontroller` |
| 3 | microSD 128 Go | 1 | Système, logiciels et données du musée | `storage` |
| 4 | Dissipateur + ventilateur Pi 5 | 1 | Refroidissement du Raspberry Pi | `cooling` |

## Locomotion & déplacement / Locomotion

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 5 | Moteurs DC 12 V avec encodeurs | 2 | Déplacement du robot | `dc_motor` |
| 6 | Roues motrices | 2 | Déplacement | `wheel` |
| 7 | Roue folle (caster) | 1 | Maintien de l'équilibre | `caster` |
| 8 | Driver moteur | 1 | Contrôle des moteurs (pont en H) | `motor_driver` |

## Perception & navigation / Perception & navigation

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 9 | LiDAR 2D | 1 | Cartographie et détection des obstacles | `lidar` |
| 10 | IMU 6 axes | 1 | Mesure de l'orientation et des mouvements | `imu` |
| 11 | Capteurs ToF | 2-4 | Détection des obstacles proches | `tof` |
| 12 | Bumpers physiques | 2-4 | Détection des collisions | `bumper` |
| 13 | Caméra USB 1080p | 1 | Vision et interaction avec les visiteurs | `camera` |

## Interaction humain-robot (IHR) / Human-robot interaction

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 14 | Écran tactile 7–10″ | 1 | Interface interactive avec les visiteurs | `display` |
| 15 | Matrice LED HUB75 32×16 RGB | 1 | Visage et animations du robot | `led_matrix` |
| 16 | Microphone USB | 1 | Capture des questions vocales | `microphone` |
| 17 | Haut-parleur | 1 | Réponse vocale du robot | `speaker` |
| 18 | Amplificateur audio | 1 | Amplification du son | `audio_amplifier` |

## Actionneurs & animation / Actuators & animation

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 19 | Servomoteurs MG996R | 2 | Mouvement des bras | `servo` |
| 20 | PCA9685 | 1 | Contrôle des servomoteurs (driver 16 canaux I2C) | `servo_driver` |

## Alimentation & sécurité électrique / Power & electrical safety

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 21 | Batterie 12 V | 1 | Alimentation principale | `battery` |
| 22 | BMS | 1 | Protection de la batterie (surcharge/décharge) | `bms` |
| 23 | Convertisseur DC-DC 12→5 V | 1 | Alimentation du Pi et de l'électronique | `dcdc_converter` |
| 24 | Convertisseur DC-DC 12→6 V | 1 | Alimentation des servomoteurs | `dcdc_converter` |
| 25 | Fusibles | several | Protection électrique | `fuse` |
| 26 | Interrupteur général | 1 | Mise sous/hors tension | `switch` |
| 27 | Arrêt d'urgence | 1 | Arrêt immédiat des moteurs | `emergency_stop` |

## Structure & fixation / Structure & mounting

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 28 | Châssis | 1 | Structure du robot | `chassis` |
| 29 | Support caméra | 1 | Fixation de la caméra | `mount` |
| 30 | Support LiDAR | 1 | Fixation du LiDAR | `mount` |
| 31 | Supports écran/LED | 1 lot | Fixation des interfaces | `mount` |

## Câblage & assemblage / Wiring & assembly

| # | Matériel | Qté | Utilité | Catégorie RobotLab |
|---|---|---|---|---|
| 32 | Câbles électriques | several | Connexions | `cable` |
| 33 | Connecteurs/borniers | several | Connexions fiables | `connector` |
| 34 | Vis, écrous, entretoises | 1 lot | Assemblage | `hardware` |
| 35 | Gaine/serre-câbles | 1 lot | Organisation et protection du câblage | `hardware` |
