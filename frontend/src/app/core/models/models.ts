export interface Utilisateur {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  nom_complet: string;
  role: 'DFIP' | 'ENSEIGNANT' | 'COORDINATEUR' | 'APPRENANT';
  date_creation: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: Utilisateur;
}

export interface ENO {
  id: number;
  code: string;
  nom: string;
  region: string;
  ville: string;
  latitude: number;
  longitude: number;
  est_actif: boolean;
  nb_apprenants?: number;
}

export interface Specialite {
  id: number;
  code: string;
  nom: string;
  niveau: 'LICENCE' | 'MASTER';
  est_active: boolean;
}

export interface Cohorte {
  id: number;
  label: string;
  annee_academique: string;
  specialite: Specialite;
  statut: 'IMPORTEE' | 'PRETE' | 'EN_COURS' | 'REGROUPEE' | 'VALIDEE';
  nb_apprenants: number;
  date_creation: string;
  date_modification: string;
  cree_par_nom: string;
}

export interface Apprenant {
  id: number;
  ine: string;
  nom: string;
  prenom: string;
  email: string;
  nom_complet: string;
  latitude: number;
  longitude: number;
  eno: ENO;
  eno_id?: number;
  eno_nom?: string;
  eno_code?: string;
  cohorte: number;
  cohorte_label?: string;
  specialite: Specialite;
}

export interface MembreGroupe {
  id: number;
  apprenant: Apprenant;
  distance_eno_km: number;
  est_hors_eno: boolean;
  eno_administratif_nom: string;
}

export interface Groupe {
  id: number;
  numero: number;
  eno_rattachement?: ENO;
  eno_nom?: string;
  eno_region?: string;
  eno_latitude?: number;
  eno_longitude?: number;
  taille: number;
  dist_moy_km: number;
  dist_max_km: number;
  nb_hors_eno: number;
  membres?: MembreGroupe[];
  date_creation?: string;
}

export interface PointProgression {
  generation: number;
  fitness: number;
  d_geo: number;
  p_eno: number;
}

export interface Regroupement {
  id: number;
  cohorte: Cohorte;
  w1: number;
  w2: number;
  taille_min: number;
  taille_max: number;
  nb_generations: number;
  taille_population: number;
  seed: number;
  statut: 'EN_ATTENTE' | 'EN_COURS' | 'TERMINE' | 'VALIDE' | 'ERREUR';
  d_geo_final: number | null;
  p_eno_final: number | null;
  fitness_final: number | null;
  nb_groupes: number | null;
  nb_hors_eno: number | null;
  variance_territoriale: number | null;
  temps_execution_sec: number | null;
  message_erreur: string;
  progression_data: PointProgression[];
  date_creation: string;
  date_modification: string;
  lance_par_nom: string;
  groupes: Groupe[];
}

export interface MetriquesENO {
  eno_id: number;
  eno_nom: string;
  eno_region: string;
  nb_groupes: number;
  nb_apprenants: number;
  dist_moy_km: number;
  nb_hors_eno: number;
}

export interface MetriquesRegroupement {
  regroupement_id: number;
  cohorte: string;
  statut: string;
  d_geo_final: number;
  p_eno_final: number;
  fitness_final: number;
  variance_territoriale: number;
  nb_groupes: number;
  nb_hors_eno: number;
  temps_execution_sec: number;
  metriques_par_eno: MetriquesENO[];
  historique_fitness: PointProgression[];
}

export interface ImportCSVResult {
  succes: boolean;
  cohorte_id: number;
  cohorte_label: string;
  nb_apprenants: number;
  repartition_eno: Record<string, number>;
  enos_peu_peuples: string[];
  alertes: string[];
}

export interface ProgressionRegroupement {
  regroupement_id: number;
  statut: string;
  progression: PointProgression[];
  derniere_generation: PointProgression | null;
  d_geo_final: number | null;
  p_eno_final: number | null;
  fitness_final: number | null;
  temps_execution_sec: number | null;
  message_erreur: string;
}

export interface MonGroupe {
  groupe_id: number;
  groupe_numero: number;
  eno_rattachement: ENO;
  est_hors_eno: boolean;
  distance_eno_km: number;
  cohorte: string;
  membres: { nom: string; prenom: string; email: string; est_hors_eno: boolean }[];
}

export interface JournalAudit {
  id: number;
  utilisateur_nom: string;
  action: string;
  description: string;
  objet_type: string;
  objet_id: number;
  date: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
