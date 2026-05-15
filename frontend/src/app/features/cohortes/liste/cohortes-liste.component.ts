import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { Cohorte } from '../../../core/models/models';

@Component({
  selector: 'app-cohortes-liste',
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './cohortes-liste.component.html',
  styleUrl: './cohortes-liste.component.css'
})
export class CohortesListeComponent implements OnInit {
  cohortes: Cohorte[] = [];
  loading = true;
  filtreStatut = '';

  constructor(public auth: AuthService, private api: ApiService) {}

  ngOnInit() { this.charger(); }

  charger() {
    this.loading = true;
    this.api.getCohortes(this.filtreStatut || undefined).subscribe({
      next: res => { this.cohortes = res.results; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  getStatutClass(statut: string): string {
    const map: Record<string, string> = {
      IMPORTEE: 'badge-importee', PRETE: 'badge-prete', EN_COURS: 'badge-en-cours',
      REGROUPEE: 'badge-regroupee', VALIDEE: 'badge-validee',
    };
    return map[statut] || 'badge-importee';
  }
}
