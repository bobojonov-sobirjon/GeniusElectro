from django.db import models

from django.contrib.auth.models import AbstractUser, BaseUserManager

from django.utils import timezone

from django.conf import settings

import secrets





class CustomUserManager(BaseUserManager):

    """Custom user manager where email is the unique identifier"""

    

    def create_user(self, email, password=None, **extra_fields):

        """Create and save a regular user with the given email and password"""

        if not email:

            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user

    

    def create_superuser(self, email, password=None, **extra_fields):

        """Create and save a superuser with the given email and password"""

        extra_fields.setdefault('is_staff', True)

        extra_fields.setdefault('is_superuser', True)

        extra_fields.setdefault('is_email_verified', True)

        

        if extra_fields.get('is_staff') is not True:

            raise ValueError('Superuser must have is_staff=True.')

        if extra_fields.get('is_superuser') is not True:

            raise ValueError('Superuser must have is_superuser=True.')

        

        return self.create_user(email, password, **extra_fields)





class CustomUser(AbstractUser):

    first_name = models.CharField(max_length=150, verbose_name='Имя')

    last_name = models.CharField(max_length=150, verbose_name='Фамилия')

    phone = models.CharField(max_length=20, unique=True, verbose_name='Номер телефона')

    email = models.EmailField(unique=True, verbose_name='Email')

    city = models.CharField(max_length=100, verbose_name='Город', null=True, blank=True)

    street = models.TextField(verbose_name='Улица', null=True, blank=True)

    flat = models.CharField(max_length=10, verbose_name='Квартира', null=True, blank=True)

    house = models.CharField(max_length=10, verbose_name='Дом', null=True, blank=True)

    index = models.CharField(max_length=10, verbose_name='Индекс', null=True, blank=True)

    is_email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')



    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    

    objects = CustomUserManager()



    class Meta:

        verbose_name = 'Пользователь'

        verbose_name_plural = 'Пользователи'

        ordering = ['-created_at']



    def __str__(self):

        return f"{self.first_name} {self.last_name} ({self.email})"





# Proxy models for CustomUser

class BuyerUser(CustomUser):

    """Proxy model for Buyer users"""

    class Meta:

        proxy = True

        verbose_name = 'Покупатель'

        verbose_name_plural = '01. Покупатели'





class SupplierUser(CustomUser):

    """Proxy model for Supplier users"""

    class Meta:

        proxy = True

        verbose_name = 'Поставщик'

        verbose_name_plural = '02. Поставщики'





