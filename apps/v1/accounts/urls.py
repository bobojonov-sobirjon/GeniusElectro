from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('user/', views.UserDetailAPIView.as_view(), name='user-detail'),
    path('verify-email/', views.VerifyEmailAPIView.as_view(), name='verify-email'),
    path('forgot-password/', views.ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordAPIView.as_view(), name='reset-password'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),
]
