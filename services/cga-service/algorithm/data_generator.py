"""
Générateur de données synthétiques pour ENOLink.
Utilise les coordonnées GPS réelles des 18 ENO de l'UN-CHK.
SEED=42 pour la reproductibilité (BNF-04).
"""
import random
import numpy as np
from faker import Faker

# Données réelles des 18 ENO de l'UN-CHK
ENO_DATA = [
    {'code': 'ENO-DKR', 'nom': 'ENO Dakar', 'region': 'Dakar', 'ville': 'Dakar',
     'latitude': 14.6937, 'longitude': -17.4441},
    {'code': 'ENO-GUE', 'nom': 'ENO Guédiawaye', 'region': 'Dakar', 'ville': 'Guédiawaye',
     'latitude': 14.7745, 'longitude': -17.3986},
    {'code': 'ENO-PIK', 'nom': 'ENO Pikine', 'region': 'Dakar', 'ville': 'Pikine',
     'latitude': 14.7500, 'longitude': -17.3900},
    {'code': 'ENO-RUF', 'nom': 'ENO Rufisque', 'region': 'Dakar', 'ville': 'Rufisque',
     'latitude': 14.7167, 'longitude': -17.2667},
    {'code': 'ENO-THI', 'nom': 'ENO Thiès', 'region': 'Thiès', 'ville': 'Thiès',
     'latitude': 14.7910, 'longitude': -16.9359},
    {'code': 'ENO-MBR', 'nom': 'ENO Mbour', 'region': 'Thiès', 'ville': 'Mbour',
     'latitude': 14.3667, 'longitude': -16.9667},
    {'code': 'ENO-DIO', 'nom': 'ENO Diourbel', 'region': 'Diourbel', 'ville': 'Diourbel',
     'latitude': 14.6500, 'longitude': -16.2333},
    {'code': 'ENO-KAO', 'nom': 'ENO Kaolack', 'region': 'Kaolack', 'ville': 'Kaolack',
     'latitude': 14.1500, 'longitude': -16.0667},
    {'code': 'ENO-FAT', 'nom': 'ENO Fatick', 'region': 'Fatick', 'ville': 'Fatick',
     'latitude': 14.3333, 'longitude': -16.4000},
    {'code': 'ENO-ZIG', 'nom': 'ENO Ziguinchor', 'region': 'Ziguinchor', 'ville': 'Ziguinchor',
     'latitude': 12.5500, 'longitude': -16.2667},
    {'code': 'ENO-KOL', 'nom': 'ENO Kolda', 'region': 'Kolda', 'ville': 'Kolda',
     'latitude': 12.8833, 'longitude': -14.9500},
    {'code': 'ENO-VEL', 'nom': 'ENO Vélingara', 'region': 'Kolda', 'ville': 'Vélingara',
     'latitude': 13.1500, 'longitude': -14.1167},
    {'code': 'ENO-TAM', 'nom': 'ENO Tambacounda', 'region': 'Tambacounda', 'ville': 'Tambacounda',
     'latitude': 13.7667, 'longitude': -13.6667},
    {'code': 'ENO-KED', 'nom': 'ENO Kédougou', 'region': 'Kédougou', 'ville': 'Kédougou',
     'latitude': 12.5500, 'longitude': -12.1833},
    {'code': 'ENO-MAT', 'nom': 'ENO Matam', 'region': 'Matam', 'ville': 'Matam',
     'latitude': 15.6500, 'longitude': -13.2500},
    {'code': 'ENO-POD', 'nom': 'ENO Podor', 'region': 'Saint-Louis', 'ville': 'Podor',
     'latitude': 16.6500, 'longitude': -14.9667},
    {'code': 'ENO-STL', 'nom': 'ENO Saint-Louis', 'region': 'Saint-Louis', 'ville': 'Saint-Louis',
     'latitude': 16.0179, 'longitude': -16.4896},
    {'code': 'ENO-LOU', 'nom': 'ENO Louga', 'region': 'Louga', 'ville': 'Louga',
     'latitude': 15.6167, 'longitude': -16.2333},
]

