from rest_framework import status

from rest_framework.views import APIView

from rest_framework.response import Response

from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema, OpenApiParameter

from drf_spectacular.types import OpenApiTypes

from django.db import transaction

from django.db.models import Q

from .models import DeliveryMethod, PaymentMethod, Order, OrderProduct, OrderStatusType

from .serializers import (
    DeliveryMethodSerializer, PaymentMethodSerializer,
    OrderSerializer, OrderCreateSerializer, OrderProductStatusUpdateSerializer,
    OrderProductSerializer
)

from apps.v1.products.models import Product

from apps.v1.orders.utils import send_order_status_sms

from datetime import timedelta
from django.db.models import Sum, Count
from django.utils import timezone
from django.db.models.functions import TruncDay
from django.http import JsonResponse




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

        

        # Create order with default status

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

                price=price,

                status=OrderStatusType.OZHIDANIE  # Default status

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





# Supplier Order API Views

@extend_schema(

    tags=['Заказы (Поставщик)'],

    summary='Получить список заказов с товарами поставщика',

    description='Возвращает список заказов, содержащих товары текущего поставщика. Поставщик видит только свои товары в заказах. Заказы отсортированы по дате создания (новые сначала). Требуется аутентификация.',

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

            name='status',

            type=OpenApiTypes.STR,

            location=OpenApiParameter.QUERY,

            description='Фильтр по статусу товара в заказе: Ожидание, Обрабатывается, Отправлен',

            required=False

        )

    ]

)

class SupplierOrderListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    pagination_class = OrderPagination

    

    def get_queryset(self):

        """Get orders containing products from current supplier"""

        # Get orders that contain products from this supplier

        queryset = Order.objects.filter(

            order_products__product__user=self.request.user

        ).select_related(

            'user', 'delivery_method', 'payment_method'

        ).prefetch_related(

            'order_products__product',

            'order_products__product__sub_category',

            'order_products__product__sub_category__parent'

        ).distinct().order_by('-created_at', '-id')  # Yangi orderlar boshida

        

        # Filter by status (OrderProduct status)

        status_filter = self.request.query_params.get('status', None)

        if status_filter:

            queryset = queryset.filter(order_products__status=status_filter).distinct()

        

        return queryset

    

    def get(self, request):

        """Get orders with supplier's products"""

        queryset = self.get_queryset()

        

        # Apply pagination

        paginator = self.pagination_class()

        paginated_queryset = paginator.paginate_queryset(queryset, request)

        

        # Filter order_products to show only supplier's products

        serializer = OrderSerializer(paginated_queryset, many=True, context={'request': request})

        

        # Filter order_products in response to show only supplier's products

        supplier_id = request.user.id

        for order_data in serializer.data:

            if 'order_products' in order_data:

                order_data['order_products'] = [

                    op for op in order_data['order_products']

                    if op.get('product', {}).get('user') == supplier_id

                ]

        

        return paginator.get_paginated_response(serializer.data)





