from django.urls import path

from . import views



urlpatterns = [

    path('register/', views.RegisterAPIView.as_view(), name='register'),

    path('register-supplier/', views.RegisterSupplierAPIView.as_view(), name='register-supplier'),

    path('login/', views.LoginAPIView.as_view(), name='login'),

    path('user/', views.UserDetailAPIView.as_view(), name='user-detail'),

    path('verify-email/', views.VerifyEmailAPIView.as_view(), name='verify-email'),

    path('forgot-password/', views.ForgotPasswordAPIView.as_view(), name='forgot-password'),

    path('reset-password/', views.ResetPasswordAPIView.as_view(), name='reset-password'),

    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),

    path('company/', views.CompanyDetailAPIView.as_view(), name='company-detail'),

    path('companies/<int:id>/', views.CompanyByIdAPIView.as_view(), name='company-by-id'),

    path('companies/<int:company_id>/update/', views.CompanyUpdateAPIView.as_view(), name='company-update'),
    
    path('companies/<int:company_id>/documents/', views.DocumentAPIView.as_view(), name='company-documents'),
]
