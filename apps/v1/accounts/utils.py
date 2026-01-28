import logging

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import EmailVerificationToken, PasswordResetToken

logger = logging.getLogger(__name__)


def _email_debug_context():
    """
    Safe email configuration snapshot for logs (no passwords/tokens).
    """
    return {
        "EMAIL_BACKEND": getattr(settings, "EMAIL_BACKEND", None),
        "EMAIL_HOST": getattr(settings, "EMAIL_HOST", None),
        "EMAIL_PORT": getattr(settings, "EMAIL_PORT", None),
        "EMAIL_USE_TLS": getattr(settings, "EMAIL_USE_TLS", None),
        "EMAIL_USE_SSL": getattr(settings, "EMAIL_USE_SSL", None),
        "EMAIL_HOST_USER": getattr(settings, "EMAIL_HOST_USER", None),
        "DEFAULT_FROM_EMAIL": getattr(settings, "DEFAULT_FROM_EMAIL", None),
        "FRONTEND_URL": getattr(settings, "FRONTEND_URL", None),
        "DEBUG": getattr(settings, "DEBUG", None),
    }


def send_verification_email(user, token):
    verification_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/verify-email/?token={token}"
    
    subject = 'Подтверждение регистрации'
    message = f"""
Здравствуйте, {user.first_name}!

Спасибо за регистрацию в GeniusElectro.

Для подтверждения вашего email адреса, пожалуйста, перейдите по следующей ссылке:
{verification_url}

Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

С уважением,
Команда GeniusElectro
"""

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(
            "Verification email sent_count=%s recipient=%s ctx=%s",
            sent_count,
            user.email,
            _email_debug_context(),
        )
        return sent_count
    except Exception:
        logger.exception(
            "Verification email send failed recipient=%s ctx=%s",
            getattr(user, "email", None),
            _email_debug_context(),
        )
        raise


def send_password_reset_email(user, token):
    reset_url = f"{settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'}/reset-password/?token={token}"
    
    subject = 'Сброс пароля'
    message = f"""
Здравствуйте, {user.first_name}!

Вы запросили сброс пароля для вашего аккаунта.

Для сброса пароля перейдите по следующей ссылке:
{reset_url}

Эта ссылка действительна в течение 24 часов.

Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.

С уважением,
Команда GeniusElectro
"""

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(
            "Password reset email sent_count=%s recipient=%s ctx=%s",
            sent_count,
            user.email,
            _email_debug_context(),
        )
        return sent_count
    except Exception:
        logger.exception(
            "Password reset email send failed recipient=%s ctx=%s",
            getattr(user, "email", None),
            _email_debug_context(),
        )
        raise


def create_email_verification_token(user):
    token = EmailVerificationToken.generate_token()
    expires_at = timezone.now() + timedelta(days=1)
    
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
    
    verification_token = EmailVerificationToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    
    return verification_token


def create_password_reset_token(user):
    token = PasswordResetToken.generate_token()
    expires_at = timezone.now() + timedelta(hours=24)
    
    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
    
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    
    return reset_token

