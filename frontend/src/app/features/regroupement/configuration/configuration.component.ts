import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { Cohorte, ENO } from '../../../core/models/models';

@Component({
  selector: 'app-configuration',
  imports: [CommonModule, FormsModule],
  templateUrl: './configuration.component.html',
  styleUrl: './configuration.component.css'
})
export class ConfigurationComponent implements OnInit {
  cohortes: Cohorte[] = [];
  enos: ENO[] = [];
  cohorteSelectionnee: Cohorte | null = null;

  params = {
    cohorte: 0,
    w1: 0.7,
    w2: 0.3,
    taille_min: 3,
    taille_max: 6,
    nb_generations: 200,
    taille_population: 100,
    seed: 42,
  };

  loading = false;
  erreur = '';
  lance = false;
  regroupementId: number | null = null;

  constructor(private api: ApiService, private router: Router, private route: ActivatedRoute) {}

  ngOnInit() {
    this.api.getCohortes().subscribe(res => {
      this.cohortes = res.results.filter(c => c.statut === 'PRETE' || c.statut === 'REGROUPEE');
    });

    this.route.queryParams.subscribe(p => {
      if (p['cohorte_id']) {
        this.params.cohorte = +p['cohorte_id'];
        this.onCohorteChange();
      }
    });
  }

  onCohorteChange() {
    if (!this.params.cohorte) return;
    this.cohorteSelectionnee = this.cohortes.find(c => c.id === +this.params.cohorte) || null;
    this.api.getENOs(this.params.cohorte).subscribe(res => this.enos = res);
  }

  onW1Change() {
    this.params.w2 = Math.round((1 - this.params.w1) * 100) / 100;
  }

  onW2Change() {
    this.params.w1 = Math.round((1 - this.params.w2) * 100) / 100;
  }

  lancer() {
    if (!this.params.cohorte) { this.erreur = 'Sélectionnez une cohorte.'; return; }
    if (Math.abs(this.params.w1 + this.params.w2 - 1) > 0.001) {
      this.erreur = 'w₁ + w₂ doit être égal à 1.'; return;
    }
    this.loading = true;
    this.erreur = '';

    this.api.lancerRegroupement(this.params).subscribe({
      next: res => {
        this.loading = false;
        this.lance = true;
        this.regroupementId = res.regroupement_id;
      },
      error: err => {
        this.loading = false;
        this.erreur = err.error?.error || 'Erreur lors du lancement.';
      }
    });
  }

  voirCarte() {
    if (this.regroupementId) {
      this.router.navigate(['/regroupements', this.regroupementId, 'carte']);
    }
  }
}
