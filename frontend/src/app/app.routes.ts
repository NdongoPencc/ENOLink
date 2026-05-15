import { Routes } from '@angular/router';
import { authGuard, dfipGuard, apprenantGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'cohortes',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/cohortes/liste/cohortes-liste.component').then(m => m.CohortesListeComponent)
      },
      {
        path: 'import',
        canActivate: [dfipGuard],
        loadComponent: () => import('./features/cohortes/import/import-csv.component').then(m => m.ImportCsvComponent)
      },
    ]
  },
  {
    path: 'regroupements',
    canActivate: [authGuard],
    children: [
      {
        path: 'configurer',
        canActivate: [dfipGuard],
        loadComponent: () => import('./features/regroupement/configuration/configuration.component').then(m => m.ConfigurationComponent)
      },
      {
        path: ':id/carte',
        loadComponent: () => import('./features/regroupement/carte/carte.component').then(m => m.CarteComponent)
      },
      {
        path: ':id/metriques',
        loadComponent: () => import('./features/regroupement/metriques/metriques.component').then(m => m.MetriquesComponent)
      },
      {
        path: ':id/validation',
        canActivate: [dfipGuard],
        loadComponent: () => import('./features/regroupement/validation/validation.component').then(m => m.ValidationComponent)
      },
    ]
  },
  {
    path: 'mon-groupe',
    canActivate: [authGuard],
    loadComponent: () => import('./features/apprenants/mon-groupe/mon-groupe.component').then(m => m.MonGroupeComponent)
  },
  { path: '**', redirectTo: '/dashboard' }
];
