import { Component, OnInit, OnDestroy } from '@angular/core';

@Component({
  selector: 'app-live-device-status',
  templateUrl: './live-device-status.component.html',
  styleUrls: ['./live-device-status.component.scss']
})
export class LiveDeviceStatusComponent implements OnInit, OnDestroy {
  ws: WebSocket | null = null;
  latestStatus: any = null;
  allStatuses: any[] = [];

  ngOnInit() {
    this.ws = new WebSocket('ws://172.19.103.44:8000/ws/frontend');
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.latestStatus = data;
        this.allStatuses.unshift(data); // Keep a history
      } catch (e) {
        console.error('Failed to parse WS data:', e, event.data);
      }
    };
    this.ws.onopen = () => console.log('Connected to backend WebSocket');
    this.ws.onerror = (err) => console.error('WebSocket error:', err);
    this.ws.onclose = () => console.log('WebSocket closed');
  }

  ngOnDestroy() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