class EmailVerificationToken(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_verification_tokens', verbose_name='Пользователь')

    token = models.CharField(max_length=64, unique=True, verbose_name='Токен')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    expires_at = models.DateTimeField(verbose_name='Истекает')

    is_used = models.BooleanField(default=False, verbose_name='Использован')



    class Meta:

        verbose_name = 'Токен подтверждения email'

        verbose_name_plural = 'Токены подтверждения email'

        ordering = ['-created_at']



    def __str__(self):

        return f"Token for {self.user.email}"



    @staticmethod

    def generate_token():

        return secrets.token_urlsafe(32)



    def is_expired(self):

        return timezone.now() > self.expires_at





class PasswordResetToken(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_tokens', verbose_name='Пользователь')

    token = models.CharField(max_length=64, unique=True, verbose_name='Токен')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    expires_at = models.DateTimeField(verbose_name='Истекает')

    is_used = models.BooleanField(default=False, verbose_name='Использован')



    class Meta:

        verbose_name = 'Токен сброса пароля'

        verbose_name_plural = 'Токены сброса пароля'

        ordering = ['-created_at']



    def __str__(self):

        return f"Password reset token for {self.user.email}"



    @staticmethod

    def generate_token():

        return secrets.token_urlsafe(32)



    def is_expired(self):

        return timezone.now() > self.expires_at





# Company models

class LegalFormType(models.TextChoices):

    """Choices for organizational legal form"""

    OOO = 'ООО', 'ООО'

    PAO = 'ПАО', 'ПАО'

    AO = 'АО', 'АО'

    IP = 'ИП', 'ИП'

    ZAO = 'ЗАО', 'ЗАО'





class ActsOnBasisType(models.TextChoices):

    """Choices for acts on basis"""

    USTAV = 'Устав', 'Устав'

    DOVERENNOST = 'Доверенность', 'Доверенность'

    SVIDETELSTVO_IP = 'Свидетельство о регистрации ИП', 'Свидетельство о регистрации ИП'





class Company(models.Model):

    """Company model with all required fields"""

    

    # User relationship

    user = models.ForeignKey(

        CustomUser,

        on_delete=models.CASCADE,

        related_name='companies',

        verbose_name='Пользователь',

        null=True,

        blank=True

    )

    

    # Основная информация о компании

    name_company = models.CharField(max_length=255, verbose_name='Название компании')

    organizational_legal_form = models.CharField(

        max_length=100,

        choices=LegalFormType.choices,

        verbose_name='Организационно-правовая форма',

        null=True,

        blank=True

    )

    abbreviated_name = models.CharField(

        max_length=255,

        verbose_name='Сокращенное наименование организации',

        null=True,

        blank=True

    )

    full_name = models.CharField(

        max_length=500,

        verbose_name='Полное наименование организации',

        null=True,

        blank=True

    )

    inn = models.CharField(

        max_length=12,

        verbose_name='ИНН',

        help_text='10 цифр для юр. лиц, 12 цифр для ИП',

        null=True,

        blank=True

    )

    ogrn_ogrnip = models.CharField(

        max_length=15,

        verbose_name='ОГРН/ОГРНИП',

        help_text='13 цифр для юр. лиц, 15 цифр для ИП',

        null=True,

        blank=True

    )

    kpp = models.CharField(

        max_length=9,

        verbose_name='КПП',

        help_text='9 цифр',

        null=True,

        blank=True

    )

    okpo = models.CharField(

        max_length=10,

        verbose_name='ОКПО',

        help_text='8 или 10 цифр',

        null=True,

        blank=True

    )

    registration_date = models.DateField(

        verbose_name='Дата регистрации',

        null=True,

        blank=True

    )

    

    # Юридический адрес

    legal_index = models.CharField(

        max_length=6,

        verbose_name='Индекс (юридический)',

        null=True,

        blank=True

    )

    legal_region = models.CharField(

        max_length=255,

        verbose_name='Регион/Область (юридический)',

        null=True,

        blank=True

    )

    legal_city = models.CharField(

        max_length=255,

        verbose_name='Город/Населенный пункт (юридический)',

        null=True,

        blank=True

    )

    legal_street = models.CharField(

        max_length=255,

        verbose_name='Улица (юридический)',

        null=True,

        blank=True

    )

    legal_house = models.CharField(

        max_length=50,

        verbose_name='Дом (юридический)',

        null=True,

        blank=True

    )

    legal_building = models.CharField(

        max_length=50,

        verbose_name='Корпус/Строение (юридический)',

        null=True,

        blank=True

    )

    legal_office = models.CharField(

        max_length=50,

        verbose_name='Офис/Помещение (юридический)',

        null=True,

        blank=True

    )

    

    # Фактический адрес

    matches_legal_address = models.BooleanField(

        default=False,

        verbose_name='Совпадает с юридическим адресом'

    )

    actual_index = models.CharField(

        max_length=6,

        verbose_name='Индекс (фактический)',

        null=True,

        blank=True

    )

    actual_region = models.CharField(

        max_length=255,

        verbose_name='Регион/Область (фактический)',

        null=True,

        blank=True

    )

    actual_city = models.CharField(

        max_length=255,

        verbose_name='Город/Населенный пункт (фактический)',

        null=True,

        blank=True

    )

    actual_street = models.CharField(

        max_length=255,

        verbose_name='Улица (фактический)',

        null=True,

        blank=True

    )

    actual_house = models.CharField(

        max_length=50,

        verbose_name='Дом (фактический)',

        null=True,

        blank=True

    )

    actual_building = models.CharField(

        max_length=50,

        verbose_name='Корпус/Строение (фактический)',

        null=True,

        blank=True

    )

    actual_office = models.CharField(

        max_length=50,

        verbose_name='Офис/Помещение (фактический)',

        null=True,

        blank=True

    )

    

    # Банковские реквизиты

    bank_name = models.CharField(

        max_length=255,

        verbose_name='Наименование банка',

        null=True,

        blank=True

    )

    bic = models.CharField(

        max_length=50,

        verbose_name='БИК',

        null=True,

        blank=True

    )

    settlement_account = models.CharField(

        max_length=20,

        verbose_name='Расчетный счет',

        help_text='20 цифр',

        null=True,

        blank=True

    )

    correspondent_account = models.CharField(

        max_length=20,

        verbose_name='Корреспондентский счет',

        help_text='20 цифр',

        null=True,

        blank=True

    )

    

    # Контактная информация

    contact_person_full_name = models.CharField(

        max_length=255,

        verbose_name='ФИО контактного лица',

        null=True,

        blank=True

    )

    position = models.CharField(

        max_length=255,

        verbose_name='Должность',

        null=True,

        blank=True

    )

    phone_number = models.CharField(

        max_length=20,

        verbose_name='Номер телефона',

        null=True,

        blank=True

    )

    email = models.EmailField(

        verbose_name='E-mail',

        null=True,

        blank=True

    )

    

    # Данные руководителя

    director_full_name = models.CharField(

        max_length=255,

        verbose_name='ФИО руководителя полностью',

        null=True,

        blank=True

    )

    director_position = models.CharField(

        max_length=255,

        verbose_name='Должность руководителя',

        null=True,

        blank=True

    )

    acts_on_basis = models.CharField(

        max_length=255,

        choices=ActsOnBasisType.choices,

        verbose_name='Действует на основании',

        null=True,

        blank=True

    )

    

    # Timestamps

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    

    class Meta:

        verbose_name = 'Компания'

        verbose_name_plural = '03. Компании'

        ordering = ['-created_at']

    

    def __str__(self):

        return self.name_company


class CompanyDocument(models.Model):
    """Model for storing company documents with separate file fields"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Компания'
    )
    
    # Document files
    tin_certificate = models.FileField(
        upload_to='companies/documents/tin/',
        verbose_name='Свидетельство ИНН',
        null=True,
        blank=True
    )
    ogrn_certificate = models.FileField(
        upload_to='companies/documents/ogrn/',
        verbose_name='Свидетельство ОГРН/ОГРНИП',
        null=True,
        blank=True
    )
    charter = models.FileField(
        upload_to='companies/documents/charter/',
        verbose_name='Устав (для юр. лиц)',
        null=True,
        blank=True
    )
    director_appointment = models.FileField(
        upload_to='companies/documents/director/',
        verbose_name='Документ о назначении руководителя',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Документ компании'
        verbose_name_plural = 'Документы компаний'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Документы компании: {self.company.name_company}"
