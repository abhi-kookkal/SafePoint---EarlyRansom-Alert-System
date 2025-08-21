import { Component, OnInit } from '@angular/core';
import { AlertService, Alert } from '../../services/alert.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  alerts: Alert[] = [];
  loading = true;

  constructor(private alertService: AlertService) {}

  ngOnInit(): void {
    this.loadAlerts();
  }

  loadAlerts(): void {
    this.alertService.getAlerts().subscribe({
      next: (data) => {
        this.alerts = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }
}