@extend_schema(

    tags=['Заказы (Поставщик)'],

    summary='Получить детали заказа по ID',

    description='Возвращает полную информацию о заказе по его ID. Показываются только товары текущего поставщика. Требуется аутентификация.',

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

class SupplierOrderDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    

    def get(self, request, id):

        """Get order details by ID with only supplier's products"""

        try:

            order = Order.objects.select_related(

                'user', 'delivery_method', 'payment_method'

            ).prefetch_related(

                'order_products__product',

                'order_products__product__sub_category',

                'order_products__product__sub_category__parent',

                'order_products__product__images'

            ).filter(

                order_products__product__user=request.user

            ).distinct().get(id=id)

        except Order.DoesNotExist:

            return Response({

                'error': 'Заказ не найден или не содержит ваших товаров'

            }, status=status.HTTP_404_NOT_FOUND)

        

        serializer = OrderSerializer(order, context={'request': request})

        

        # Filter order_products to show only supplier's products

        supplier_id = request.user.id

        if 'order_products' in serializer.data:

            serializer.data['order_products'] = [

                op for op in serializer.data['order_products']

                if op.get('product', {}).get('user') == supplier_id

            ]

        

        return Response(serializer.data, status=status.HTTP_200_OK)





@extend_schema(

    tags=['Заказы (Поставщик)'],

    summary='Изменить статус товара в заказе',

    description="""

    Изменяет статус товара в заказе. Поставщик может изменить статус только своих товаров в заказе.

    При изменении статуса, пользователю, создавшему заказ, отправляется SMS уведомление.

    

    **Доступные статусы:**

    - `Ожидание` - Товар ожидает обработки

    - `Обрабатывается` - Товар находится в обработке

    - `Отправлен` - Товар отправлен

    

    **SMS уведомление:**

    После успешного изменения статуса, пользователю, создавшему заказ, отправляется SMS с информацией о том, что статус товара в заказе был изменен на новый статус.

    

    Требуется аутентификация.

    """,

    request=OrderProductStatusUpdateSerializer,

    responses={

        200: OrderProductSerializer,

        400: OpenApiTypes.OBJECT,

        404: OpenApiTypes.OBJECT

    },

    parameters=[

        OpenApiParameter(

            name='order_id',

            type=OpenApiTypes.INT,

            location=OpenApiParameter.PATH,

            description='ID заказа',

            required=True

        ),

        OpenApiParameter(

            name='order_product_id',

            type=OpenApiTypes.INT,

            location=OpenApiParameter.PATH,

            description='ID товара в заказе (OrderProduct ID)',

            required=True

        )

    ]

)

class SupplierOrderProductStatusUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    

    def patch(self, request, order_id, order_product_id):

        """Update order product status"""

        try:

            order_product = OrderProduct.objects.select_related(

                'order', 'order__user', 'product', 'product__user'

            ).get(

                id=order_product_id,

                order_id=order_id,

                product__user=request.user  # Only supplier's products

            )

        except OrderProduct.DoesNotExist:

            return Response({

                'error': 'Товар в заказе не найден или не принадлежит вам'

            }, status=status.HTTP_404_NOT_FOUND)

        

        serializer = OrderProductStatusUpdateSerializer(data=request.data)

        if serializer.is_valid():

            old_status = order_product.status

            new_status = serializer.validated_data['status']

            

            # Update status

            order_product.status = new_status

            order_product.save()

            

            # Send SMS to order creator if status changed

            if old_status != new_status:

                try:

                    send_order_status_sms(order_product.order, new_status, order_product)

                except Exception as e:

                    # Log error but don't fail the request

                    import logging

                    logger = logging.getLogger(__name__)

                    logger.error(f"Failed to send SMS for order product {order_product.id}: {str(e)}")

            

            # Return updated order product

            from .serializers import OrderProductSerializer

            order_product_serializer = OrderProductSerializer(order_product, context={'request': request})

            return Response({

                'message': 'Статус товара в заказе успешно обновлен',

                'order_product': order_product_serializer.data

            }, status=status.HTTP_200_OK)

        

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierSalesAnalyticsAPIView(APIView):
    """
    API для аналитики продаж поставщика по дням
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Analytics"],
        summary="Аналитика продаж по дням",
        description="""
        Возвращает аналитику продаж поставщика по дням за указанный месяц и год.
        
        **Параметры запроса:**
        - month (integer): Месяц (1-12)
        - year (integer): Год (например: 2024)
        
        **Возвращаемые данные:**
        - sales_data: Массив данных по дням месяца
        - total_sales: Общая сумма продаж за месяц
        - total_orders: Общее количество заказов за месяц
        
        **Формат данных по дням:**
        ```json
        {
            "date": "2024-01-01",
            "total_price": 15000.00,
            "order_count": 3
        }
        ```
        """,
        parameters=[
            OpenApiParameter(
                name='month',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Месяц (1-12)',
                required=True
            ),
            OpenApiParameter(
                name='year',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Год (например: 2024)',
                required=True
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        }
    )
    
    def get(self, request):
        """Получить аналитику продаж по дням"""
        try:
            month = int(request.GET.get('month'))
            year = int(request.GET.get('year'))
            
            # Валидация месяца
            if month < 1 or month > 12:
                return Response({
                    'error': 'Месяц должен быть от 1 до 12'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Валидация года
            if year < 2020 or year > 2030:
                return Response({
                    'error': 'Год должен быть от 2020 до 2030'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, TypeError):
            return Response({
                'error': 'Неверный формат месяца или года'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Получаем начало и конец месяца
        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, month + 1, 1)
        
        # Получаем все OrderProduct для товаров пользователя за указанный период
        order_products = OrderProduct.objects.filter(
            product__user=user,
            created_at__gte=start_date,
            created_at__lt=end_date
        ).annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            total_price=Sum('price'),
            order_count=Count('order', distinct=True)
        ).order_by('day')
        
        # Формируем данные для каждого дня месяца
        sales_data = []
        total_sales = 0
        total_orders = 0
        
        # Получаем количество дней в месяце
        if month == 12:
            days_in_month = 31
        else:
            days_in_month = (timezone.datetime(year, month + 1, 1) - timezone.datetime(year, month, 1)).days
        
        # Создаем словарь с данными по дням
        daily_data = {}
        for item in order_products:
            daily_data[item['day'].day] = {
                'date': item['day'].strftime('%Y-%m-%d'),
                'total_price': float(item['total_price'] or 0),
                'order_count': item['order_count'] or 0
            }
            total_sales += float(item['total_price'] or 0)
            total_orders += item['order_count'] or 0
        
        # Заполняем пропущенные дни нулями
        for day in range(1, days_in_month + 1):
            if day in daily_data:
                sales_data.append(daily_data[day])
            else:
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                sales_data.append({
                    'date': date_str,
                    'total_price': 0.0,
                    'order_count': 0
                })
        
        return Response({
            'month': month,
            'year': year,
            'sales_data': sales_data,
            'total_sales': total_sales,
            'total_orders': total_orders,
            'days_in_month': days_in_month
        }, status=status.HTTP_200_OK)


def calculate_percentage_change(current, previous):
    if previous == 0:
        return {
            "change_type": "increase" if current > 0 else "same",
            "difference": 100 if current > 0 else 0
        }

    percent = ((current - previous) / previous) * 100

    return {
        "change_type": "increase" if percent > 0 else "decrease" if percent < 0 else "same",
        "difference": round(abs(percent), 2)
    }


def calculate_count_change(current, previous):
    if previous == 0:
        return {
            "change_type": "increase" if current > 0 else "same",
            "difference": current
        }

    if current > previous:
        return {
            "change_type": "increase",
            "difference": current - previous
        }
    elif current < previous:
        return {
            "change_type": "decrease",
            "difference": previous - current
        }
    return {
        "change_type": "same",
        "difference": 0
    }


class SupplierAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
    tags=["Analytics"],
    summary="Аналитика для дашборда",
    description="""
API возвращает **основную аналитику для дашборда поставщика**.

Возвращаемые показатели:

1️⃣ **Общий доход (total_income)**
- Общий доход за последние 7 дней
- Сравнивается с предыдущей неделей
- `difference` возвращается в процентах (%)

2️⃣ **Активные товары (active_products)**
- Общее количество товаров пользователя
- Количество товаров, добавленных в текущем месяце
- Сравнение с прошлым месяцем

3️⃣ **Всего заказов (orders_total)**
- Общее количество заказов пользователя
- Количество заказов за текущий год
- Сравнение с прошлым годом

4️⃣ **Заказы в работе (orders_in_progress)**
- Количество заказов со статусами:
  - `Ожидание`
  - `Обрабатывается`
- Сравнение за последнюю неделю

Возможные значения `change_type`:
- `increase` — увеличение
- `decrease` — уменьшение
- `same` — без изменений

Требуется авторизация.
""",
)
    def get(self, request):
        user = request.user
        now = timezone.now()

        # ============================
        # DATE RANGES
        # ============================
        start_week = now - timedelta(days=7)
        prev_week = start_week - timedelta(days=7)

        start_month = now.replace(day=1)
        prev_month = (start_month - timedelta(days=1)).replace(day=1)

        start_year = now.replace(month=1, day=1)
        prev_year = start_year.replace(year=start_year.year - 1)

        # ============================
        # 1. TOTAL INCOME (WEEKLY, %)
        # ============================
        current_income = Order.objects.filter(
            user=user,
            created_at__gte=start_week
        ).aggregate(total=Sum('total_price'))['total'] or 0

        previous_income = Order.objects.filter(
            user=user,
            created_at__gte=prev_week,
            created_at__lt=start_week
        ).aggregate(total=Sum('total_price'))['total'] or 0

        income_change = calculate_percentage_change(
            current_income,
            previous_income
        )

        # ============================
        # 2. ACTIVE PRODUCTS (MONTHLY)
        # ============================
        total_products = Product.objects.filter(user=user).count()

        current_month_products = Product.objects.filter(
            user=user,
            created_at__gte=start_month
        ).count()

        previous_month_products = Product.objects.filter(
            user=user,
            created_at__gte=prev_month,
            created_at__lt=start_month
        ).count()

        products_change = calculate_count_change(
            current_month_products,
            previous_month_products
        )

        # ============================
        # 3. TOTAL ORDERS (YEARLY)
        # ============================
        total_orders = Order.objects.filter(user=user).count()

        current_year_orders = Order.objects.filter(
            user=user,
            created_at__gte=start_year
        ).count()

        previous_year_orders = Order.objects.filter(
            user=user,
            created_at__gte=prev_year,
            created_at__lt=start_year
        ).count()

        orders_change = calculate_count_change(
            current_year_orders,
            previous_year_orders
        )

        # ============================
        # 4. ORDERS IN PROGRESS (WEEKLY)
        # STATUS LOGIC (TZ):
        # - Ожидание
        # - Обрабатывается  → IN PROGRESS
        # - Отправлен       → FINISHED
        # ============================
        current_in_progress = OrderProduct.objects.filter(
            order__user=user,
            created_at__gte=start_week,
            status__in=[
                OrderStatusType.OZHIDANIE,
                OrderStatusType.OBRABATYVAETSYA
            ]
        ).count()

        previous_in_progress = OrderProduct.objects.filter(
            order__user=user,
            created_at__gte=prev_week,
            created_at__lt=start_week,
            status__in=[
                OrderStatusType.OZHIDANIE,
                OrderStatusType.OBRABATYVAETSYA
            ]
        ).count()

        in_progress_change = calculate_count_change(
            current_in_progress,
            previous_in_progress
        )

        # ============================
        # RESPONSE
        # ============================
        return Response({
            "total_income": {
                "total": current_income,
                **income_change   # difference => %
            },
            "active_products": {
                "total": total_products,
                "this_month": current_month_products,
                **products_change
            },
            "orders_total": {
                "total": total_orders,
                "this_year": current_year_orders,
                **orders_change
            },
            "orders_in_progress": {
                "total": current_in_progress,
                **in_progress_change
            }
        })