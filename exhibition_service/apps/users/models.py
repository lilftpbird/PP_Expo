# exhibition_service/apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import uuid
import secrets
from datetime import timedelta


class User(AbstractUser):
    """Кастомная модель пользователя"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Администратор')
        ORGANIZER = 'organizer', _('Организатор')
        VISITOR = 'visitor', _('Посетитель')
    
    # Основные поля
    email = models.EmailField(_('Email адрес'), unique=True)
    role = models.CharField(
        _('Роль'),
        max_length=20,
        choices=Role.choices,
        default=Role.VISITOR
    )
    
    # Личная информация
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    company_name = models.CharField(_('Название компании'), max_length=200, blank=True)
    position = models.CharField(_('Должность'), max_length=100, blank=True)
    
    # Подтверждение email
    is_email_verified = models.BooleanField(_('Email подтвержден'), default=False)
    email_verified_at = models.DateTimeField(_('Дата подтверждения email'), null=True, blank=True)
    
    # Согласие на обработку персональных данных
    gdpr_consent = models.BooleanField(_('Согласие на обработку персональных данных'), default=False)
    gdpr_consent_date = models.DateTimeField(_('Дата согласия на обработку данных'), null=True, blank=True)
    
    # Настройки уведомлений
    email_notifications = models.BooleanField(_('Email уведомления'), default=True)
    marketing_emails = models.BooleanField(_('Маркетинговые рассылки'), default=False)
    
    # Статистика
    last_activity = models.DateTimeField(_('Последняя активность'), null=True, blank=True)
    login_count = models.PositiveIntegerField(_('Количество входов'), default=0)
    
    # Служебные поля
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Поля для безопасности
    failed_login_attempts = models.PositiveIntegerField(_('Неудачные попытки входа'), default=0)
    locked_until = models.DateTimeField(_('Заблокирован до'), null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active', 'is_email_verified']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Устанавливаем username равным email если не задан
        if not self.username:
            self.username = self.email
        
        # Устанавливаем дату согласия GDPR
        if self.gdpr_consent and not self.gdpr_consent_date:
            self.gdpr_consent_date = timezone.now()
            
        super().save(*args, **kwargs)

    # Методы проверки ролей
    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    @property
    def is_visitor(self):
        return self.role == self.Role.VISITOR
    
    @property
    def can_create_exhibitions(self):
        """Может ли пользователь создавать выставки"""
        return self.is_organizer or self.is_admin_user
    
    @property
    def can_create_companies(self):
        """Может ли пользователь создавать компании"""
        return self.is_authenticated and self.is_email_verified
    
    @property
    def is_account_locked(self):
        """Заблокирован ли аккаунт"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    @property
    def days_since_registration(self):
        """Количество дней с регистрации"""
        return (timezone.now() - self.created_at).days
    
    @property
    def profile_completion_percentage(self):
        """Процент заполнения профиля"""
        fields_to_check = [
            'first_name', 'last_name', 'phone', 'company_name', 'position'
        ]
        filled_fields = sum(1 for field in fields_to_check if getattr(self, field))
        
        # Добавляем проверку профиля и аватара
        if hasattr(self, 'profile'):
            if self.profile.bio:
                filled_fields += 1
            if self.profile.avatar:
                filled_fields += 1
            total_fields = len(fields_to_check) + 2
        else:
            total_fields = len(fields_to_check)
        
        return int((filled_fields / total_fields) * 100)

    def get_full_name(self):
        """Полное имя пользователя"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email.split('@')[0]

    def get_short_name(self):
        """Короткое имя"""
        return self.first_name or self.email.split('@')[0]
    
    def get_initials(self):
        """Инициалы пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        else:
            return self.email[0].upper()

    def update_last_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

    def increment_login_count(self):
        """Увеличивает счетчик входов"""
        self.login_count += 1
        self.last_activity = timezone.now()
        self.failed_login_attempts = 0  # Сбрасываем неудачные попытки
        self.save(update_fields=['login_count', 'last_activity', 'failed_login_attempts'])

    def increment_failed_login(self):
        """Увеличивает счетчик неудачных попыток входа"""
        self.failed_login_attempts += 1
        
        # Блокируем аккаунт после 5 неудачных попыток
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def unlock_account(self):
        """Разблокирует аккаунт"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def verify_email(self):
        """Подтверждает email пользователя"""
        self.is_email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['is_email_verified', 'email_verified_at'])

    def send_verification_email(self, request=None):
        """Отправляет письмо с подтверждением email"""
        # Создаем или получаем токен подтверждения
        token, created = EmailVerificationToken.objects.get_or_create(
            user=self,
            is_used=False,
            defaults={
                'token': secrets.token_urlsafe(32),
                'expires_at': timezone.now() + timedelta(hours=24)
            }
        )
        
        # Если токен существует, но просрочен, создаем новый
        if not created and not token.is_valid:
            token.is_used = True
            token.save()
            token = EmailVerificationToken.objects.create(
                user=self,
                token=secrets.token_urlsafe(32),
                expires_at=timezone.now() + timedelta(hours=24)
            )
        
        # Отправляем email
        context = {
            'user': self,
            'token': token.token,
            'domain': settings.SITE_DOMAIN if hasattr(settings, 'SITE_DOMAIN') else 'localhost:8000',
            'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
        }
        
        subject = 'Подтверждение email - ПП Expo'
        html_message = render_to_string('users/emails/verification.html', context)
        
        try:
            send_mail(
                subject=subject,
                message='',  # Текстовая версия
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False

    def send_password_reset_email(self, request=None):
        """Отправляет письмо для сброса пароля"""
        # Деактивируем старые токены
        PasswordResetToken.objects.filter(
            user=self,
            is_used=False
        ).update(is_used=True)
        
        # Создаем новый токен
        token = PasswordResetToken.objects.create(
            user=self,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        # Отправляем email
        context = {
            'user': self,
            'token': token.token,
            'domain': settings.SITE_DOMAIN if hasattr(settings, 'SITE_DOMAIN') else 'localhost:8000',
            'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
        }
        
        subject = 'Восстановление пароля - ПП Expo'
        html_message = render_to_string('users/emails/password_reset.html', context)
        
        try:
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False

    def get_favorite_exhibitions(self):
        """Возвращает избранные выставки пользователя"""
        return self.favorite_exhibitions.filter(exhibition__status='published')

    def get_favorite_companies(self):
        """Возвращает избранные компании пользователя"""
        return self.favorite_companies.filter(company__is_active=True)

    def get_created_exhibitions(self):
        """Возвращает выставки, созданные пользователем"""
        if self.can_create_exhibitions:
            return self.organized_exhibitions.all()
        return []

    def get_created_companies(self):
        """Возвращает компании, созданные пользователем"""
        return self.created_companies.filter(is_active=True)


class UserProfile(models.Model):
    """Расширенный профиль пользователя"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name=_('Пользователь')
    )
    
    # Медиа
    avatar = models.ImageField(
        _('Аватар'), 
        upload_to='avatars/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 200x200 пикселей')
    )
    
    # Дополнительная информация
    bio = models.TextField(_('О себе'), blank=True, max_length=500)
    website = models.URLField(_('Веб-сайт'), blank=True)
    birth_date = models.DateField(_('Дата рождения'), blank=True, null=True)
    
    # Адрес
    country = models.CharField(_('Страна'), max_length=100, blank=True)
    city = models.CharField(_('Город'), max_length=100, blank=True)
    timezone = models.CharField(_('Часовой пояс'), max_length=50, blank=True, default='Europe/Moscow')
    
    # Для организаторов
    organization_name = models.CharField(_('Название организации'), max_length=200, blank=True)
    organization_description = models.TextField(_('Описание организации'), blank=True)
    organization_website = models.URLField(_('Сайт организации'), blank=True)
    organization_logo = models.ImageField(
        _('Логотип организации'), 
        upload_to='org_logos/', 
        blank=True, 
        null=True
    )
    
    # Социальные сети
    linkedin_url = models.URLField(_('LinkedIn'), blank=True)
    facebook_url = models.URLField(_('Facebook'), blank=True)
    twitter_url = models.URLField(_('Twitter'), blank=True)
    instagram_url = models.URLField(_('Instagram'), blank=True)
    
    # Настройки приватности
    show_email = models.BooleanField(_('Показывать email'), default=False)
    show_phone = models.BooleanField(_('Показывать телефон'), default=False)
    allow_messages = models.BooleanField(_('Разрешить сообщения'), default=True)
    
    # Настройки уведомлений  
    email_notifications = models.BooleanField(_('Email уведомления'), default=True)
    marketing_emails = models.BooleanField(_('Маркетинговые рассылки'), default=False)
    exhibition_reminders = models.BooleanField(_('Напоминания о выставках'), default=True)
    weekly_digest = models.BooleanField(_('Еженедельная сводка'), default=True)
    
    # Метаданные
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Профиль пользователя')
        verbose_name_plural = _('Профили пользователей')
        db_table = 'user_profiles'

    def __str__(self):
        return f"Профиль {self.user.email}"

    @property
    def has_avatar(self):
        """Есть ли аватар у пользователя"""
        return bool(self.avatar)

    @property
    def avatar_url(self):
        """URL аватара или заглушка"""
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def display_name(self):
        """Отображаемое имя"""
        return self.user.get_full_name()

    def get_social_links(self):
        """Возвращает список социальных ссылок"""
        links = []
        social_fields = {
            'linkedin_url': 'LinkedIn',
            'facebook_url': 'Facebook', 
            'twitter_url': 'Twitter',
            'instagram_url': 'Instagram'
        }
        
        for field, name in social_fields.items():
            url = getattr(self, field)
            if url:
                links.append({'name': name, 'url': url})
        
        return links


