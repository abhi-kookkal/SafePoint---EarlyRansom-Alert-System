import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AlertDetailComponent } from './alert-detail.component';

describe('AlertDetailComponent', () => {
  let component: AlertDetailComponent;
  let fixture: ComponentFixture<AlertDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AlertDetailComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AlertDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
