import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ENO, Specialite, Cohorte, Apprenant, Regroupement,
  Groupe, MetriquesRegroupement, ImportCSVResult,
  ProgressionRegroupement, MonGroupe, JournalAudit, PaginatedResponse
} from '../models/models';

const API = 'http://localhost:8000/api';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  // ── ENO ──────────────────────────────────────────────────────────────────
  getENOs(cohorteId?: number): Observable<ENO[]> {
    let params = new HttpParams();
    if (cohorteId) params = params.set('cohorte_id', cohorteId);
    return this.http.get<ENO[]>(`${API}/enos/`, { params });
  }

  getENO(id: number): Observable<ENO> {
    return this.http.get<ENO>(`${API}/enos/${id}/`);
  }

  // ── SPÉCIALITÉS ──────────────────────────────────────────────────────────
  getSpecialites(niveau?: string): Observable<Specialite[]> {
    let params = new HttpParams();
    if (niveau) params = params.set('niveau', niveau);
    return this.http.get<Specialite[]>(`${API}/specialites/`, { params });
  }

  // ── COHORTES ─────────────────────────────────────────────────────────────
  getCohortes(statut?: string): Observable<PaginatedResponse<Cohorte>> {
    let params = new HttpParams();
    if (statut) params = params.set('statut', statut);
    return this.http.get<PaginatedResponse<Cohorte>>(`${API}/cohortes/`, { params });
  }

  getCohorte(id: number): Observable<Cohorte> {
    return this.http.get<Cohorte>(`${API}/cohortes/${id}/`);
  }

  // ── IMPORT CSV ───────────────────────────────────────────────────────────
  importCSV(formData: FormData): Observable<ImportCSVResult> {
    return this.http.post<ImportCSVResult>(`${API}/import-csv/`, formData);
  }

  genererDonnees(data: {
    nb_apprenants: number;
    specialite_id: number;
    label: string;
    annee_academique: string;
    seed?: number;
  }): Observable<any> {
    return this.http.post(`${API}/generer-donnees/`, data);
  }

  // ── APPRENANTS ───────────────────────────────────────────────────────────
  getApprenants(cohorteId?: number, enoId?: number): Observable<PaginatedResponse<Apprenant>> {
    let params = new HttpParams();
    if (cohorteId) params = params.set('cohorte_id', cohorteId);
    if (enoId) params = params.set('eno_id', enoId);
    return this.http.get<PaginatedResponse<Apprenant>>(`${API}/apprenants/`, { params });
  }

  getMonGroupe(): Observable<MonGroupe> {
    return this.http.get<MonGroupe>(`${API}/mon-groupe/`);
  }

  // ── REGROUPEMENTS ────────────────────────────────────────────────────────
  getRegroupements(cohorteId?: number): Observable<PaginatedResponse<Regroupement>> {
    let params = new HttpParams();
    if (cohorteId) params = params.set('cohorte_id', cohorteId);
    return this.http.get<PaginatedResponse<Regroupement>>(`${API}/regroupements/`, { params });
  }

  getRegroupement(id: number): Observable<Regroupement> {
    return this.http.get<Regroupement>(`${API}/regroupements/${id}/`);
  }

  lancerRegroupement(data: {
    cohorte: number;
    w1: number;
    w2: number;
    taille_min: number;
    taille_max: number;
    nb_generations: number;
    taille_population: number;
    seed: number;
  }): Observable<{ regroupement_id: number; statut: string; message: string }> {
    return this.http.post<any>(`${API}/regroupements/lancer/`, data);
  }

  getProgression(id: number): Observable<ProgressionRegroupement> {
    return this.http.get<ProgressionRegroupement>(`${API}/regroupements/${id}/progression/`);
  }

  validerRegroupement(id: number): Observable<any> {
    return this.http.post(`${API}/regroupements/${id}/valider/`, {});
  }

  getMetriques(id: number): Observable<MetriquesRegroupement> {
    return this.http.get<MetriquesRegroupement>(`${API}/regroupements/${id}/metriques/`);
  }

  exportCSV(id: number): void {
    window.open(`${API}/regroupements/${id}/export-csv/`, '_blank');
  }

  exportPDF(id: number): void {
    window.open(`${API}/regroupements/${id}/export-pdf/`, '_blank');
  }

  // ── GROUPES ──────────────────────────────────────────────────────────────
  getGroupes(regroupementId?: number, enoId?: number): Observable<PaginatedResponse<Groupe>> {
    let params = new HttpParams();
    if (regroupementId) params = params.set('regroupement_id', regroupementId);
    if (enoId) params = params.set('eno_id', enoId);
    return this.http.get<PaginatedResponse<Groupe>>(`${API}/groupes/`, { params });
  }

  getGroupe(id: number): Observable<Groupe> {
    return this.http.get<Groupe>(`${API}/groupes/${id}/`);
  }

  deplacerApprenant(regroupementId: number, apprenantId: number, groupeDestId: number): Observable<any> {
    return this.http.post(`${API}/regroupements/${regroupementId}/deplacer-apprenant/`, {
      apprenant_id: apprenantId,
      groupe_destination_id: groupeDestId,
    });
  }

  // ── JOURNAL ──────────────────────────────────────────────────────────────
  getJournal(): Observable<PaginatedResponse<JournalAudit>> {
    return this.http.get<PaginatedResponse<JournalAudit>>(`${API}/journal/`);
  }
}
