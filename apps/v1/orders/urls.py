from django.urls import path
from . import views

urlpatterns = [
    path('delivery-methods/', views.DeliveryMethodListAPIView.as_view(), name='delivery-methods-list'),
    path('payment-methods/', views.PaymentMethodListAPIView.as_view(), name='payment-methods-list'),
    path('create/', views.OrderCreateAPIView.as_view(), name='order-create'),
    path('my-orders/', views.MyOrdersAPIView.as_view(), name='my-orders'),
    path('<int:id>/', views.OrderDetailAPIView.as_view(), name='order-detail'),
]