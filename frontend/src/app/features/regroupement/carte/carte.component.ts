import { Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { Regroupement, Groupe, ProgressionRegroupement } from '../../../core/models/models';
import * as L from 'leaflet';

// Fix icônes Leaflet
const iconDefault = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
});
L.Marker.prototype.options.icon = iconDefault;

const COULEURS = [
  '#e53935','#8e24aa','#1e88e5','#00897b','#f4511e',
  '#6d4c41','#039be5','#43a047','#fb8c00','#d81b60',
  '#5e35b1','#00acc1','#7cb342','#fdd835','#3949ab',
  '#00897b','#c0ca33','#f06292',
];

@Component({
  selector: 'app-carte',
  imports: [CommonModule, RouterLink],
  templateUrl: './carte.component.html',
  styleUrl: './carte.component.css'
})
export class CarteComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('mapContainer') mapContainer!: ElementRef;

  regroupement: Regroupement | null = null;
  progression: ProgressionRegroupement | null = null;
  groupes: Groupe[] = [];
  groupeSelectionne: Groupe | null = null;
  loading = true;
  enCours = false;
  regroupementId!: number;

  private map!: L.Map;
  private markersLayer!: L.LayerGroup;
  private pollingInterval: any;
  private mapInitialise = false;

  constructor(
    private api: ApiService,
    public auth: AuthService,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.regroupementId = +this.route.snapshot.params['id'];
    this.charger();
  }

  ngAfterViewInit() {
    setTimeout(() => this.initCarte(), 100);
  }

  ngOnDestroy() {
    if (this.pollingInterval) clearInterval(this.pollingInterval);
    if (this.map) this.map.remove();
  }

  charger() {
    this.api.getRegroupement(this.regroupementId).subscribe({
      next: reg => {
        this.regroupement = reg;
        this.groupes = reg.groupes || [];
        this.loading = false;

        if (reg.statut === 'EN_COURS' || reg.statut === 'EN_ATTENTE') {
          this.enCours = true;
          this.demarrerPolling();
        } else if (reg.statut === 'TERMINE' || reg.statut === 'VALIDE') {
          this.chargerGroupesDetailles();
        }
      },
      error: () => { this.loading = false; }
    });
  }

  chargerGroupesDetailles() {
    this.api.getGroupes(this.regroupementId).subscribe(res => {
      this.groupes = res.results;
      if (this.mapInitialise) this.afficherGroupesSurCarte();
    });
  }

  demarrerPolling() {
    this.pollingInterval = setInterval(() => {
      this.api.getProgression(this.regroupementId).subscribe(prog => {
        this.progression = prog;
        if (prog.statut === 'TERMINE' || prog.statut === 'VALIDE') {
          clearInterval(this.pollingInterval);
          this.enCours = false;
          this.charger();
        } else if (prog.statut === 'ERREUR') {
          clearInterval(this.pollingInterval);
          this.enCours = false;
        }
      });
    }, 2000);
  }

  initCarte() {
    if (!this.mapContainer?.nativeElement || this.mapInitialise) return;

    this.map = L.map(this.mapContainer.nativeElement, {
      center: [14.5, -14.5],
      zoom: 6,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(this.map);

    this.markersLayer = L.layerGroup().addTo(this.map);
    this.mapInitialise = true;

    if (this.groupes.length > 0) this.afficherGroupesSurCarte();
  }

  afficherGroupesSurCarte() {
    if (!this.map || !this.markersLayer) return;
    this.markersLayer.clearLayers();

    this.groupes.forEach((groupe, idx) => {
      const couleur = COULEURS[idx % COULEURS.length];
      const enoLat = groupe.eno_latitude;
      const enoLon = groupe.eno_longitude;

      if (!enoLat || !enoLon) return;

      // Marqueur ENO
      const enoIcon = L.divIcon({
        html: `<div class="eno-marker" style="background:${couleur}">
                 <span>${groupe.numero}</span>
               </div>`,
        className: '',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
      });

      L.marker([enoLat, enoLon], { icon: enoIcon })
        .bindPopup(`
          <div class="popup-eno">
            <strong>Groupe ${groupe.numero}</strong><br>
            ENO : ${groupe.eno_nom}<br>
            Région : ${groupe.eno_region}<br>
            Apprenants : ${groupe.taille}<br>
            Distance moy. : ${groupe.dist_moy_km?.toFixed(2)} km<br>
            Hors ENO : ${groupe.nb_hors_eno}
          </div>
        `)
        .addTo(this.markersLayer);
    });

    // Afficher les membres si un groupe est sélectionné
    if (this.groupeSelectionne) {
      this.afficherMembresGroupe(this.groupeSelectionne);
    }
  }

  afficherMembresGroupe(groupe: Groupe) {
    if (!groupe.membres) {
      this.api.getGroupe(groupe.id).subscribe(g => {
        this.groupeSelectionne = g;
        this._dessinerMembres(g);
      });
    } else {
      this._dessinerMembres(groupe);
    }
  }

  private _dessinerMembres(groupe: Groupe) {
    if (!groupe.membres) return;
    const idx = this.groupes.findIndex(g => g.id === groupe.id);
    const couleur = COULEURS[idx % COULEURS.length];

    groupe.membres.forEach(m => {
      const appIcon = L.circleMarker(
        [m.apprenant.latitude, m.apprenant.longitude],
        {
          radius: 6,
          fillColor: m.est_hors_eno ? '#ff9800' : couleur,
          color: m.est_hors_eno ? '#e65100' : couleur,
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8,
        }
      ).bindPopup(`
        <strong>${m.apprenant.prenom} ${m.apprenant.nom}</strong><br>
        INE : ${m.apprenant.ine}<br>
        ENO admin. : ${m.apprenant.eno_nom}<br>
        Distance ENO : ${m.distance_eno_km?.toFixed(2)} km<br>
        ${m.est_hors_eno ? '<span style="color:#e65100">⚠️ Hors ENO administratif</span>' : ''}
      `);
      appIcon.addTo(this.markersLayer);

      // Ligne entre apprenant et ENO
      if (groupe.eno_latitude && groupe.eno_longitude) {
        L.polyline(
          [[m.apprenant.latitude, m.apprenant.longitude], [groupe.eno_latitude!, groupe.eno_longitude!]],
          { color: couleur, weight: 1, opacity: 0.4, dashArray: '4,4' }
        ).addTo(this.markersLayer);
      }
    });
  }

  selectionnerGroupe(groupe: Groupe) {
    this.groupeSelectionne = groupe;
    this.afficherGroupesSurCarte();
    this.afficherMembresGroupe(groupe);

    if (groupe.eno_latitude && groupe.eno_longitude) {
      this.map.setView([groupe.eno_latitude, groupe.eno_longitude], 9);
    }
  }

  get pourcentageProgression(): number {
    if (!this.progression?.progression?.length || !this.regroupement) return 0;
    return Math.round((this.progression.progression.length / this.regroupement.nb_generations) * 100);
  }

  exportCSV() { this.api.exportCSV(this.regroupementId); }
  exportPDF() { this.api.exportPDF(this.regroupementId); }
}
