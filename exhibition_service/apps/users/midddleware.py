# exhibition_service/apps/users/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from functools import wraps


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
        
        if not (request.user.is_organizer or request.user.is_admin_user):
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
        
        if not (request.user.is_visitor or request.user.is_organizer or request.user.is_admin_user):
            messages.error(request, 'Доступ только для зарегистрированных пользователей.')
            return redirect('core:index')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def email_verified_required(view_func):
    """Декоратор для проверки подтверждения email"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Необходима авторизация.')
            return redirect('users:login')
        
        if not request.user.is_email_verified:
            messages.warning(request, 'Для доступа к этой функции необходимо подтвердить email.')
            return redirect('users:profile')
        
        return view_func(request, *args, **kwargs)
    return wrapper