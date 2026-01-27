from django.urls import path
from . import views

urlpatterns = [
    path('main-categories/', views.MainCategoryListAPIView.as_view(), name='main-categories-list'),
    path('products/', views.ProductListAPIView.as_view(), name='products-list'),
    path('products/filter-data/', views.ProductFilterDataAPIView.as_view(), name='products-filter-data'),
    path('products/<int:id>/', views.ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/<int:id>/similar/', views.SimilarProductsAPIView.as_view(), name='similar-products'),
    path('products/favourites/', views.FavouriteListAPIView.as_view(), name='favourites-list'),
    path('products/<int:product_id>/favourite/', views.AddFavouriteAPIView.as_view(), name='add-favourite'),
    path('products/<int:product_id>/favourite/remove/', views.RemoveFavouriteAPIView.as_view(), name='remove-favourite'),
    # Supplier Product APIs
    path('supplier/products/', views.SupplierProductListAPIView.as_view(), name='supplier-products-list'),
    path('supplier/products/<int:id>/', views.SupplierProductDetailAPIView.as_view(), name='supplier-product-detail'),
    path('supplier/products/create/', views.SupplierProductCreateAPIView.as_view(), name='supplier-product-create'),
    path('supplier/products/<int:id>/update/', views.SupplierProductUpdateAPIView.as_view(), name='supplier-product-update'),
    path('supplier/products/<int:id>/delete/', views.SupplierProductDeleteAPIView.as_view(), name='supplier-product-delete'),
]
