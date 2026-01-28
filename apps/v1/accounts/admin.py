from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from django.contrib.auth.models import Group

from django.contrib.sites.models import Site

from .models import (

    CustomUser, BuyerUser, SupplierUser,

    EmailVerificationToken, PasswordResetToken,

    Company, CompanyDocument

)



try:

    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    admin.site.unregister(BlacklistedToken)

    admin.site.unregister(OutstandingToken)

except:

    pass



admin.site.unregister(Site)





# Hide CustomUser from admin

# CustomUser will not be registered, only proxy models will be shown





@admin.register(BuyerUser)

class BuyerUserAdmin(BaseUserAdmin):

    list_display = ('email', 'first_name', 'last_name', 'phone', 'is_email_verified', 'created_at')

    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'created_at')

    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')

    ordering = ('-created_at',)

    

    fieldsets = (

        (None, {'fields': ('email', 'username', 'password')}),

        ('Личная информация', {'fields': ('first_name', 'last_name', 'phone')}),

        ('Адрес', {'fields': ('city', 'street', 'flat', 'house', 'index')}),

        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),

        ('Важные даты', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),

        ('Подтверждение', {'fields': ('is_email_verified',)}),

    )

    

    add_fieldsets = (

        (None, {

            'classes': ('wide',),

            'fields': ('email', 'username', 'first_name', 'last_name', 'phone', 'password1', 'password2'),

        }),

    )

    

    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')

    def get_queryset(self, request):
        """
        Показывать здесь только пользователей, которые входят в группу 'Buyer'.
        """
        qs = super().get_queryset(request)
        return qs.filter(groups__name='Buyer').distinct()





@admin.register(SupplierUser)

class SupplierUserAdmin(BaseUserAdmin):

    list_display = ('email', 'first_name', 'last_name', 'phone', 'is_email_verified', 'created_at')

    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'created_at')

    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')

    ordering = ('-created_at',)

    

    fieldsets = (

        (None, {'fields': ('email', 'username', 'password')}),

        ('Личная информация', {'fields': ('first_name', 'last_name', 'phone')}),

        ('Адрес', {'fields': ('city', 'street', 'flat', 'house', 'index')}),

        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),

        ('Важные даты', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),

        ('Подтверждение', {'fields': ('is_email_verified',)}),

    )

    

    add_fieldsets = (

        (None, {

            'classes': ('wide',),

            'fields': ('email', 'username', 'first_name', 'last_name', 'phone', 'password1', 'password2'),

        }),

    )

    

    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')

    def get_queryset(self, request):
        """
        Показывать здесь только пользователей, которые входят в группу 'Supplier'.
        """
        qs = super().get_queryset(request)
        return qs.filter(groups__name='Supplier').distinct()





# @admin.register(EmailVerificationToken)

class EmailVerificationTokenAdmin(admin.ModelAdmin):

    list_display = ('user', 'token', 'is_used', 'expires_at', 'created_at')

    list_filter = ('is_used', 'created_at', 'expires_at')

    search_fields = ('user__email', 'token')

    readonly_fields = ('token', 'created_at')





# @admin.register(PasswordResetToken)

class PasswordResetTokenAdmin(admin.ModelAdmin):

    list_display = ('user', 'token', 'is_used', 'expires_at', 'created_at')

    list_filter = ('is_used', 'created_at', 'expires_at')

    search_fields = ('user__email', 'token')

    readonly_fields = ('token', 'created_at')





class CompanyDocumentInline(admin.TabularInline):

    """Inline admin for Company documents"""

    model = CompanyDocument
    extra = 0
    # Use real file fields from CompanyDocument model
    fields = ('tin_certificate', 'ogrn_certificate', 'charter', 'director_appointment', 'created_at')
    readonly_fields = ('created_at',)





@admin.register(Company)

class CompanyAdmin(admin.ModelAdmin):

    list_display = ('name_company', 'user', 'inn', 'ogrn_ogrnip', 'contact_person_full_name', 'phone_number', 'created_at')

    list_filter = ('organizational_legal_form', 'matches_legal_address', 'created_at')

    search_fields = ('name_company', 'abbreviated_name', 'full_name', 'inn', 'ogrn_ogrnip', 'contact_person_full_name', 'phone_number', 'email', 'user__email', 'user__first_name', 'user__last_name')

    readonly_fields = ('created_at', 'updated_at')

    inlines = [CompanyDocumentInline]

    

    fieldsets = (

        ('Пользователь', {

            'fields': ('user',)

        }),

        ('Основная информация о компании', {

            'fields': (

                'name_company', 'organizational_legal_form', 'abbreviated_name', 'full_name',

                'inn', 'ogrn_ogrnip', 'kpp', 'okpo', 'registration_date'

            )

        }),

        ('Юридический адрес', {

            'fields': (

                'legal_index', 'legal_region', 'legal_city', 'legal_street',

                'legal_house', 'legal_building', 'legal_office'

            )

        }),

        ('Фактический адрес', {

            'fields': (

                'matches_legal_address',

                'actual_index', 'actual_region', 'actual_city', 'actual_street',

                'actual_house', 'actual_building', 'actual_office'

            )

        }),

        ('Банковские реквизиты', {

            'fields': ('bank_name', 'bic', 'settlement_account', 'correspondent_account')

        }),

        ('Контактная информация', {

            'fields': ('contact_person_full_name', 'position', 'phone_number', 'email')

        }),

        ('Данные руководителя', {

            'fields': ('director_full_name', 'director_position', 'acts_on_basis')

        }),

        ('Системная информация', {

            'fields': ('created_at', 'updated_at'),

            'classes': ('collapse',)

        }),

    )





# @admin.register(CompanyDocument)

class CompanyDocumentAdmin(admin.ModelAdmin):

    list_display = ('company', 'document_type', 'file', 'created_at')

    list_filter = ('document_type', 'created_at')

    search_fields = ('company__name_company', 'document_type')

    readonly_fields = ('created_at',)





admin.site.site_header = 'Genius Electronics'

admin.site.site_title = 'Genius Electronics'

admin.site.index_title = 'Администрирование Genius Electronics'

