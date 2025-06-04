# exhibition_service/config/admin.py
# exhibition_service/config/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from datetime import datetime, timedelta
import json

# Импорты моделей (пока что основные)
from apps.users.models import User, UserProfile
from apps.exhibitions.models import Category, Exhibition
from apps.companies.models import Company
from apps.core.models import SiteSettings


class ExhibitionAdminSite(admin.AdminSite):
    """Кастомная админка для платформы выставок"""
    
    site_header = 'ПП Expo - Панель управления'
    site_title = 'ПП Expo Admin'
    index_title = 'Добро пожаловать в панель управления'
    
    def get_urls(self):
        """Добавляем кастомные URL для дашборда"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('statistics/', self.admin_view(self.statistics_view), name='statistics'),
            path('moderation/', self.admin_view(self.moderation_view), name='moderation'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Главная страница дашборда"""
        # Простая статистика для начала
        stats = {
            'users_total': User.objects.count(),
            'users_today': User.objects.filter(created_at__date=timezone.now().date()).count(),
            'exhibitions_total': Exhibition.objects.count(),
            'exhibitions_published': Exhibition.objects.filter(status='published').count(),
            'companies_total': Company.objects.count(),
            'companies_active': Company.objects.filter(status='active').count(),
        }
        
        context = {
            'title': 'Дашборд',
            'stats': stats,
        }
        
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
    def statistics_view(self, request):
        """Страница статистики"""
        context = {
            'title': 'Статистика',
        }
        return TemplateResponse(request, 'admin/statistics.html', context)
    
    def moderation_view(self, request):
        """Страница модерации"""
        context = {
            'title': 'Модерация',
        }
        return TemplateResponse(request, 'admin/moderation.html', context)


# Создаем экземпляр кастомной админки
admin_site = ExhibitionAdminSite(name='exhibition_admin')

# Базовая регистрация моделей (пока простые)

@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'is_email_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_email_verified', 'is_active', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Полное имя'


@admin.register(Exhibition, site=admin_site)
class ExhibitionAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'category', 'status', 'start_date', 'city']
    list_filter = ['status', 'category', 'start_date', 'city']
    search_fields = ['title', 'description', 'city']
    ordering = ['-created_at']


@admin.register(Company, site=admin_site)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'category', 'status', 'city', 'is_verified']
    list_filter = ['status', 'category', 'is_verified', 'city']
    search_fields = ['name', 'description', 'city']
    ordering = ['-created_at']


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'sort_order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']


@admin.register(SiteSettings, site=admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'is_active']
    list_filter = ['setting_type', 'is_active']
    search_fields = ['key', 'description']
    ordering = ['key']