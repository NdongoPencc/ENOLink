import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { Specialite, ImportCSVResult } from '../../../core/models/models';

@Component({
  selector: 'app-import-csv',
  imports: [CommonModule, FormsModule],
  templateUrl: './import-csv.component.html',
  styleUrl: './import-csv.component.css'
})
export class ImportCsvComponent implements OnInit {
  specialites: Specialite[] = [];
  fichier: File | null = null;
  label = '';
  annee = '2025-2026';
  specialite_id: number | null = null;
  loading = false;
  resultat: ImportCSVResult | null = null;
  erreur = '';
  erreurs_csv: any[] = [];

  // Génération de données synthétiques
  modeDemo = false;
  nb_apprenants_demo = 150;
  seed_demo = 42;

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit() {
    this.api.getSpecialites().subscribe(res => this.specialites = res);
  }

  onFichierChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.fichier = input.files?.[0] ?? null;
    this.erreur = '';
  }

  importer() {
    if (!this.fichier || !this.label || !this.annee || !this.specialite_id) {
      this.erreur = 'Veuillez remplir tous les champs et sélectionner un fichier CSV.';
      return;
    }
    this.loading = true;
    this.erreur = '';
    this.erreurs_csv = [];
    this.resultat = null;

    const formData = new FormData();
    formData.append('fichier', this.fichier);
    formData.append('cohorte_label', this.label);
    formData.append('annee_academique', this.annee);
    formData.append('specialite_id', String(this.specialite_id));

    this.api.importCSV(formData).subscribe({
      next: res => {
        this.loading = false;
        this.resultat = res;
      },
      error: err => {
        this.loading = false;
        if (err.status === 422) {
          this.erreurs_csv = err.error.erreurs || [];
          this.erreur = `${err.error.nb_erreurs} erreur(s) détectée(s) dans le fichier.`;
        } else {
          this.erreur = err.error?.error || 'Erreur lors de l\'import.';
        }
      }
    });
  }

  genererDonnees() {
    if (!this.label || !this.annee || !this.specialite_id) {
      this.erreur = 'Veuillez remplir le label, l\'année et la spécialité.';
      return;
    }
    this.loading = true;
    this.erreur = '';
    this.api.genererDonnees({
      nb_apprenants: this.nb_apprenants_demo,
      specialite_id: this.specialite_id!,
      label: this.label,
      annee_academique: this.annee,
      seed: this.seed_demo,
    }).subscribe({
      next: res => {
        this.loading = false;
        this.resultat = { succes: true, cohorte_id: res.cohorte_id, cohorte_label: res.label,
          nb_apprenants: res.nb_apprenants, repartition_eno: {}, enos_peu_peuples: [], alertes: [] };
      },
      error: err => {
        this.loading = false;
        this.erreur = err.error?.error || 'Erreur lors de la génération.';
      }
    });
  }

  allerRegroupement() {
    if (this.resultat) {
      this.router.navigate(['/regroupements/configurer'], {
        queryParams: { cohorte_id: this.resultat.cohorte_id }
      });
    }
  }

  hasRepartition(): boolean {
    return !!this.resultat && Object.keys(this.resultat.repartition_eno).length > 0;
  }

  telechargerModele() {
    const contenu = 'ine;nom;prenom;email;latitude;longitude;eno_code\nUNCHK000001;Diallo;Moussa;moussa.diallo@unchk.edu.sn;14.6937;-17.4441;ENO-DKR\nUNCHK000002;Ba;Fatou;fatou.ba@unchk.edu.sn;14.7910;-16.9359;ENO-THI\n';
    const blob = new Blob(['\ufeff' + contenu], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'modele_import_enolink.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
}
