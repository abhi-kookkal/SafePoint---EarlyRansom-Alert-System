import { Component, OnInit } from '@angular/core';
import { EndpointService, Endpoint } from '../../services/endpoint.service';

@Component({
  selector: 'app-endpoint-list',
  templateUrl: './endpoint-list.component.html',
  styleUrls: ['./endpoint-list.component.scss']
})
export class EndpointListComponent implements OnInit {
  endpoints: Endpoint[] = [];
  loading = true;

  constructor(private endpointService: EndpointService) {}

  ngOnInit(): void {
    this.endpointService.getEndpoints().subscribe({
      next: (data) => {
        this.endpoints = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }
}
