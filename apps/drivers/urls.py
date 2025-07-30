from django.urls import path
from .views import DriverAvailabilityAPIView, SuitableLoadsAPIView, BulkDriverAvailabilityAPIView

urlpatterns = [
    path('availability/', DriverAvailabilityAPIView.as_view(), name='driver-availability'),
    path('suitable-loads/', SuitableLoadsAPIView.as_view(), name='suitable-loads'),
    path('availability/bulk/', BulkDriverAvailabilityAPIView.as_view(), name='drivers-availability'),
]
