from django.contrib import admin
from .models import (
    Category, MainCategory, SubCategory, Product,
    ProductImage, ProductMeterage, Favourite
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_parent_display', 'has_image', 'created_at', 'updated_at')
    list_filter = ('parent', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'parent')
        }),
        ('Изображение', {
            'fields': ('image',),
            'description': 'Изображение только для главных категорий (без родителя)'
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_parent_display(self, obj):
        if obj.parent:
            return f"Подкатегория: {obj.parent.name}"
        return "Главная категория"
    get_parent_display.short_description = 'Тип категории'
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Есть изображение'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent')


@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'has_image', 'get_subcategories_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description')
        }),
        ('Изображение', {
            'fields': ('image',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Показываем только категории без родителя
        return super().get_queryset(request).filter(parent__isnull=True)
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Есть изображение'
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.count()
    get_subcategories_count.short_description = 'Количество подкатегорий'
    
    def save_model(self, request, obj, form, change):
        # Гарантируем, что parent всегда None
        obj.parent = None
        super().save_model(request, obj, form, change)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_main_category', 'description', 'created_at', 'updated_at')
    list_filter = ('parent', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'parent__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('parent', 'name', 'description')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Показываем только категории с родителем
        return super().get_queryset(request).filter(parent__isnull=False).select_related('parent')
    
    def get_main_category(self, obj):
        return obj.parent.name if obj.parent else '-'
    get_main_category.short_description = 'Главная категория'
    
    def save_model(self, request, obj, form, change):
        # Проверяем, что parent установлен
        if not obj.parent:
            from django.core.exceptions import ValidationError
            raise ValidationError("Подкатегория должна иметь родительскую категорию")
        super().save_model(request, obj, form, change)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_main', 'order')
    ordering = ('-is_main', 'order')


class ProductMeterageInline(admin.TabularInline):
    model = ProductMeterage
    extra = 1
    fields = ('value', 'is_active')
    ordering = ('value',)
    
    
class ProductFavouriteInline(admin.TabularInline):
    model = Favourite
    extra = 1
    fields = ('user',)
    ordering = ('-created_at',)
    can_delete = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_category_display', 'sku', 'price_per_meter', 'stock', 'is_active', 'created_at')
    list_filter = ('sub_category__parent', 'sub_category', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline, ProductMeterageInline, ProductFavouriteInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('sub_category', 'name', 'sku', 'description')
        }),
        ('Цена и наличие', {
            'fields': ('price_per_meter', 'stock', 'is_active')
        }),
        ('Производитель и страна производства', {
            'fields': ('manufacturer', 'country_of_origin')
        }),
        ('Количество ядер и материал проводника', {
            'fields': ('number_of_cores', 'conductor_material')
        }),
        ('Характеристики кабеля', {
            'fields': (
                'cable_cross_section', 'outer_insulation_material',
                'conductor_insulation_material', 'outer_sheath_material'
            )
        }),
        ('Дополнительные характеристики', {
            'fields': ('model_version', 'color')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_category_display(self, obj):
        if obj.sub_category.parent:
            return f"{obj.sub_category.parent.name} / {obj.sub_category.name}"
        return obj.sub_category.name
    get_category_display.short_description = 'Категория'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sub_category', 'sub_category__parent')
