from django.urls import path
from parking.views.vehicle import VehicleListView, VehicleCreateView, VehicleUpdateView, VehicleDeleteView
from parking.views.parking_history import ParkingHistoryView, ParkingDetailView

app_name = 'parking'

urlpatterns = [
    # Quản lý phương tiện
    path('vehicles/', VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/add/', VehicleCreateView.as_view(), name='vehicle_add'),
    path('vehicles/<int:pk>/update/', VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle_delete'),

    # Lịch sử đỗ xe
    path('history/', ParkingHistoryView.as_view(), name='parking_history'),
    path('history/<int:pk>/', ParkingDetailView.as_view(), name='parking_detail'),
]