from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import transaction
from django.db.models import Q
from .models import DeliveryMethod, PaymentMethod, Order, OrderProduct
from .serializers import (
    DeliveryMethodSerializer, PaymentMethodSerializer,
    OrderSerializer, OrderCreateSerializer
)
from apps.v1.products.models import Product


class OrderPagination(PageNumberPagination):
    """Custom pagination for orders - 12 items per page by default"""
    page_size = 12
    page_size_query_param = 'limit'
    max_page_size = 100


@extend_schema(
    tags=['Способ доставки'],
    summary='Получить список способов доставки',
    description='Возвращает список всех доступных способов доставки',
    responses={200: DeliveryMethodSerializer(many=True)}
)
class DeliveryMethodListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all delivery methods"""
        delivery_methods = DeliveryMethod.objects.all().order_by('name')
        serializer = DeliveryMethodSerializer(delivery_methods, many=True, context={'request': request})
        return Response({
            'delivery_methods': serializer.data
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Способы оплаты'],
    summary='Получить список способов оплаты',
    description='Возвращает список всех доступных способов оплаты',
    responses={200: PaymentMethodSerializer(many=True)}
)
class PaymentMethodListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all payment methods"""
        payment_methods = PaymentMethod.objects.all().order_by('name')
        serializer = PaymentMethodSerializer(payment_methods, many=True, context={'request': request})
        return Response({
            'payment_methods': serializer.data
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Заказы'],
    summary='Создать заказ',
    description='Создает новый заказ для текущего пользователя. Требуется аутентификация.',
    request=OrderCreateSerializer,
    responses={201: OrderSerializer, 400: OpenApiTypes.OBJECT}
)
class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """Create a new order"""
        serializer = OrderCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        product_list = validated_data['product_list']
        
        # Validate delivery_method and payment_method if provided
        delivery_method = None
        if validated_data.get('delivery_method'):
            try:
                delivery_method = DeliveryMethod.objects.get(id=validated_data['delivery_method'])
            except DeliveryMethod.DoesNotExist:
                return Response({
                    'error': 'Способ доставки не найден'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = None
        if validated_data.get('payment_method'):
            try:
                payment_method = PaymentMethod.objects.get(id=validated_data['payment_method'])
            except PaymentMethod.DoesNotExist:
                return Response({
                    'error': 'Способ оплаты не найден'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            city=validated_data['city'],
            street=validated_data['street'],
            house=validated_data['house'],
            flat=validated_data.get('flat', ''),
            index=validated_data.get('index', ''),
            total_price=validated_data['total_price'],
            delivery_method=delivery_method,
            payment_method=payment_method,
            price_for_delivery=validated_data['price_for_delivery']
        )
        
        # Create order products
        order_products = []
        for product_item in product_list:
            product_id = int(product_item['product_id'])
            quantity = int(product_item['quantity'])
            price = float(product_item['price'])
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                order.delete()  # Rollback order if product not found
                return Response({
                    'error': f'Товар с ID {product_id} не найден или неактивен'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            order_product = OrderProduct.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )
            order_products.append(order_product)
        
        # Return created order with products
        response_serializer = OrderSerializer(order, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Заказы'],
    summary='Получить мои заказы',
    description='Возвращает список всех заказов текущего пользователя с пагинацией и фильтрацией. Требуется аутентификация.',
    responses={200: OrderSerializer(many=True)},
    parameters=[
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
            description='Количество заказов на странице (по умолчанию 12, максимум 100)',
            required=False
        ),
        OpenApiParameter(
            name='product_name',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Фильтр по названию товара (частичное совпадение)',
            required=False
        ),
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
        )
    ]
)
class MyOrdersAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Get filtered orders for current user"""
        queryset = Order.objects.filter(user=self.request.user).select_related(
            'delivery_method', 'payment_method'
        ).prefetch_related(
            'order_products__product',
            'order_products__product__sub_category',
            'order_products__product__sub_category__parent'
        ).order_by('-created_at')
        
        # Filter by product name
        product_name = self.request.query_params.get('product_name', None)
        if product_name:
            queryset = queryset.filter(
                order_products__product__name__icontains=product_name
            ).distinct()
        
        # Filter by main category ID
        main_category_id = self.request.query_params.get('main_category_id', None)
        if main_category_id:
            try:
                queryset = queryset.filter(
                    order_products__product__sub_category__parent_id=int(main_category_id)
                ).distinct()
            except (ValueError, TypeError):
                pass
        
        # Filter by sub category ID
        sub_category_id = self.request.query_params.get('sub_category_id', None)
        if sub_category_id:
            try:
                queryset = queryset.filter(
                    order_products__product__sub_category_id=int(sub_category_id)
                ).distinct()
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def get(self, request):
        """Get all orders for current user with pagination and filters"""
        queryset = self.get_queryset()
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = OrderSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


@extend_schema(
    tags=['Заказы'],
    summary='Получить детали заказа',
    description='Возвращает полную информацию о заказе по его ID. Требуется аутентификация. Пользователь может видеть только свои заказы.',
    responses={200: OrderSerializer, 404: OpenApiTypes.OBJECT},
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID заказа',
            required=True
        )
    ]
)
class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        """Get order details by ID"""
        try:
            order = Order.objects.select_related(
                'delivery_method', 'payment_method', 'user'
            ).prefetch_related('order_products__product').get(id=id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
