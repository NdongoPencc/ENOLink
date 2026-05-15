import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { NgIcon } from '@ng-icons/core';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule, NgIcon],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  menuOuvert = false;
  constructor(public auth: AuthService) {}
  toggleMenu() { this.menuOuvert = !this.menuOuvert; }
  fermerMenu() { this.menuOuvert = false; }
}
