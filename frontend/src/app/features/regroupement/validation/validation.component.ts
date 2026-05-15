import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { Regroupement, Groupe } from '../../../core/models/models';

@Component({
  selector: 'app-validation',
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './validation.component.html',
  styleUrl: './validation.component.css'
})
export class ValidationComponent implements OnInit {
  regroupement: Regroupement | null = null;
  groupes: Groupe[] = [];
  loading = true;
  validating = false;
  regroupementId!: number;
  messageSucces = '';
  erreur = '';

  // Déplacement manuel
  apprenantSelectionne: number | null = null;
  groupeDestination: number | null = null;
  deplacement_loading = false;

  constructor(private api: ApiService, private route: ActivatedRoute, private router: Router) {}

  ngOnInit() {
    this.regroupementId = +this.route.snapshot.params['id'];
    this.charger();
  }

  charger() {
    this.api.getRegroupement(this.regroupementId).subscribe({
      next: reg => {
        this.regroupement = reg;
        this.chargerGroupes();
      }
    });
  }

  chargerGroupes() {
    this.api.getGroupes(this.regroupementId).subscribe({
      next: res => {
        // Charger les membres pour chaque groupe
        const ids = res.results.map(g => g.id);
        let loaded = 0;
        this.groupes = res.results;
        this.loading = false;
        res.results.forEach(g => {
          this.api.getGroupe(g.id).subscribe(gDetail => {
            const idx = this.groupes.findIndex(x => x.id === g.id);
            if (idx >= 0) this.groupes[idx] = gDetail;
          });
        });
      },
      error: () => { this.loading = false; }
    });
  }

  deplacerApprenant() {
    if (!this.apprenantSelectionne || !this.groupeDestination) return;
    this.deplacement_loading = true;
    this.erreur = '';

    this.api.deplacerApprenant(this.regroupementId, this.apprenantSelectionne, this.groupeDestination).subscribe({
      next: res => {
        this.deplacement_loading = false;
        this.messageSucces = 'Déplacement effectué. Métriques recalculées.';
        this.apprenantSelectionne = null;
        this.groupeDestination = null;
        this.chargerGroupes();
        setTimeout(() => this.messageSucces = '', 3000);
      },
      error: err => {
        this.deplacement_loading = false;
        this.erreur = err.error?.error || 'Erreur lors du déplacement.';
      }
    });
  }

  valider() {
    this.validating = true;
    this.api.validerRegroupement(this.regroupementId).subscribe({
      next: () => {
        this.validating = false;
        this.router.navigate(['/regroupements', this.regroupementId, 'metriques']);
      },
      error: err => {
        this.validating = false;
        this.erreur = err.error?.error || 'Erreur lors de la validation.';
      }
    });
  }
}