class EmailVerificationToken(models.Model):
    """Токены для подтверждения email"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='verification_tokens',
        verbose_name=_('Пользователь')
    )
    token = models.CharField(_('Токен'), max_length=64, unique=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Дата истечения'))
    is_used = models.BooleanField(_('Использован'), default=False)
    used_at = models.DateTimeField(_('Дата использования'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)

    class Meta:
        verbose_name = _('Токен подтверждения email')
        verbose_name_plural = _('Токены подтверждения email')
        db_table = 'email_verification_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Токен для {self.user.email}"

    @property
    def is_valid(self):
        """Проверяет, действителен ли токен"""
        return not self.is_used and timezone.now() < self.expires_at

    def use_token(self, ip_address=None):
        """Использует токен"""
        if self.is_valid:
            self.is_used = True
            self.used_at = timezone.now()
            self.ip_address = ip_address
            self.save(update_fields=['is_used', 'used_at', 'ip_address'])
            return True
        return False


class PasswordResetToken(models.Model):
    """Токены для сброса пароля"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='password_reset_tokens',
        verbose_name=_('Пользователь')
    )
    token = models.CharField(_('Токен'), max_length=64, unique=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Дата истечения'))
    is_used = models.BooleanField(_('Использован'), default=False)
    used_at = models.DateTimeField(_('Дата использования'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)

    class Meta:
        verbose_name = _('Токен сброса пароля')
        verbose_name_plural = _('Токены сброса пароля')
        db_table = 'password_reset_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Токен сброса для {self.user.email}"

    @property
    def is_valid(self):
        """Проверяет, действителен ли токен"""
        return not self.is_used and timezone.now() < self.expires_at

    def use_token(self, ip_address=None):
        """Использует токен"""
        if self.is_valid:
            self.is_used = True
            self.used_at = timezone.now()
            self.ip_address = ip_address
            self.save(update_fields=['is_used', 'used_at', 'ip_address'])
            return True
        return False


class UserActivity(models.Model):
    """Лог активности пользователей"""
    
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Вход в систему')
        LOGOUT = 'logout', _('Выход из системы')
        PROFILE_UPDATE = 'profile_update', _('Обновление профиля')
        PASSWORD_CHANGE = 'password_change', _('Смена пароля')
        EMAIL_VERIFICATION = 'email_verification', _('Подтверждение email')
        EXHIBITION_CREATE = 'exhibition_create', _('Создание выставки')
        COMPANY_CREATE = 'company_create', _('Создание компании')
        FAVORITE_ADD = 'favorite_add', _('Добавление в избранное')
        FAVORITE_REMOVE = 'favorite_remove', _('Удаление из избранного')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('Пользователь')
    )
    activity_type = models.CharField(
        _('Тип активности'),
        max_length=20,
        choices=ActivityType.choices
    )
    description = models.CharField(_('Описание'), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    metadata = models.JSONField(_('Дополнительные данные'), default=dict, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Активность пользователя')
        verbose_name_plural = _('Активность пользователей')
        db_table = 'user_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()}"

    @classmethod
    def log_activity(cls, user, activity_type, description='', request=None, **metadata):
        """Логирует активность пользователя"""
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )

    @staticmethod
    def get_client_ip(request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip