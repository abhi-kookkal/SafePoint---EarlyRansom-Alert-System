import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Endpoint {
  id: number;
  hostname: string;
  ip: string;
  status: string;
}

@Injectable({ providedIn: 'root' })
export class EndpointService {
  private apiUrl = 'http://localhost:8000/fetch_endpoints';

  constructor(private http: HttpClient) {}

  getEndpoints(): Observable<Endpoint[]> {
    return this.http.get<Endpoint[]>(this.apiUrl);
  }
}
