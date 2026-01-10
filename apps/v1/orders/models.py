from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DeliveryMethod(models.Model):
    """Способ доставки"""
    name = models.CharField(max_length=255, verbose_name='Название', null=False, blank=False)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '01. Способ доставки'
        verbose_name_plural = '01. Способы доставки'
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentMethod(models.Model):
    """Способ оплаты"""
    name = models.CharField(max_length=255, verbose_name='Название', null=False, blank=False)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '02. Способ оплаты'
        verbose_name_plural = '02. Способы оплаты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Заказ"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь'
    )
    city = models.CharField(max_length=100, verbose_name='Город', null=False, blank=False)
    street = models.TextField(verbose_name='Улица', null=False, blank=False)
    house = models.CharField(max_length=10, verbose_name='Дом', null=False, blank=False)
    flat = models.CharField(max_length=10, verbose_name='Квартира', null=True, blank=True)
    index = models.CharField(max_length=10, verbose_name='Индекс', null=True, blank=True)
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость',
        null=False,
        blank=False
    )
    delivery_method = models.ForeignKey(
        DeliveryMethod,
        on_delete=models.SET_NULL,
        related_name='orders',
        verbose_name='Способ доставки',
        null=True,
        blank=True
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        related_name='orders',
        verbose_name='Способ оплаты',
        null=True,
        blank=True
    )
    price_for_delivery = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Стоимость доставки',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '03. Заказ'
        verbose_name_plural = '03. Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} - {self.user.email} ({self.total_price} руб.)"


class OrderProduct(models.Model):
    """Товар в заказе"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_products',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='order_products',
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество', null=False, blank=False, default=1)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказах'
        ordering = ['-created_at']
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.order} - {self.product.name} (x{self.quantity})"
