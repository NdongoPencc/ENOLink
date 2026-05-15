import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap, catchError } from 'rxjs/operators';
import { Observable, throwError } from 'rxjs';
import { AuthResponse, Utilisateur } from '../models/models';

const API = 'http://localhost:8000/api/auth';

@Injectable({ providedIn: 'root' })
export class AuthService {
  utilisateur = signal<Utilisateur | null>(this._chargerUtilisateur());

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${API}/login/`, { email, password }).pipe(
      tap(res => {
        localStorage.setItem('access_token', res.access);
        localStorage.setItem('refresh_token', res.refresh);
        localStorage.setItem('utilisateur', JSON.stringify(res.user));
        this.utilisateur.set(res.user);
      }),
      catchError(err => throwError(() => err))
    );
  }

  logout(): void {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      this.http.post(`${API}/logout/`, { refresh }).subscribe();
    }
    localStorage.clear();
    this.utilisateur.set(null);
    this.router.navigate(['/login']);
  }

  refreshToken(): Observable<{ access: string }> {
    const refresh = localStorage.getItem('refresh_token');
    return this.http.post<{ access: string }>(`${API}/token/refresh/`, { refresh }).pipe(
      tap(res => localStorage.setItem('access_token', res.access))
    );
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  get role(): string {
    return this.utilisateur()?.role ?? '';
  }

  isDFIP(): boolean { return this.role === 'DFIP'; }
  isEnseignant(): boolean { return this.role === 'ENSEIGNANT'; }
  isCoordinateur(): boolean { return this.role === 'COORDINATEUR'; }
  isApprenant(): boolean { return this.role === 'APPRENANT'; }

  private _chargerUtilisateur(): Utilisateur | null {
    const data = localStorage.getItem('utilisateur');
    return data ? JSON.parse(data) : null;
  }
}
