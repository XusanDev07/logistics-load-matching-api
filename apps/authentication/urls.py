from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from apps.authentication.views import RegisterAPIView

urlpatterns = [
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterAPIView.as_view(), name='register-view'),
    path('login/', TokenObtainPairView.as_view(), name='login-view'),

]
