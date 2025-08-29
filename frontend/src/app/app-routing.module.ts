import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { EndpointListComponent } from './components/endpoint-list/endpoint-list.component';
import { AlertDetailComponent } from './components/alert-detail/alert-detail.component';

import { LiveDeviceStatusComponent } from './live-device-status/live-device-status.component';

const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'endpoints', component: EndpointListComponent },
  { path: 'alert/:id', component: AlertDetailComponent },
  { path: 'live-device-status', component: LiveDeviceStatusComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
