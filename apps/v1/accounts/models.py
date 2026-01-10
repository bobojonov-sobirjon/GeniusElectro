from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import secrets


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, unique=True, verbose_name='Номер телефона')
    email = models.EmailField(unique=True, verbose_name='Email')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.TextField(verbose_name='Улица')
    flat = models.CharField(max_length=10, verbose_name='Квартира')
    house = models.CharField(max_length=10, verbose_name='Дом')
    index = models.CharField(max_length=10, verbose_name='Индекс')
    is_email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


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
