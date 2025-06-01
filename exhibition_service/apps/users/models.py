from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Кастомная модель пользователя"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Администратор')
        ORGANIZER = 'organizer', _('Организатор')
        VISITOR = 'visitor', _('Посетитель')
    
    email = models.EmailField(_('Email адрес'), unique=True)
    role = models.CharField(
        _('Роль'),
        max_length=20,
        choices=Role.choices,
        default=Role.VISITOR
    )
    is_email_verified = models.BooleanField(_('Email подтвержден'), default=False)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    company_name = models.CharField(_('Название компании'), max_length=200, blank=True)
    position = models.CharField(_('Должность'), max_length=100, blank=True)
    gdpr_consent = models.BooleanField(_('Согласие на обработку персональных данных'), default=False)
    gdpr_consent_date = models.DateTimeField(_('Дата согласия на обработку данных'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        db_table = 'users'

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    @property
    def is_visitor(self):
        return self.role == self.Role.VISITOR

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class UserProfile(models.Model):
    """Профиль пользователя с дополнительной информацией"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(_('Аватар'), upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(_('О себе'), blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)
    
    # Для организаторов
    organization_name = models.CharField(_('Название организации'), max_length=200, blank=True)
    organization_description = models.TextField(_('Описание организации'), blank=True)
    organization_website = models.URLField(_('Сайт организации'), blank=True)
    organization_logo = models.ImageField(_('Логотип организации'), upload_to='org_logos/', blank=True, null=True)
    
    # Настройки уведомлений
    email_notifications = models.BooleanField(_('Email уведомления'), default=True)
    marketing_emails = models.BooleanField(_('Маркетинговые рассылки'), default=False)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Профиль пользователя')
        verbose_name_plural = _('Профили пользователей')
        db_table = 'user_profiles'

    def __str__(self):
        return f"Профиль {self.user.email}"


class EmailVerificationToken(models.Model):
    """Токены для подтверждения email"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(_('Токен'), max_length=64, unique=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Дата истечения'))
    is_used = models.BooleanField(_('Использован'), default=False)

    class Meta:
        verbose_name = _('Токен подтверждения email')
        verbose_name_plural = _('Токены подтверждения email')
        db_table = 'email_verification_tokens'

    def __str__(self):
        return f"Токен для {self.user.email}"

    @property
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at


class PasswordResetToken(models.Model):
    """Токены для сброса пароля"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(_('Токен'), max_length=64, unique=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Дата истечения'))
    is_used = models.BooleanField(_('Использован'), default=False)

    class Meta:
        verbose_name = _('Токен сброса пароля')
        verbose_name_plural = _('Токены сброса пароля')
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f"Токен сброса для {self.user.email}"

    @property
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at