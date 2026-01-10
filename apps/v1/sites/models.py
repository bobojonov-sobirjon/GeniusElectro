from django.db import models
from django.utils.translation import gettext_lazy as _


class Contact(models.Model):
    """Контактная информация"""
    zip_code = models.CharField(max_length=10, verbose_name='Индекс', null=True, blank=True)
    city = models.CharField(max_length=100, verbose_name='Город', null=False, blank=False)
    street = models.CharField(max_length=255, verbose_name='Улица', null=False, blank=False)
    building_number = models.CharField(max_length=20, verbose_name='Номер дома', null=False, blank=False)
    office_number = models.CharField(max_length=50, verbose_name='Номер офиса', null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон', null=False, blank=False)
    email = models.EmailField(verbose_name='Email', null=False, blank=False)
    working_hours_weekday = models.CharField(
        max_length=100,
        verbose_name='Режим работы (будни)',
        null=True,
        blank=True,
        help_text='Например: Пн - Пт: 9.00 - 18.00'
    )
    working_hours_weekend = models.CharField(
        max_length=100,
        verbose_name='Режим работы (выходные)',
        null=True,
        blank=True,
        help_text='Например: Сб - Вс: выходные'
    )
    map_iframe = models.TextField(
        verbose_name='Карта (iframe)',
        null=True,
        blank=True,
        help_text='HTML код для встраивания карты (iframe)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '01. Контактная информация'
        verbose_name_plural = '01. Контактная информация'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.city}, {self.street}, д. {self.building_number}"

    def get_full_address(self):
        """Получить полный адрес"""
        address_parts = []
        if self.zip_code:
            address_parts.append(self.zip_code)
        address_parts.append(f"г. {self.city}")
        address_parts.append(f"ул. {self.street}")
        address_parts.append(f"д. {self.building_number}")
        if self.office_number:
            address_parts.append(f"оф. {self.office_number}")
        return ", ".join(address_parts)


class Partner(models.Model):
    """Партнер"""
    image = models.ImageField(
        upload_to='partners/',
        verbose_name='Изображение',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '02. Партнер'
        verbose_name_plural = '02. Партнеры'
        ordering = ['-created_at']

    def __str__(self):
        return f"Партнер #{self.id}"


class Request(models.Model):
    """Заявка (Оставить заявку)"""
    name = models.CharField(max_length=255, verbose_name='Имя', null=False, blank=False)
    phone = models.CharField(max_length=20, verbose_name='Телефон', null=False, blank=False)
    email = models.EmailField(verbose_name='Email', null=True, blank=True)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)
    file = models.FileField(
        upload_to='requests/files/',
        verbose_name='Прикрепленный файл',
        null=True,
        blank=True,
        help_text='Документы для подбора кабеля и расчёта стоимости'
    )
    privacy_policy_agreed = models.BooleanField(
        default=False,
        verbose_name='Согласие с политикой конфиденциальности',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = '03. Заявка'
        verbose_name_plural = '03. Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка от {self.name} ({self.phone})"
