from django.contrib import admin
from .models import DeliveryMethod, PaymentMethod, Order, OrderProduct


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'has_description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_description(self, obj):
        return bool(obj.description)
    has_description.boolean = True
    has_description.short_description = 'Есть описание'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'has_description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_description(self, obj):
        return bool(obj.description)
    has_description.boolean = True
    has_description.short_description = 'Есть описание'


class OrderProductInline(admin.TabularInline):
    """Inline для товаров в заказе"""
    model = OrderProduct
    extra = 0
    fields = ('product', 'quantity', 'price')
    autocomplete_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'get_user_name', 'total_price', 'get_delivery_method', 'get_payment_method', 'created_at')
    list_filter = ('delivery_method', 'payment_method', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'city', 'street', 'house')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderProductInline]
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Адрес доставки', {
            'fields': ('city', 'street', 'house', 'flat', 'index')
        }),
        ('Оплата и доставка', {
            'fields': ('total_price', 'delivery_method', 'payment_method', 'price_for_delivery')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email пользователя'
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_user_name.short_description = 'Имя пользователя'
    
    def get_delivery_method(self, obj):
        return obj.delivery_method.name if obj.delivery_method else '-'
    get_delivery_method.short_description = 'Способ доставки'
    
    def get_payment_method(self, obj):
        return obj.payment_method.name if obj.payment_method else '-'
    get_payment_method.short_description = 'Способ оплаты'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'delivery_method', 'payment_method')

