import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { Cohorte, Regroupement } from '../../core/models/models';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, RouterLink, NgIcon],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  cohortes: Cohorte[] = [];
  regroupements: Regroupement[] = [];
  loading = true;

  stats = { total_cohortes: 0, total_apprenants: 0, total_groupes: 0, cohortes_validees: 0 };

  constructor(public auth: AuthService, private api: ApiService) {}

  ngOnInit() {
    this.api.getCohortes().subscribe({
      next: res => {
        this.cohortes = res.results.slice(0, 5);
        this.stats.total_cohortes = res.count;
        this.stats.total_apprenants = res.results.reduce((s, c) => s + c.nb_apprenants, 0);
        this.stats.cohortes_validees = res.results.filter(c => c.statut === 'VALIDEE').length;
      }
    });

    this.api.getRegroupements().subscribe({
      next: res => {
        this.regroupements = res.results.slice(0, 5);
        this.stats.total_groupes = res.results.reduce((s, r) => s + (r.nb_groupes || 0), 0);
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }

  getStatutClass(statut: string): string {
    const map: Record<string, string> = {
      IMPORTEE: 'badge-importee', PRETE: 'badge-prete', EN_COURS: 'badge-en-cours',
      REGROUPEE: 'badge-regroupee', VALIDEE: 'badge-validee',
      TERMINE: 'badge-termine', VALIDE: 'badge-validee', ERREUR: 'badge-erreur',
    };
    return map[statut] || 'badge-importee';
  }
}
