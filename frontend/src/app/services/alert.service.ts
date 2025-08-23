import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Alert {
  id: string;
  file: string;
  process: string;
  user: string;
  timestamp: string;
  status: string;
  riskLevel: 'low' | 'medium' | 'high';
  device_id:string;
  device_risk_score: number;
} 


@Injectable({ providedIn: 'root' })
export class AlertService {
  private apiUrl = 'http://localhost:8000/fetch_alerts';

  constructor(private http: HttpClient) {}

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(this.apiUrl);
  }

  getAlertById(id: number): Observable<Alert> {
    return this.http.get<Alert>(`${this.apiUrl}/${id}`);
  }

  killProcess(id: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${id}/kill_process`, {});
  }
  
  isolateDevice(id: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/${id}/isolate`, {});
  }
}
