import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AlertService, Alert } from '../../services/alert.service';

@Component({
  selector: 'app-alert-detail',
  templateUrl: './alert-detail.component.html',
  styleUrls: ['./alert-detail.component.scss']
})
export class AlertDetailComponent implements OnInit {
  alert?: Alert;
  message = '';

  constructor(
    private route: ActivatedRoute,
    private alertService: AlertService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.alertService.getAlertById(id).subscribe((data) => (this.alert = data));
  }

  killProcess(): void {
    if (!this.alert) return;
    console.log("kill process", this.alert)
    this.alertService.killProcess(this.alert.id).subscribe(() => {
      this.message = '🛑 Process killed successfully';
    });
  }

  isolateDevice(): void {
    if (!this.alert) return;
    this.alertService.isolateDevice(this.alert.id).subscribe(() => {
      this.message = '🔒 Device isolated successfully';
    });
  }

  markNonIssue(): void {
    if (!this.alert) return;
    // For mock/demo, update status locally
    this.alert.status = 'non-issue';
    this.message = '✅ Marked as non-issue. This alert will not be shown as a threat.';
    // In a real app, you would call a backend endpoint here
  }
}

