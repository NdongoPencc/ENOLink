import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { MonGroupe } from '../../../core/models/models';
import * as L from 'leaflet';

@Component({
  selector: 'app-mon-groupe',
  imports: [CommonModule],
  templateUrl: './mon-groupe.component.html',
  styleUrl: './mon-groupe.component.css'
})
export class MonGroupeComponent implements OnInit, AfterViewInit {
  @ViewChild('mapContainer') mapContainer!: ElementRef;
  groupe: MonGroupe | null = null;
  loading = true;
  erreur = '';
  private map!: L.Map;

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() {
    this.api.getMonGroupe().subscribe({
      next: g => { this.groupe = g; this.loading = false; },
      error: err => {
        this.loading = false;
        this.erreur = err.error?.error || 'Impossible de charger votre groupe.';
      }
    });
  }

  ngAfterViewInit() {
    setTimeout(() => this.initCarte(), 300);
  }

  initCarte() {
    if (!this.mapContainer?.nativeElement || !this.groupe) return;

    this.map = L.map(this.mapContainer.nativeElement, {
      center: [this.groupe.eno_rattachement.latitude, this.groupe.eno_rattachement.longitude],
      zoom: 8,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap'
    }).addTo(this.map);

    // Marqueur ENO
    L.marker([this.groupe.eno_rattachement.latitude, this.groupe.eno_rattachement.longitude])
      .bindPopup(`<strong>${this.groupe.eno_rattachement.nom}</strong><br>${this.groupe.eno_rattachement.region}`)
      .addTo(this.map)
      .openPopup();
  }
}
