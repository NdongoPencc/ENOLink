"""
Fonctions géographiques pour ENOLink.
Formule de Haversine pour le calcul des distances GPS.
"""
import math
import numpy as np


RAYON_TERRE_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance en km entre deux points GPS.
    Formule : d = 2R · arcsin(√(sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlon/2)))
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * RAYON_TERRE_KM * math.asin(math.sqrt(a))


def haversine_batch(lat1: float, lon1: float, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Calcule les distances entre un point fixe et un tableau de points."""
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lats_r = np.radians(lats)
    lons_r = np.radians(lons)
    dlat = lats_r - lat1_r
    dlon = lons_r - lon1_r
    a = np.sin(dlat / 2) ** 2 + math.cos(lat1_r) * np.cos(lats_r) * np.sin(dlon / 2) ** 2
    return 2 * RAYON_TERRE_KM * np.arcsin(np.sqrt(a))


def calculer_d_geo(partition: list[list[dict]], enos: dict) -> float:
    """
    Calcule D_geo(S) : distance géographique moyenne entre chaque apprenant
    et l'ENO de rattachement de son groupe.

    partition : liste de groupes, chaque groupe est une liste d'apprenants (dict avec lat, lon, eno_id)
    enos : dict {eno_id: {'latitude': ..., 'longitude': ...}}
    """
    total_distance = 0.0
    total_apprenants = 0

    for groupe in partition:
        if not groupe:
            continue
        eno_id = groupe[0]['eno_rattachement_id']
        eno = enos[eno_id]
        for apprenant in groupe:
            dist = haversine(apprenant['latitude'], apprenant['longitude'],
                             eno['latitude'], eno['longitude'])
            total_distance += dist
            total_apprenants += 1

    return total_distance / total_apprenants if total_apprenants > 0 else 0.0


def calculer_p_eno(partition: list[list[dict]]) -> float:
    """
    Calcule P_ENO(S) : nombre d'apprenants dont l'ENO de rattachement du groupe
    ne correspond pas à leur ENO administratif.
    """
    total_hors_eno = 0
    total_apprenants = 0

    for groupe in partition:
        if not groupe:
            continue
        eno_rattachement = groupe[0]['eno_rattachement_id']
        for apprenant in groupe:
            if apprenant['eno_id'] != eno_rattachement:
                total_hors_eno += 1
            total_apprenants += 1

    return float(total_hors_eno)


def calculer_variance_territoriale(partition: list[list[dict]], enos: dict) -> float:
    """
    Calcule la variance des distances moyennes par ENO.
    Mesure l'équité territoriale : une variance faible = équité élevée.
    """
    distances_par_eno: dict[int, list[float]] = {}

    for groupe in partition:
        if not groupe:
            continue
        eno_id = groupe[0]['eno_rattachement_id']
        eno = enos[eno_id]
        if eno_id not in distances_par_eno:
            distances_par_eno[eno_id] = []
        for apprenant in groupe:
            dist = haversine(apprenant['latitude'], apprenant['longitude'],
                             eno['latitude'], eno['longitude'])
            distances_par_eno[eno_id].append(dist)

    moyennes = [np.mean(dists) for dists in distances_par_eno.values() if dists]
    return float(np.var(moyennes)) if len(moyennes) > 1 else 0.0


def calculer_metriques_groupe(groupe: list[dict], eno: dict) -> dict:
    """Calcule les métriques détaillées pour un groupe."""
    if not groupe:
        return {'dist_moy_km': 0.0, 'dist_max_km': 0.0, 'nb_hors_eno': 0}

    eno_rattachement_id = groupe[0]['eno_rattachement_id']
    distances = []
    nb_hors_eno = 0

    for apprenant in groupe:
        dist = haversine(apprenant['latitude'], apprenant['longitude'],
                         eno['latitude'], eno['longitude'])
        distances.append(dist)
        if apprenant['eno_id'] != eno_rattachement_id:
            nb_hors_eno += 1

    return {
        'dist_moy_km': float(np.mean(distances)),
        'dist_max_km': float(np.max(distances)),
        'nb_hors_eno': nb_hors_eno,
        'distances': distances,
    }
