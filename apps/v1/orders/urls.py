from django.urls import path

from . import views



urlpatterns = [

    path('delivery-methods/', views.DeliveryMethodListAPIView.as_view(), name='delivery-methods-list'),

    path('payment-methods/', views.PaymentMethodListAPIView.as_view(), name='payment-methods-list'),

    path('create/', views.OrderCreateAPIView.as_view(), name='order-create'),

    path('my-orders/', views.MyOrdersAPIView.as_view(), name='my-orders'),

    path('<int:id>/', views.OrderDetailAPIView.as_view(), name='order-detail'),

    # Supplier Order APIs

    path('supplier/orders/', views.SupplierOrderListAPIView.as_view(), name='supplier-orders-list'),

    path('supplier/orders/<int:id>/', views.SupplierOrderDetailAPIView.as_view(), name='supplier-order-detail'),

    path('supplier/orders/<int:order_id>/products/<int:order_product_id>/status/', views.SupplierOrderProductStatusUpdateAPIView.as_view(), name='supplier-order-product-status-update'),

    path('supplier/analytics/', views.SupplierAnalyticsAPIView.as_view(), name='supplier-analytics'),
    path('supplier/analytics/sales/', views.SupplierSalesAnalyticsAPIView.as_view(), name='supplier-sales-analytics'),

]