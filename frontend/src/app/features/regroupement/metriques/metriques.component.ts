import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { MetriquesRegroupement } from '../../../core/models/models';

@Component({
  selector: 'app-metriques',
  imports: [CommonModule, RouterLink],
  templateUrl: './metriques.component.html',
  styleUrl: './metriques.component.css'
})
export class MetriquesComponent implements OnInit {
  metriques: MetriquesRegroupement | null = null;
  loading = true;
  regroupementId!: number;

  constructor(private api: ApiService, private route: ActivatedRoute) {}

  ngOnInit() {
    this.regroupementId = +this.route.snapshot.params['id'];
    this.api.getMetriques(this.regroupementId).subscribe({
      next: m => { this.metriques = m; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  get maxDistMoy(): number {
    return Math.max(...(this.metriques?.metriques_par_eno.map(e => e.dist_moy_km) || [1]));
  }

  getConvergencePoints(): string {
    if (!this.metriques?.historique_fitness.length) return '';
    const data = this.metriques.historique_fitness;
    const maxF = data[0].fitness;
    const minF = this.metriques.fitness_final;
    const range = maxF - minF || 1;
    return data.map((p, i) => {
      const x = (i / (data.length - 1)) * 800;
      const y = 200 - ((p.fitness - minF) / range) * 180;
      return `${x},${y}`;
    }).join(' ');
  }

  exportCSV() { this.api.exportCSV(this.regroupementId); }
  exportPDF() { this.api.exportPDF(this.regroupementId); }
}
