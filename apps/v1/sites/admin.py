from django.contrib import admin
from django.utils.html import format_html
from .models import Contact, Partner, Request


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('get_full_address_display', 'phone', 'email', 'created_at', 'updated_at')
    list_filter = ('city', 'created_at', 'updated_at')
    search_fields = ('city', 'street', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Адрес', {
            'fields': ('zip_code', 'city', 'street', 'building_number', 'office_number')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email')
        }),
        ('Режим работы', {
            'fields': ('working_hours_weekday', 'working_hours_weekend')
        }),
        ('Карта', {
            'fields': ('map_iframe',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_address_display(self, obj):
        return obj.get_full_address()
    get_full_address_display.short_description = 'Полный адрес'


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_image_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'get_image_preview')
    
    fieldsets = (
        ('Изображение', {
            'fields': ('image', 'get_image_preview')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.image.url)
        return '-'
    get_image_preview.short_description = 'Превью изображения'


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'has_file', 'privacy_policy_agreed', 'created_at')
    list_filter = ('privacy_policy_agreed', 'created_at', 'updated_at')
    search_fields = ('name', 'phone', 'email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Контактная информация', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Дополнительная информация', {
            'fields': ('comment', 'file', 'privacy_policy_agreed')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = 'Есть файл'
