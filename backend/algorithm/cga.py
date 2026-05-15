"""
Algorithme Génétique Cyclique (CGA) pour ENOLink.
Optimise f(S) = w1 * D_geo(S) + w2 * P_ENO(S)

Structure du chromosome : liste d'entiers représentant l'affectation de chaque
apprenant à un groupe. Le chromosome est cyclique : les groupes gravitent
autour d'un ENO fixe.
"""
import random
import time
import numpy as np
from typing import Callable

from .geo import (
    haversine,
    calculer_d_geo,
    calculer_p_eno,
    calculer_variance_territoriale,
    calculer_metriques_groupe,
)


class CGA:
    """
    Algorithme Génétique Cyclique pour le regroupement d'apprenants.

    Paramètres
    ----------
    apprenants : list[dict]
        Chaque dict contient : id, latitude, longitude, eno_id, nom, prenom, ine, email
    enos : dict
        {eno_id: {'id', 'nom', 'latitude', 'longitude', 'region'}}
    w1 : float
        Poids géographique (distance GPS)
    w2 : float
        Poids institutionnel (cohérence ENO)
    taille_min : int
        Taille minimale d'un groupe
    taille_max : int
        Taille maximale d'un groupe
    nb_generations : int
        Nombre de générations
    taille_population : int
        Taille de la population
    seed : int
        Graine aléatoire pour la reproductibilité
    callback_progression : Callable
        Fonction appelée à chaque génération avec les données de progression
    """

    def __init__(
        self,
        apprenants: list[dict],
        enos: dict,
        w1: float = 0.7,
        w2: float = 0.3,
        taille_min: int = 3,
        taille_max: int = 6,
        nb_generations: int = 200,
        taille_population: int = 100,
        seed: int = 42,
        callback_progression: Callable = None,
    ):
        self.apprenants = apprenants
        self.enos = enos
        self.w1 = w1
        self.w2 = w2
        self.taille_min = taille_min
        self.taille_max = taille_max
        self.nb_generations = nb_generations
        self.taille_population = taille_population
        self.seed = seed
        self.callback_progression = callback_progression

        random.seed(seed)
        np.random.seed(seed)

        self.n = len(apprenants)
        self._preparer_donnees()

    def _preparer_donnees(self):
        """Prépare les structures de données optimisées."""
        # Grouper les apprenants par ENO
        self.apprenants_par_eno: dict[int, list[int]] = {}
        for i, app in enumerate(self.apprenants):
            eno_id = app['eno_id']
            if eno_id not in self.apprenants_par_eno:
                self.apprenants_par_eno[eno_id] = []
            self.apprenants_par_eno[eno_id].append(i)

        # Identifier les ENO peu peuplés
        self.enos_peu_peuples: set[int] = set()
        self.apprenants_hors_eno: list[int] = []  # indices des apprenants à réaffecter

        for eno_id, indices in self.apprenants_par_eno.items():
            if len(indices) < self.taille_min:
                self.enos_peu_peuples.add(eno_id)
                self.apprenants_hors_eno.extend(indices)

        # ENO avec assez d'apprenants
        self.enos_actifs = {
            eno_id: indices
            for eno_id, indices in self.apprenants_par_eno.items()
            if eno_id not in self.enos_peu_peuples
        }

        # Calculer le nombre de groupes par ENO
        self.groupes_par_eno: dict[int, int] = {}
        for eno_id, indices in self.enos_actifs.items():
            nb = len(indices)
            nb_groupes = max(1, round(nb / ((self.taille_min + self.taille_max) / 2)))
            self.groupes_par_eno[eno_id] = nb_groupes

        self.nb_groupes_total = sum(self.groupes_par_eno.values())

    def _rattacher_hors_eno(self, chromosome: list[int]) -> list[int]:
        """
        Rattache les apprenants des ENO peu peuplés au groupe géographiquement
        le plus proche (contrainte C2 — cas exceptionnel).
        """
        if not self.apprenants_hors_eno:
            return chromosome

        # Construire la partition actuelle pour trouver les centroïdes
        partition = self._decoder_chromosome(chromosome)

        for idx_app in self.apprenants_hors_eno:
            app = self.apprenants[idx_app]
            meilleur_groupe = None
            meilleure_distance = float('inf')

            for g_idx, groupe in enumerate(partition):
                if not groupe:
                    continue
                eno_id = groupe[0]['eno_rattachement_id']
                eno = self.enos[eno_id]
                dist = haversine(app['latitude'], app['longitude'],
                                 eno['latitude'], eno['longitude'])
                if dist < meilleure_distance:
                    meilleure_distance = dist
                    meilleur_groupe = g_idx

            if meilleur_groupe is not None:
                chromosome[idx_app] = meilleur_groupe

        return chromosome

    def _creer_chromosome_initial(self) -> list[int]:
        """
        Crée un chromosome initial en respectant les contraintes ENO.
        Chaque apprenant est assigné à un groupe de son ENO.
        """
        chromosome = [-1] * self.n
        groupe_offset = 0

        for eno_id, indices in self.enos_actifs.items():
            nb_groupes = self.groupes_par_eno[eno_id]
            indices_melanges = indices.copy()
            random.shuffle(indices_melanges)

            # Distribuer équitablement dans les groupes de cet ENO
            for i, idx_app in enumerate(indices_melanges):
                groupe_local = i % nb_groupes
                chromosome[idx_app] = groupe_offset + groupe_local

            groupe_offset += nb_groupes

        # Rattacher les apprenants hors ENO
        chromosome = self._rattacher_hors_eno(chromosome)
        return chromosome

    def _decoder_chromosome(self, chromosome: list[int]) -> list[list[dict]]:
        """Convertit un chromosome en partition (liste de groupes)."""
        partition: list[list[dict]] = [[] for _ in range(self.nb_groupes_total)]

        # Déterminer l'ENO de rattachement de chaque groupe
        eno_par_groupe: dict[int, int] = {}
        groupe_offset = 0
        for eno_id, nb_groupes in self.groupes_par_eno.items():
            for g in range(nb_groupes):
                eno_par_groupe[groupe_offset + g] = eno_id
            groupe_offset += nb_groupes

        for idx_app, groupe_idx in enumerate(chromosome):
            if groupe_idx < 0 or groupe_idx >= self.nb_groupes_total:
                continue
            app = self.apprenants[idx_app].copy()
            app['eno_rattachement_id'] = eno_par_groupe.get(groupe_idx, app['eno_id'])
            partition[groupe_idx].append(app)

        return partition

    def _fitness(self, chromosome: list[int]) -> tuple[float]:
        """
        Calcule f(S) = w1 * D_geo(S) + w2 * P_ENO(S)
        Retourne un tuple (valeur,) pour compatibilité DEAP.
        """
        partition = self._decoder_chromosome(chromosome)

        # Pénalité pour groupes trop petits ou trop grands
        penalite_taille = 0.0
        for groupe in partition:
            taille = len(groupe)
            if taille > 0 and taille < self.taille_min:
                penalite_taille += (self.taille_min - taille) * 50
            elif taille > self.taille_max:
                penalite_taille += (taille - self.taille_max) * 50

        d_geo = calculer_d_geo(partition, self.enos)
        p_eno = calculer_p_eno(partition)

        fitness = self.w1 * d_geo + self.w2 * p_eno + penalite_taille
        return (fitness,)

    def _croisement_cyclique(self, parent1: list[int], parent2: list[int]) -> tuple[list[int], list[int]]:
        """
        Croisement cyclique (CX) : préserve la structure des groupes ENO.
        """
        n = len(parent1)
        enfant1 = [-1] * n
        enfant2 = [-1] * n

        # Cycle 1 : de parent1
        visited = [False] * n
        i = 0
        while not visited[i]:
            visited[i] = True
            enfant1[i] = parent1[i]
            enfant2[i] = parent2[i]
            # Trouver la position de parent2[i] dans parent1
            val = parent2[i]
            positions = [j for j, v in enumerate(parent1) if v == val and not visited[j]]
            if not positions:
                break
            i = positions[0]

        # Remplir le reste avec l'autre parent
        for j in range(n):
            if not visited[j]:
                enfant1[j] = parent2[j]
                enfant2[j] = parent1[j]

        return enfant1, enfant2

    def _mutation(self, chromosome: list[int], taux: float = 0.02) -> list[int]:
        """
        Mutation : échange aléatoire de deux apprenants entre groupes du même ENO.
        Préserve la contrainte ENO autant que possible.
        """
        mutant = chromosome.copy()

        for _ in range(max(1, int(self.n * taux))):
            # Choisir un ENO actif aléatoire
            if not self.enos_actifs:
                break
            eno_id = random.choice(list(self.enos_actifs.keys()))
            indices = self.enos_actifs[eno_id]
            if len(indices) < 2:
                continue
            i, j = random.sample(indices, 2)
            mutant[i], mutant[j] = mutant[j], mutant[i]

        return mutant

    def _selection_tournoi(self, population: list[list[int]], fitnesses: list[float], k: int = 3) -> list[int]:
        """Sélection par tournoi de taille k."""
        candidats = random.sample(range(len(population)), min(k, len(population)))
        meilleur = min(candidats, key=lambda i: fitnesses[i])
        return population[meilleur].copy()

    def executer(self) -> dict:
        """
        Exécute l'algorithme CGA et retourne les résultats complets.
        """
        debut = time.time()

        if self.n == 0:
            return {'erreur': 'Aucun apprenant dans la cohorte.'}

        if self.nb_groupes_total == 0:
            return {'erreur': 'Impossible de former des groupes avec les paramètres donnés.'}

        # Initialiser la population
        population = [self._creer_chromosome_initial() for _ in range(self.taille_population)]
        fitnesses = [self._fitness(c)[0] for c in population]

        meilleur_chromosome = population[np.argmin(fitnesses)].copy()
        meilleure_fitness = min(fitnesses)

        historique = []

        for generation in range(self.nb_generations):
            nouvelle_population = []

            # Élitisme : garder le meilleur
            nouvelle_population.append(meilleur_chromosome.copy())

            # Générer le reste de la population
            while len(nouvelle_population) < self.taille_population:
                parent1 = self._selection_tournoi(population, fitnesses)
                parent2 = self._selection_tournoi(population, fitnesses)

                # Croisement (probabilité 0.8)
                if random.random() < 0.8:
                    enfant1, enfant2 = self._croisement_cyclique(parent1, parent2)
                else:
                    enfant1, enfant2 = parent1.copy(), parent2.copy()

                # Mutation (probabilité 0.15)
                if random.random() < 0.15:
                    enfant1 = self._mutation(enfant1)
                if random.random() < 0.15:
                    enfant2 = self._mutation(enfant2)

                nouvelle_population.extend([enfant1, enfant2])

            population = nouvelle_population[:self.taille_population]
            fitnesses = [self._fitness(c)[0] for c in population]

            idx_meilleur = np.argmin(fitnesses)
            if fitnesses[idx_meilleur] < meilleure_fitness:
                meilleure_fitness = fitnesses[idx_meilleur]
                meilleur_chromosome = population[idx_meilleur].copy()

            # Calculer les métriques de la génération courante
            partition_courante = self._decoder_chromosome(meilleur_chromosome)
            d_geo_courant = calculer_d_geo(partition_courante, self.enos)
            p_eno_courant = calculer_p_eno(partition_courante)

            point_progression = {
                'generation': generation + 1,
                'fitness': round(meilleure_fitness, 4),
                'd_geo': round(d_geo_courant, 4),
                'p_eno': round(p_eno_courant, 4),
            }
            historique.append(point_progression)

            # Callback pour le suivi temps réel
            if self.callback_progression:
                self.callback_progression(point_progression)

        # Construire les résultats finaux
        partition_finale = self._decoder_chromosome(meilleur_chromosome)
        d_geo_final = calculer_d_geo(partition_finale, self.enos)
        p_eno_final = calculer_p_eno(partition_finale)
        variance = calculer_variance_territoriale(partition_finale, self.enos)
        temps = time.time() - debut

        # Construire les groupes détaillés
        groupes_details = []
        groupe_offset = 0
        for eno_id, nb_groupes in self.groupes_par_eno.items():
            eno = self.enos[eno_id]
            for g in range(nb_groupes):
                idx_groupe = groupe_offset + g
                groupe = partition_finale[idx_groupe]
                metriques = calculer_metriques_groupe(groupe, eno)
                groupes_details.append({
                    'numero': idx_groupe + 1,
                    'eno_id': eno_id,
                    'eno_nom': eno['nom'],
                    'membres': groupe,
                    'dist_moy_km': metriques['dist_moy_km'],
                    'dist_max_km': metriques['dist_max_km'],
                    'nb_hors_eno': metriques['nb_hors_eno'],
                    'taille': len(groupe),
                })
            groupe_offset += nb_groupes

        return {
            'succes': True,
            'fitness_final': round(meilleure_fitness, 6),
            'd_geo_final': round(d_geo_final, 4),
            'p_eno_final': round(p_eno_final, 4),
            'variance_territoriale': round(variance, 4),
            'nb_groupes': self.nb_groupes_total,
            'nb_hors_eno': int(p_eno_final),
            'enos_peu_peuples': list(self.enos_peu_peuples),
            'temps_execution_sec': round(temps, 2),
            'groupes': groupes_details,
            'historique_fitness': historique,
        }