SPECIALITES_DATA = [
    # Licences
    {'code': 'L-INFO', 'nom': 'Informatique', 'niveau': 'LICENCE'},
    {'code': 'L-GESTION', 'nom': 'Gestion', 'niveau': 'LICENCE'},
    {'code': 'L-DROIT', 'nom': 'Droit', 'niveau': 'LICENCE'},
    {'code': 'L-LETTRES', 'nom': 'Lettres Modernes', 'niveau': 'LICENCE'},
    {'code': 'L-MATHS', 'nom': 'Mathématiques', 'niveau': 'LICENCE'},
    {'code': 'L-PHILO', 'nom': 'Philosophie', 'niveau': 'LICENCE'},
    {'code': 'L-HIST', 'nom': 'Histoire-Géographie', 'niveau': 'LICENCE'},
    {'code': 'L-ECO', 'nom': 'Économie', 'niveau': 'LICENCE'},
    {'code': 'L-SOCIO', 'nom': 'Sociologie', 'niveau': 'LICENCE'},
    {'code': 'L-PSYCH', 'nom': 'Psychologie', 'niveau': 'LICENCE'},
    {'code': 'L-COMM', 'nom': 'Communication', 'niveau': 'LICENCE'},
    {'code': 'L-COMPTA', 'nom': 'Comptabilité', 'niveau': 'LICENCE'},
    {'code': 'L-MARKET', 'nom': 'Marketing', 'niveau': 'LICENCE'},
    {'code': 'L-FINANCE', 'nom': 'Finance', 'niveau': 'LICENCE'},
    {'code': 'L-RH', 'nom': 'Ressources Humaines', 'niveau': 'LICENCE'},
    {'code': 'L-ANGLAIS', 'nom': 'Anglais', 'niveau': 'LICENCE'},
    {'code': 'L-ARABE', 'nom': 'Arabe', 'niveau': 'LICENCE'},
    {'code': 'L-BIOLOGIE', 'nom': 'Biologie', 'niveau': 'LICENCE'},
    {'code': 'L-CHIMIE', 'nom': 'Chimie', 'niveau': 'LICENCE'},
    # Masters
    {'code': 'M-IL', 'nom': 'Ingénierie Logicielle', 'niveau': 'MASTER'},
    {'code': 'M-RESEAUX', 'nom': 'Réseaux et Télécommunications', 'niveau': 'MASTER'},
    {'code': 'M-IA', 'nom': 'Intelligence Artificielle', 'niveau': 'MASTER'},
    {'code': 'M-GESTION', 'nom': 'Management des Organisations', 'niveau': 'MASTER'},
    {'code': 'M-DROIT', 'nom': 'Droit des Affaires', 'niveau': 'MASTER'},
    {'code': 'M-ECO', 'nom': 'Économie du Développement', 'niveau': 'MASTER'},
    {'code': 'M-FINANCE', 'nom': 'Finance et Comptabilité', 'niveau': 'MASTER'},
]


def generer_donnees_synthetiques(
    nb_apprenants: int = 200,
    eno_ids: list = None,
    seed: int = 42
) -> list[dict]:
    """
    Génère des données synthétiques d'apprenants.

    Les coordonnées GPS sont générées autour des ENO avec une dispersion
    réaliste (rayon de 50 km max).
    """
    random.seed(seed)
    np.random.seed(seed)

    try:
        fake = Faker('fr_FR')
        Faker.seed(seed)
    except Exception:
        fake = None

    if eno_ids is None:
        eno_ids = list(range(len(ENO_DATA)))

    # Distribution des apprenants par ENO (pondérée par la taille des villes)
    poids = [3, 2, 2, 1, 2, 1, 1, 2, 1, 1, 1, 0.5, 1, 0.5, 0.5, 0.5, 1, 1]
    poids_filtres = [poids[i] for i in eno_ids]
    total_poids = sum(poids_filtres)
    proportions = [p / total_poids for p in poids_filtres]

    nb_par_eno = np.random.multinomial(nb_apprenants, proportions)

    apprenants = []
    compteur_ine = 1

    noms_senegalais = [
        'Diallo', 'Ba', 'Sow', 'Diop', 'Ndiaye', 'Fall', 'Mbaye', 'Sarr', 'Sy',
        'Cissé', 'Konaté', 'Traoré', 'Coulibaly', 'Diouf', 'Faye', 'Gaye', 'Kane',
        'Mbodj', 'Ndoye', 'Sène', 'Thiaw', 'Wade', 'Badji', 'Camara', 'Dème',
        'Guèye', 'Lô', 'Manga', 'Ndour', 'Sagna', 'Tamba', 'Balde', 'Barry',
        'Niang', 'Mballo', 'Diouf', 'Coly', 'Diatta', 'Sambou', 'Tendeng',
    ]
    prenoms_senegalais = [
        'Moussa', 'Ibrahima', 'Mamadou', 'Ousmane', 'Abdoulaye', 'Cheikh', 'Modou',
        'Pape', 'Serigne', 'Alioune', 'Babacar', 'Boubacar', 'Daouda', 'El Hadji',
        'Fatou', 'Aminata', 'Mariama', 'Aissatou', 'Rokhaya', 'Ndéye', 'Khady',
        'Coumba', 'Adja', 'Binta', 'Fatoumata', 'Marème', 'Sokhna', 'Yacine',
        'Alpha', 'Tafsir', 'Seydou', 'Lamine', 'Samba', 'Demba', 'Malick',
        'Assane', 'Birame', 'Cheikhou', 'Djibril', 'Elhadji',
    ]

    for eno_idx, nb in zip(eno_ids, nb_par_eno):
        eno = ENO_DATA[eno_idx]

        for _ in range(nb):
            # Générer des coordonnées GPS autour de l'ENO (dispersion réaliste)
            # Rayon max : 50 km, distribution normale centrée sur l'ENO
            rayon_deg = 0.45  # ~50 km en degrés
            lat = eno['latitude'] + np.random.normal(0, rayon_deg / 2)
            lon = eno['longitude'] + np.random.normal(0, rayon_deg / 2)

            # Contraindre dans les limites du Sénégal
            lat = max(12.3, min(16.7, lat))
            lon = max(-17.5, min(-11.3, lon))

            nom = random.choice(noms_senegalais)
            prenom = random.choice(prenoms_senegalais)
            ine = f"UNCHK{str(compteur_ine).zfill(6)}"
            email = f"{prenom.lower().replace(' ', '').replace('é', 'e').replace('è', 'e')}.{nom.lower()}_{compteur_ine}@unchk.edu.sn"

            apprenants.append({
                'ine': ine,
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'eno_id': eno_idx,  # index dans ENO_DATA
                'eno_code': eno['code'],
            })
            compteur_ine += 1

    random.shuffle(apprenants)
    return apprenants
