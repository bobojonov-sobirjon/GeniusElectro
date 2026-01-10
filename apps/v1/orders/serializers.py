from rest_framework import serializers
from .models import DeliveryMethod, PaymentMethod, Order, OrderProduct
from apps.v1.products.serializers import ProductSerializer


class DeliveryMethodSerializer(serializers.ModelSerializer):
    """Serializer for DeliveryMethod"""
    class Meta:
        model = DeliveryMethod
        fields = ('id', 'name', 'description')


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod"""
    class Meta:
        model = PaymentMethod
        fields = ('id', 'name', 'description')


class OrderProductSerializer(serializers.ModelSerializer):
    """Serializer for OrderProduct with product details"""
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = OrderProduct
        fields = ('id', 'product', 'product_id', 'quantity', 'price')


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order with order products"""
    order_products = OrderProductSerializer(many=True, read_only=True)
    delivery_method = DeliveryMethodSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'user', 'city', 'street', 'house', 'flat', 'index',
            'total_price', 'delivery_method', 'payment_method', 'price_for_delivery',
            'order_products', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class ProductListItemSerializer(serializers.Serializer):
    """Serializer for product list item"""
    product_id = serializers.IntegerField(required=True, help_text="ID товара")
    quantity = serializers.IntegerField(required=True, help_text="Количество")
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, help_text="Цена за единицу")


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    product_list = serializers.ListField(
        child=ProductListItemSerializer(),
        required=True,
        help_text="Список товаров в заказе"
    )
    city = serializers.CharField(max_length=100, required=True)
    street = serializers.CharField(required=True)
    house = serializers.CharField(max_length=10, required=True)
    flat = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    index = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    delivery_method = serializers.IntegerField(required=False, allow_null=True)
    payment_method = serializers.IntegerField(required=False, allow_null=True)
    price_for_delivery = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    
    def validate_product_list(self, value):
        """Validate product_list structure"""
        if not value:
            raise serializers.ValidationError("product_list cannot be empty")
        return value
