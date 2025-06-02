# exhibition_service/apps/users/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from functools import wraps
from .models import User

class RoleRequiredMiddleware:
    """Middleware для проверки ролей пользователей"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response

# Декораторы для проверки ролей
def role_required(allowed_roles):
    """
    Декоратор для проверки роли пользователя
    Args:
        allowed_roles (list): Список разрешенных ролей
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Необходима авторизация.')
                return redirect('users:login')
            
            user_role = request.user.role
            if user_role not in allowed_roles and not request.user.is_superuser:
                messages.error(request, 'У вас недостаточно прав для доступа к этой странице.')
                return redirect('core:index')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def admin_required(view_func):
    """Декоратор для проверки прав администратора"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Необходима авторизация.')
            return redirect('users:login')
        
        if not request.user.is_admin_user:
            messages.error(request, 'Доступ только для администраторов.')
            return redirect('core:index')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def organizer_required(view_func):
    """Декоратор для проверки прав организатора"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Необходима авторизация.')
            return redirect('users:login')
        
        if not request.user.is_organizer_user:
            messages.error(request, 'Доступ только для организаторов.')
            return redirect('core:index')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def visitor_required(view_func):
    """Декоратор для проверки прав посетителя"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Необходима авторизация.')
            return redirect('users:login')
        
        if not request.user.is_visitor_user:
            messages.error(request, 'Доступ только для посетителей.')
            return redirect('core:index')
        
        return view_func(request, *args, **kwargs)
    return wrapper

# exhibition_service/apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import uuid

class User(AbstractUser):
    """Кастомная модель пользователя с ролями"""
    
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('organizer', 'Организатор'),
        ('visitor', 'Посетитель'),
    ]
    
    email = models.EmailField('Email', unique=True)
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='visitor')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    
    # Поля для подтверждения email
    is_email_verified = models.BooleanField('Email подтвержден', default=False)
    email_verification_token = models.UUIDField('Токен подтверждения email', default=uuid.uuid4)
    
    # Поля для восстановления пароля
    password_reset_token = models.UUIDField('Токен сброса пароля', null=True, blank=True)
    password_reset_expires = models.DateTimeField('Срок действия токена сброса', null=True, blank=True)
    
    # Согласие на обработку персональных данных
    personal_data_consent = models.BooleanField('Согласие на обработку персональных данных', default=False)
    personal_data_consent_date = models.DateTimeField('Дата согласия', null=True, blank=True)
    
    # Дополнительные поля
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'users_user'
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    # Методы проверки ролей
    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_organizer_user(self):
        return self.role == 'organizer' or self.is_admin_user
    
    @property
    def is_visitor_user(self):
        return self.role == 'visitor' or self.is_organizer_user
    
    def send_verification_email(self):
        """Отправка письма с подтверждением email"""
        subject = 'Подтверждение email'
        message = render_to_string('users/emails/verification.html', {
            'user': self,
            'token': self.email_verification_token,
            'domain': settings.SITE_DOMAIN,
            'protocol': 'https' if settings.USE_HTTPS else 'http',
        })
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=message,
            fail_silently=False,
        )
    
    def send_password_reset_email(self):
        """Отправка письма для сброса пароля"""
        self.password_reset_token = uuid.uuid4()
        self.password_reset_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save(update_fields=['password_reset_token', 'password_reset_expires'])
        
        subject = 'Восстановление пароля'
        message = render_to_string('users/emails/password_reset.html', {
            'user': self,
            'token': self.password_reset_token,
            'domain': settings.SITE_DOMAIN,
            'protocol': 'https' if settings.USE_HTTPS else 'http',
        })
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=message,
            fail_silently=False,
        )
