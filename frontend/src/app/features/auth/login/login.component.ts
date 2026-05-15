import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  imports: [CommonModule, FormsModule, NgIcon],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  email = '';
  password = '';
  loading = false;
  erreur = '';

  constructor(private auth: AuthService, private router: Router) {
    if (this.auth.isAuthenticated()) this.router.navigate(['/dashboard']);
  }

  login() {
    if (!this.email || !this.password) {
      this.erreur = 'Veuillez remplir tous les champs.';
      return;
    }
    this.loading = true;
    this.erreur = '';
    this.auth.login(this.email, this.password).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err: any) => {
        this.loading = false;
        this.erreur = err.error?.detail || 'Email ou mot de passe incorrect.';
      }
    });
  }
}
