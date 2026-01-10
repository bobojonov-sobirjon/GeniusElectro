from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import models
from django.db.models import Q, Min, Max
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Category, Product, Favourite
from .serializers import MainCategorySerializer, ProductSerializer


class ProductPagination(PageNumberPagination):
    """Custom pagination for products - 12 items per page by default"""
    page_size = 12
    page_size_query_param = 'limit'
    max_page_size = 100


@extend_schema(
    tags=['Категории'],
    summary='Получить список основных категорий',
    description='Возвращает список всех основных категорий с их подкатегориями. Поддерживает фильтрацию по ID, названию основной категории, названию подкатегории и поиск.',
    responses={200: MainCategorySerializer(many=True)},
    parameters=[
        OpenApiParameter(
            name='main_category_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Фильтр по ID основной категории',
            required=False
        ),
        OpenApiParameter(
            name='main_category',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по названию основной категории (частичное совпадение)',
            required=False
        ),
        OpenApiParameter(
            name='sub_category',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по названию подкатегории (частичное совпадение)',
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Поиск по названиям основной и подкатегорий',
            required=False
        )
    ]
)
class MainCategoryListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Get all main categories (categories without parent)"""
        queryset = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
        
        # Filter by main category ID
        main_category_id = self.request.query_params.get('main_category_id', None)
        if main_category_id:
            try:
                queryset = queryset.filter(id=int(main_category_id))
            except (ValueError, TypeError):
                pass  # Invalid ID, ignore filter
        
        # Filter by main category name
        main_category_name = self.request.query_params.get('main_category', None)
        if main_category_name:
            queryset = queryset.filter(name__icontains=main_category_name)
        
        # Filter by sub category name
        sub_category_name = self.request.query_params.get('sub_category', None)
        if sub_category_name:
            queryset = queryset.filter(subcategories__name__icontains=sub_category_name)
        
        # Search filter (both main and sub category names)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) | 
                models.Q(subcategories__name__icontains=search)
            )
        
        return queryset.distinct()
    
    def get(self, request):
        queryset = self.get_queryset()
        serializer = MainCategorySerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Товары'],
    summary='Получить данные для фильтров',
    description='Возвращает все доступные значения для фильтров продуктов (производители, материалы, категории и т.д.)',
    responses={200: OpenApiTypes.OBJECT}
)
class ProductFilterDataAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all filter data for products"""
        # Производители (Manufacturers)
        manufacturers = Product.objects.filter(
            manufacturer__isnull=False
        ).exclude(manufacturer='').values_list('manufacturer', flat=True).distinct().order_by('manufacturer')
        
        # Материалы проводника (Conductor materials)
        conductor_materials = Product.objects.filter(
            conductor_material__isnull=False
        ).exclude(conductor_material='').values_list('conductor_material', flat=True).distinct().order_by('conductor_material')
        
        # Количество ядер (Number of cores)
        number_of_cores = Product.objects.filter(
            number_of_cores__gt=0
        ).values_list('number_of_cores', flat=True).distinct().order_by('number_of_cores')
        
        # Основные категории (Main categories)
        main_categories = Category.objects.filter(
            parent__isnull=True
        ).values('id', 'name').order_by('name')
        
        # Подкатегории (Sub categories)
        sub_categories = Category.objects.filter(
            parent__isnull=False
        ).values('id', 'name', 'parent_id').order_by('name')
        
        # Сечение кабеля, мм² (Cable cross-section)
        cable_cross_sections = Product.objects.filter(
            cable_cross_section__isnull=False
        ).values_list('cable_cross_section', flat=True).distinct().order_by('cable_cross_section')
        
        # Материал внешней изоляции (Outer insulation material)
        outer_insulation_materials = Product.objects.filter(
            outer_insulation_material__isnull=False
        ).exclude(outer_insulation_material='').values_list('outer_insulation_material', flat=True).distinct().order_by('outer_insulation_material')
        
        # Материал изоляции проводника (Conductor insulation material)
        conductor_insulation_materials = Product.objects.filter(
            conductor_insulation_material__isnull=False
        ).exclude(conductor_insulation_material='').values_list('conductor_insulation_material', flat=True).distinct().order_by('conductor_insulation_material')
        
        # Материал внешней оболочки (Outer sheath material)
        outer_sheath_materials = Product.objects.filter(
            outer_sheath_material__isnull=False
        ).exclude(outer_sheath_material='').values_list('outer_sheath_material', flat=True).distinct().order_by('outer_sheath_material')
        
        # Цвет (Color)
        colors = Product.objects.filter(
            color__isnull=False
        ).exclude(color='').values_list('color', flat=True).distinct().order_by('color')
        
        # Модель/исполнение (Model/version)
        model_versions = Product.objects.filter(
            model_version__isnull=False
        ).exclude(model_version='').values_list('model_version', flat=True).distinct().order_by('model_version')
        
        # Цена диапазон (Price range)
        price_range = Product.objects.aggregate(
            min_price=Min('price_per_meter'),
            max_price=Max('price_per_meter')
        )
        
        return Response({
            'manufacturers': list(manufacturers) if manufacturers else [],
            'conductor_materials': list(conductor_materials) if conductor_materials else [],
            'number_of_cores': list(number_of_cores) if number_of_cores else [],
            'cable_cross_sections': [float(x) for x in cable_cross_sections] if cable_cross_sections else [],
            'outer_insulation_materials': list(outer_insulation_materials) if outer_insulation_materials else [],
            'conductor_insulation_materials': list(conductor_insulation_materials) if conductor_insulation_materials else [],
            'outer_sheath_materials': list(outer_sheath_materials) if outer_sheath_materials else [],
            'colors': list(colors) if colors else [],
            'model_versions': list(model_versions) if model_versions else [],
            'main_categories': list(main_categories) if main_categories else [],
            'sub_categories': list(sub_categories) if sub_categories else [],
            'price_range': {
                'min': float(price_range['min_price']) if price_range['min_price'] else 0,
                'max': float(price_range['max_price']) if price_range['max_price'] else 0
            }
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Товары'],
    summary='Получить список товаров',
    description='Возвращает список всех товаров с полной информацией (изображения, метраж, избранное). Поддерживает множественные фильтры.',
    responses={200: ProductSerializer(many=True)},
    parameters=[
        OpenApiParameter(
            name='main_category_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Фильтр по ID основной категории',
            required=False
        ),
        OpenApiParameter(
            name='sub_category_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Фильтр по ID подкатегории',
            required=False
        ),
        OpenApiParameter(
            name='manufacturer',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по производителю (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='conductor_material',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по материалу проводника (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='number_of_cores',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Фильтр по количеству ядер',
            required=False
        ),
        OpenApiParameter(
            name='min_price',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description='Минимальная цена за метр',
            required=False
        ),
        OpenApiParameter(
            name='max_price',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description='Максимальная цена за метр',
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Поиск по названию, описанию, SKU',
            required=False
        ),
        OpenApiParameter(
            name='is_active',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Фильтр по активности товара',
            required=False
        ),
        OpenApiParameter(
            name='cable_cross_section',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description='Фильтр по сечению кабеля, мм²',
            required=False
        ),
        OpenApiParameter(
            name='outer_insulation_material',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по материалу внешней изоляции (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='conductor_insulation_material',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по материалу изоляции проводника (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='outer_sheath_material',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по материалу внешней оболочки (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='color',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по цвету (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='model_version',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по модели/исполнению (можно несколько через запятую)',
            required=False
        ),
        OpenApiParameter(
            name='popular',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Фильтр популярных товаров (с наибольшим количеством избранных)',
            required=False
        ),
        OpenApiParameter(
            name='new',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Фильтр новых товаров (недавно добавленные)',
            required=False
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Номер страницы (по умолчанию 1)',
            required=False
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Количество товаров на странице (по умолчанию 12, максимум 100)',
            required=False
        )
    ]
)
class ProductListAPIView(APIView):
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    
    def get_queryset(self):
        """Get all products with filters"""
        queryset = Product.objects.select_related(
            'sub_category', 'sub_category__parent'
        ).prefetch_related('images', 'meterages').filter(is_active=True)
        
        # Filter by main category ID
        main_category_id = self.request.query_params.get('main_category_id', None)
        if main_category_id:
            try:
                queryset = queryset.filter(sub_category__parent_id=int(main_category_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by sub category ID
        sub_category_id = self.request.query_params.get('sub_category_id', None)
        if sub_category_id:
            try:
                queryset = queryset.filter(sub_category_id=int(sub_category_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by manufacturer (multiple values)
        manufacturer = self.request.query_params.get('manufacturer', None)
        if manufacturer:
            manufacturers = [m.strip() for m in manufacturer.split(',')]
            queryset = queryset.filter(manufacturer__in=manufacturers)
        
        # Filter by conductor material (multiple values)
        conductor_material = self.request.query_params.get('conductor_material', None)
        if conductor_material:
            materials = [m.strip() for m in conductor_material.split(',')]
            queryset = queryset.filter(conductor_material__in=materials)
        
        # Filter by number of cores
        number_of_cores = self.request.query_params.get('number_of_cores', None)
        if number_of_cores:
            try:
                queryset = queryset.filter(number_of_cores=int(number_of_cores))
            except (ValueError, TypeError):
                pass
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            try:
                queryset = queryset.filter(price_per_meter__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            try:
                queryset = queryset.filter(price_per_meter__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        
        # Search filter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1', 'yes'])
        
        # Filter by cable cross-section
        cable_cross_section = self.request.query_params.get('cable_cross_section', None)
        if cable_cross_section:
            try:
                queryset = queryset.filter(cable_cross_section=float(cable_cross_section))
            except (ValueError, TypeError):
                pass
        
        # Filter by outer insulation material (multiple values)
        outer_insulation_material = self.request.query_params.get('outer_insulation_material', None)
        if outer_insulation_material:
            materials = [m.strip() for m in outer_insulation_material.split(',')]
            queryset = queryset.filter(outer_insulation_material__in=materials)
        
        # Filter by conductor insulation material (multiple values)
        conductor_insulation_material = self.request.query_params.get('conductor_insulation_material', None)
        if conductor_insulation_material:
            materials = [m.strip() for m in conductor_insulation_material.split(',')]
            queryset = queryset.filter(conductor_insulation_material__in=materials)
        
        # Filter by outer sheath material (multiple values)
        outer_sheath_material = self.request.query_params.get('outer_sheath_material', None)
        if outer_sheath_material:
            materials = [m.strip() for m in outer_sheath_material.split(',')]
            queryset = queryset.filter(outer_sheath_material__in=materials)
        
        # Filter by color (multiple values)
        color = self.request.query_params.get('color', None)
        if color:
            colors = [c.strip() for c in color.split(',')]
            queryset = queryset.filter(color__in=colors)
        
        # Filter by model version (multiple values)
        model_version = self.request.query_params.get('model_version', None)
        if model_version:
            versions = [v.strip() for v in model_version.split(',')]
            queryset = queryset.filter(model_version__in=versions)
        
        # Filter by popular (products with most favourites)
        popular = self.request.query_params.get('popular', None)
        if popular and popular.lower() in ['true', '1', 'yes']:
            from django.db.models import Count
            queryset = queryset.annotate(
                favourites_count=Count('favourites')
            ).filter(favourites_count__gt=0).order_by('-favourites_count')
        
        # Filter by new (recently added products)
        new = self.request.query_params.get('new', None)
        if new and new.lower() in ['true', '1', 'yes']:
            queryset = queryset.order_by('-created_at')
        
        return queryset.distinct()
    
    def get(self, request):
        queryset = self.get_queryset()
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = ProductSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


@extend_schema(
    tags=['Товары'],
    summary='Получить детали товара',
    description='Возвращает полную информацию о конкретном товаре по его ID',
    responses={200: ProductSerializer, 404: OpenApiTypes.OBJECT},
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID товара',
            required=True
        )
    ]
)
class ProductDetailAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, id):
        """Get product details by ID"""
        try:
            product = Product.objects.select_related(
                'sub_category', 'sub_category__parent'
            ).prefetch_related('images', 'meterages').get(id=id, is_active=True)
            
            serializer = ProductSerializer(product, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=['Товары'],
    summary='Получить похожие товары',
    description='Возвращает список товаров, похожих на указанный товар (по категории, производителю и другим характеристикам)',
    responses={200: ProductSerializer(many=True), 404: OpenApiTypes.OBJECT},
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID товара для поиска похожих',
            required=True
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Количество похожих товаров (по умолчанию 10)',
            required=False
        )
    ]
)
class SimilarProductsAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, id):
        """Get similar products by product ID"""
        try:
            product = Product.objects.get(id=id, is_active=True)
        except Product.DoesNotExist:
            return Response({
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Limit for similar products
        limit = int(request.query_params.get('limit', 10))
        
        # Get similar products based on priority:
        # 1. Same sub_category (highest priority)
        # 2. Same main_category
        # 3. Same manufacturer
        # 4. Same conductor_material
        
        similar_queryset = Product.objects.select_related(
            'sub_category', 'sub_category__parent'
        ).prefetch_related('images', 'meterages').filter(
            is_active=True
        ).exclude(id=product.id)
        
        # Build query for similar products
        from django.db.models import Q
        similar_conditions = Q()
        
        # Priority 1: Same sub_category
        if product.sub_category:
            similar_conditions |= Q(sub_category=product.sub_category)
        
        # Priority 2: Same main_category
        if product.sub_category and product.sub_category.parent:
            similar_conditions |= Q(sub_category__parent=product.sub_category.parent)
        
        # Priority 3: Same manufacturer
        if product.manufacturer:
            similar_conditions |= Q(manufacturer=product.manufacturer)
        
        # Priority 4: Same conductor_material
        if product.conductor_material:
            similar_conditions |= Q(conductor_material=product.conductor_material)
        
        # Get similar products
        if similar_conditions:
            similar_products = list(similar_queryset.filter(similar_conditions).distinct()[:limit])
        else:
            similar_products = []
        
        # If not enough products, fill with any active products
        if len(similar_products) < limit:
            remaining = limit - len(similar_products)
            similar_ids = [p.id for p in similar_products]
            similar_ids.append(product.id)
            
            additional = list(Product.objects.select_related(
                'sub_category', 'sub_category__parent'
            ).prefetch_related('images', 'meterages').filter(
                is_active=True
            ).exclude(id__in=similar_ids).order_by('-created_at')[:remaining])
            
            similar_products.extend(additional)
        
        serializer = ProductSerializer(similar_products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Избранное'],
    summary='Добавить товар в избранное',
    description='Добавляет товар в избранное для текущего пользователя. Требуется аутентификация.',
    responses={
        201: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    },
    parameters=[
        OpenApiParameter(
            name='product_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID товара для добавления в избранное',
            required=True
        )
    ]
)
class AddFavouriteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, product_id):
        """Add product to favourites"""
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already in favourites
        favourite, created = Favourite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({
                'message': 'Товар успешно добавлен в избранное',
                'product_id': product.id,
                'product_name': product.name
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Товар уже в избранном',
                'product_id': product.id,
                'product_name': product.name
            }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Избранное'],
    summary='Удалить товар из избранного',
    description='Удаляет товар из избранного для текущего пользователя. Требуется аутентификация.',
    responses={
        200: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    },
    parameters=[
        OpenApiParameter(
            name='product_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID товара для удаления из избранного',
            required=True
        )
    ]
)
class RemoveFavouriteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, product_id):
        """Remove product from favourites"""
        try:
            favourite = Favourite.objects.get(
                user=request.user,
                product_id=product_id
            )
            product_name = favourite.product.name
            favourite.delete()
            
            return Response({
                'message': 'Товар успешно удален из избранного',
                'product_id': product_id,
                'product_name': product_name
            }, status=status.HTTP_200_OK)
        except Favourite.DoesNotExist:
            return Response({
                'error': 'Товар не найден в избранном'
            }, status=status.HTTP_404_NOT_FOUND)
