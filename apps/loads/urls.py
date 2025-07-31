from django.urls import path
from apps.loads.views import LoadCreateAPIView, LoadMatchListAPIView

urlpatterns = [
    path('', LoadCreateAPIView.as_view(), name='create-load'),
    path('<int:pk>/matches/', LoadMatchListAPIView.as_view(), name='load-matches'),
]
