from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.v1.accounts.models import CustomUser


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название', null=False, blank=False)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    image = models.ImageField(upload_to='categories/', verbose_name='Изображение', null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='Родительская категория',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']


class MainCategory(Category):
    """Proxy модель для главных категорий (без родителя)"""
    
    class Meta:
        proxy = True
        verbose_name = '01. Основная категория'
        verbose_name_plural = '01. Основные категории'
    
    def save(self, *args, **kwargs):
        # Гарантируем, что parent всегда None для главных категорий
        self.parent = None
        super().save(*args, **kwargs)


class SubCategory(Category):
    """Proxy модель для подкатегорий (с родителем)"""
    
    class Meta:
        proxy = True
        verbose_name = '02. Подкатегория'
        verbose_name_plural = '02. Подкатегории'
    
    def save(self, *args, **kwargs):
        # Гарантируем, что parent всегда установлен для подкатегорий
        if not self.parent:
            raise ValueError("Подкатегория должна иметь родительскую категорию")
        super().save(*args, **kwargs)


class Product(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Поставщик',
        null=True,
        blank=True
    )
    sub_category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Подкатегория',
        limit_choices_to={'parent__isnull': False}  # Только подкатегории
    )
    name = models.CharField(max_length=500, verbose_name='Название', null=False, blank=False)
    sku = models.CharField(max_length=100, unique=True, verbose_name='Артикул', null=False, blank=False)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    price_per_meter = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за метр',
        null=False,
        blank=False
    )
    stock = models.PositiveIntegerField(default=0, verbose_name='Количество в наличии')
    manufacturer = models.CharField(max_length=255, verbose_name='Производитель', null=True, blank=True)
    country_of_origin = models.CharField(max_length=255, verbose_name='Страна производства', null=True, blank=True)
    number_of_cores = models.PositiveIntegerField(default=0, verbose_name='Количество ядер')
    conductor_material = models.CharField(max_length=255, verbose_name='Материал проводника', null=True, blank=True)
    cable_cross_section = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сечение кабеля, мм²',
        null=True,
        blank=True
    )
    outer_insulation_material = models.CharField(
        max_length=255,
        verbose_name='Материал внешней изоляции',
        null=True,
        blank=True
    )
    conductor_insulation_material = models.CharField(
        max_length=255,
        verbose_name='Материал изоляции проводника',
        null=True,
        blank=True
    )
    outer_sheath_material = models.CharField(
        max_length=255,
        verbose_name='Материал внешней оболочки',
        null=True,
        blank=True
    )
    model_version = models.CharField(
        max_length=255,
        verbose_name='Модель/исполнение',
        null=True,
        blank=True
    )
    color = models.CharField(
        max_length=100,
        verbose_name='Цвет',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        if self.sub_category.parent:
            return f"{self.sub_category.parent.name} / {self.sub_category.name} - {self.name}"
        return f"{self.sub_category.name} - {self.name}"

    class Meta:
        verbose_name = '03. Товар'
        verbose_name_plural = '03. Товары'
        ordering = ['-created_at']


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар'
    )
    image = models.ImageField(upload_to='products/images/', verbose_name='Изображение', null=False, blank=False)
    is_main = models.BooleanField(default=False, verbose_name='Главное изображение')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['-is_main', 'order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Изображение {self.id}"


class ProductMeterage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='meterages',
        verbose_name='Товар'
    )
    value = models.PositiveIntegerField(verbose_name='Метраж (м)', null=False, blank=False)
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Метраж товара'
        verbose_name_plural = 'Метражи товаров'
        ordering = ['value']
        unique_together = ['product', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.value} м"


class Favourite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Товар'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"
