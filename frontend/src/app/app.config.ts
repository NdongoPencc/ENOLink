import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { provideIcons } from '@ng-icons/core';
import {
  lucideLayoutDashboard, lucideUsers, lucideUpload, lucideSettings,
  lucideMap, lucideBarChart2, lucideLogOut, lucideMenu, lucideMapPin,
  lucideDna, lucideLineChart, lucideFileDown, lucideCheckCircle,
  lucideAlertTriangle, lucideInfo, lucideChevronRight, lucideRefreshCw,
  lucideDownload, lucideEye, lucideTrash2, lucideEdit, lucidePlusCircle,
  lucideSearch, lucideFilter, lucideHome, lucideBookOpen,
  lucideGraduationCap, lucideBuilding2, lucideGlobe, lucideClock,
  lucideTrendingUp, lucideShield, lucideFileText, lucideLayers,
  lucidePlay, lucideCheck, lucideX, lucideArrowRight, lucideUser,
  lucideFileSpreadsheet, lucideActivity, lucideTarget, lucideZap,
  lucideChevronDown, lucideExternalLink, lucideSave
} from '@ng-icons/lucide';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideIcons({
      lucideLayoutDashboard, lucideUsers, lucideUpload, lucideSettings,
      lucideMap, lucideBarChart2, lucideLogOut, lucideMenu, lucideMapPin,
      lucideDna, lucideLineChart, lucideFileDown, lucideCheckCircle,
      lucideAlertTriangle, lucideInfo, lucideChevronRight, lucideRefreshCw,
      lucideDownload, lucideEye, lucideTrash2, lucideEdit, lucidePlusCircle,
      lucideSearch, lucideFilter, lucideHome, lucideBookOpen,
      lucideGraduationCap, lucideBuilding2, lucideGlobe, lucideClock,
      lucideTrendingUp, lucideShield, lucideFileText, lucideLayers,
      lucidePlay, lucideCheck, lucideX, lucideArrowRight, lucideUser,
      lucideFileSpreadsheet, lucideActivity, lucideTarget, lucideZap,
      lucideChevronDown, lucideExternalLink, lucideSave
    }),
  ]
};
