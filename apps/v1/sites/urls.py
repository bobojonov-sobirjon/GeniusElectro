from django.urls import path
from . import views

urlpatterns = [
    path('contact/', views.ContactAPIView.as_view(), name='contact'),
    path('partners/', views.PartnerListAPIView.as_view(), name='partners-list'),
    path('request/', views.RequestCreateAPIView.as_view(), name='request-create'),
]