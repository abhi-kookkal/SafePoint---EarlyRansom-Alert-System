import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpResponse
} from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

@Injectable()
export class MockInterceptor implements HttpInterceptor {
    private alerts = [
        {
          id: 1,
          file: 'C:/Users/Public/Documents/finance.xlsx',
          process: 'encryptor.exe',
          user: 'john',
          timestamp: '2025-08-21 14:22:10',
          status: 'Active',
          riskLevel: 'high'
        },
        {
          id: 2,
          file: 'C:/Projects/codebase/config.json',
          process: 'suspicious.exe',
          user: 'alice',
          timestamp: '2025-08-21 14:30:45',
          status: 'Active',
          riskLevel: 'medium'
        },
        {
          id: 3,
          file: 'C:/Users/Public/Desktop/notes.txt',
          process: 'notepad.exe',
          user: 'bob',
          timestamp: '2025-08-21 14:35:00',
          status: 'Resolved',
          riskLevel: 'low'
        }
      ];
      

  private endpoints = [
    { id: 1, hostname: 'WORKSTATION-01', ip: '192.168.1.10', status: 'online' },
    { id: 2, hostname: 'SERVER-DB', ip: '192.168.1.15', status: 'isolated' },
    { id: 3, hostname: 'LAPTOP-ALICE', ip: '192.168.1.20', status: 'online' }
  ];

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const { url, method } = req;

    // Mock alerts list
    if (url.endsWith('/alerts') && method === 'GET') {
      return of(new HttpResponse({ status: 200, body: this.alerts })).pipe(delay(500));
    }

    // Mock get alert by ID
    if (url.match(/\/alerts\/\d+$/) && method === 'GET') {
      const id = parseInt(url.split('/').pop()!, 10);
      const alert = this.alerts.find(a => a.id === id);
      return of(new HttpResponse({ status: 200, body: alert })).pipe(delay(300));
    }

    // Mock kill process
    if (url.match(/\/alerts\/\d+\/kill$/) && method === 'POST') {
      return of(new HttpResponse({ status: 200, body: { message: 'Process killed' } })).pipe(delay(200));
    }

    // Mock isolate device
    if (url.match(/\/alerts\/\d+\/isolate$/) && method === 'POST') {
      return of(new HttpResponse({ status: 200, body: { message: 'Device isolated' } })).pipe(delay(200));
    }

    // Mock endpoints
    if (url.endsWith('/endpoints') && method === 'GET') {
      return of(new HttpResponse({ status: 200, body: this.endpoints })).pipe(delay(400));
    }

    // Pass through anything not handled
    return next.handle(req);
  }
}
