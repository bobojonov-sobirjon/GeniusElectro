from django.urls import path
from . import views

urlpatterns = [
    path('main-categories/', views.MainCategoryListAPIView.as_view(), name='main-categories-list'),
    path('products/', views.ProductListAPIView.as_view(), name='products-list'),
    path('products/filter-data/', views.ProductFilterDataAPIView.as_view(), name='products-filter-data'),
    path('products/<int:id>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/<int:id>/similar/', views.SimilarProductsAPIView.as_view(), name='similar-products'),
    path('products/<int:product_id>/favourite/', views.AddFavouriteAPIView.as_view(), name='add-favourite'),
    path('products/<int:product_id>/favourite/remove/', views.RemoveFavouriteAPIView.as_view(), name='remove-favourite'),
]
