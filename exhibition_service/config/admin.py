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

# Импорты всех моделей
from apps.users.models import User, UserProfile, EmailVerificationToken, PasswordResetToken, UserActivity
from apps.exhibitions.models import (
    Category, Exhibition, ExhibitionTag, ExhibitionImage, ExhibitionDocument,
    ExhibitionSchedule, ExhibitionSpeaker, ExhibitionSponsor, ExhibitionRegistration,
    ExhibitionAnalytics, FavoriteExhibition
)
from apps.companies.models import (
    Company, CompanyTag, CompanyProduct, CompanyGallery, CompanyReview,
    ExhibitionParticipant, CompanyContact, CompanyAnalytics, CompanyCertificate,
    FavoriteCompany
)
from apps.subscriptions.models import SubscriptionPlan, Subscription, Payment, Invoice
from apps.core.models import (
    Analytics, ViewHistory, Notification, SiteSettings, ContactMessage
)


class ExhibitionAdminSite(admin.AdminSite):
    """Кастомная админка для платформы выставок"""
    
    site_header = 'ПП Expo - Панель управления'
    site_title = 'ПП Expo Admin'
    index_title = 'Добро пожаловать в панель управления'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('statistics/', self.admin_view(self.statistics_view), name='statistics'),
            path('moderation/', self.admin_view(self.moderation_view), name='moderation'),
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
            path('users-export/', self.admin_view(self.users_export_view), name='users_export'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Главная страница дашборда"""
        # Общая статистика
        stats = {
            'users_total': User.objects.count(),
            'users_today': User.objects.filter(created_at__date=timezone.now().date()).count(),
            'users_verified': User.objects.filter(is_email_verified=True).count(),
            'exhibitions_total': Exhibition.objects.count(),
            'exhibitions_published': Exhibition.objects.filter(status='published').count(),
            'exhibitions_pending': Exhibition.objects.filter(status='pending').count(),
            'companies_total': Company.objects.count(),
            'companies_active': Company.objects.filter(status='active').count(),
            'companies_pending': Company.objects.filter(status='pending').count(),
            'registrations_total': ExhibitionRegistration.objects.count(),
            'registrations_today': ExhibitionRegistration.objects.filter(created_at__date=timezone.now().date()).count(),
        }
        
        # Последние действия
        recent_users = User.objects.order_by('-created_at')[:10]
        recent_exhibitions = Exhibition.objects.order_by('-created_at')[:10]
        recent_companies = Company.objects.order_by('-created_at')[:10]
        
        # Ожидающие модерации
        pending_exhibitions = Exhibition.objects.filter(status='pending')[:10]
        pending_companies = Company.objects.filter(status='pending')[:10]
        pending_reviews = CompanyReview.objects.filter(is_approved=False)[:10]
        
        context = {
            'title': 'Дашборд',
            'stats': stats,
            'recent_users': recent_users,
            'recent_exhibitions': recent_exhibitions,
            'recent_companies': recent_companies,
            'pending_exhibitions': pending_exhibitions,
            'pending_companies': pending_companies,
            'pending_reviews': pending_reviews,
        }
        
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
    def statistics_view(self, request):
        """Страница статистики"""
        # Статистика по дням за последний месяц
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        daily_users = []
        daily_exhibitions = []
        daily_registrations = []
        
        current_date = start_date
        while current_date <= end_date:
            daily_users.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': User.objects.filter(created_at__date=current_date).count()
            })
            daily_exhibitions.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': Exhibition.objects.filter(created_at__date=current_date).count()
            })
            daily_registrations.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': ExhibitionRegistration.objects.filter(created_at__date=current_date).count()
            })
            current_date += timedelta(days=1)
        
        # Топ категории
        top_categories = Category.objects.annotate(
            exhibitions_count=Count('exhibitions')
        ).order_by('-exhibitions_count')[:10]
        
        # Топ города
        top_cities = Exhibition.objects.values('city').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        context = {
            'title': 'Статистика',
            'daily_users': json.dumps(daily_users),
            'daily_exhibitions': json.dumps(daily_exhibitions),
            'daily_registrations': json.dumps(daily_registrations),
            'top_categories': top_categories,
            'top_cities': top_cities,
        }
        
        return TemplateResponse(request, 'admin/statistics.html', context)
    
    def moderation_view(self, request):
        """Страница модерации"""
        # Массовые действия
        if request.method == 'POST':
            action = request.POST.get('action')
            ids = request.POST.getlist('ids')
            
            if action == 'approve_exhibitions':
                Exhibition.objects.filter(id__in=ids).update(
                    status='approved',
                    moderated_by=request.user,
                    moderated_at=timezone.now()
                )
                return JsonResponse({'success': True, 'message': f'Одобрено {len(ids)} выставок'})
            
            elif action == 'reject_exhibitions':
                Exhibition.objects.filter(id__in=ids).update(
                    status='rejected',
                    moderated_by=request.user,
                    moderated_at=timezone.now()
                )
                return JsonResponse({'success': True, 'message': f'Отклонено {len(ids)} выставок'})
            
            elif action == 'approve_companies':
                Company.objects.filter(id__in=ids).update(
                    status='approved',
                    moderated_by=request.user,
                    moderated_at=timezone.now()
                )
                return JsonResponse({'success': True, 'message': f'Одобрено {len(ids)} компаний'})
            
            elif action == 'approve_reviews':
                CompanyReview.objects.filter(id__in=ids).update(
                    is_approved=True,
                    moderated_by=request.user,
                    moderated_at=timezone.now()
                )
                return JsonResponse({'success': True, 'message': f'Одобрено {len(ids)} отзывов'})
        
        # Получаем элементы для модерации
        pending_exhibitions = Exhibition.objects.filter(status='pending').order_by('-created_at')
        pending_companies = Company.objects.filter(status='pending').order_by('-created_at')
        pending_reviews = CompanyReview.objects.filter(is_approved=False).order_by('-created_at')
        
        context = {
            'title': 'Модерация',
            'pending_exhibitions': pending_exhibitions,
            'pending_companies': pending_companies,
            'pending_reviews': pending_reviews,
        }
        
        return TemplateResponse(request, 'admin/moderation.html', context)
    
    def analytics_view(self, request):
        """Страница аналитики"""
        # Получаем данные за последние 7 дней
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Аналитика выставок
        exhibition_analytics = ExhibitionAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).values('metric_type').annotate(
            total=Sum('value')
        )
        
        # Аналитика компаний
        company_analytics = CompanyAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).values('metric_type').annotate(
            total=Sum('value')
        )
        
        # Активность пользователей
        user_activities = UserActivity.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).values('activity_type').annotate(
            count=Count('id')
        )
        
        context = {
            'title': 'Аналитика',
            'exhibition_analytics': exhibition_analytics,
            'company_analytics': company_analytics,
            'user_activities': user_activities,
        }
        
        return TemplateResponse(request, 'admin/analytics.html', context)
    
    def users_export_view(self, request):
        """Экспорт пользователей в CSV"""
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Email', 'Имя', 'Фамилия', 'Роль', 'Дата регистрации', 'Email подтвержден'])
        
        for user in User.objects.all():
            writer.writerow([
                user.id,
                user.email,
                user.first_name,
                user.last_name,
                user.role,
                user.created_at.strftime('%Y-%m-%d %H:%M'),
                'Да' if user.is_email_verified else 'Нет'
            ])
        
        return response


# Создаем экземпляр кастомной админки
admin_site = ExhibitionAdminSite(name='exhibition_admin')


# ========== ПОЛЬЗОВАТЕЛИ ==========

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = [
        'avatar', 'bio', 'website', 'country', 'city',
        'organization_name', 'linkedin_url', 'show_email', 'show_phone'
    ]
    extra = 0


@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'get_full_name', 'role', 'is_email_verified', 
        'is_active', 'created_at', 'login_count'
    ]
    list_filter = [
        'role', 'is_email_verified', 'is_active', 'created_at', 'gdpr_consent'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'company_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_activity', 'login_count']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'username', 'password')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'phone', 'company_name', 'position')
        }),
        ('Права и статус', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_email_verified')
        }),
        ('GDPR', {
            'fields': ('gdpr_consent', 'gdpr_consent_date'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('created_at', 'updated_at', 'last_activity', 'login_count'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [UserProfileInline]
    
    actions = ['verify_email', 'send_verification', 'export_users']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Полное имя'
    
    def verify_email(self, request, queryset):
        count = 0
        for user in queryset.filter(is_email_verified=False):
            user.verify_email()
            count += 1
        self.message_user(request, f'Email подтвержден у {count} пользователей.')
    verify_email.short_description = 'Подтвердить email'


# ========== ВЫСТАВКИ ==========

class ExhibitionImageInline(admin.TabularInline):
    model = ExhibitionImage
    extra = 1
    fields = ['image', 'title', 'sort_order']


class ExhibitionDocumentInline(admin.TabularInline):
    model = ExhibitionDocument
    extra = 1
    fields = ['title', 'document_type', 'file', 'is_public']


@admin.register(Exhibition, site=admin_site)
class ExhibitionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'organizer', 'category', 'get_status_badge', 'start_date', 
        'city', 'views_count', 'registrations_count', 'is_featured'
    ]
    list_filter = [
        'status', 'exhibition_type', 'format', 'category', 'is_featured', 
        'start_date', 'city', 'created_at'
    ]
    search_fields = ['title', 'description', 'city', 'organizer__email']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ['-created_at']
    
    readonly_fields = [
        'views_count', 'favorites_count', 'registrations_count', 
        'created_at', 'updated_at', 'published_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category', 'tags')
        }),
        ('Тип и организация', {
            'fields': ('exhibition_type', 'format', 'organizer', 'co_organizers')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date', 'registration_deadline')
        }),
        ('Место', {
            'fields': ('venue_name', 'address', 'city', 'country')
        }),
        ('Медиа', {
            'fields': ('logo', 'banner_image')
        }),
        ('Контакты', {
            'fields': ('contact_person', 'contact_email', 'contact_phone', 'website')
        }),
        ('Стоимость', {
            'fields': ('is_free', 'visitor_fee', 'exhibitor_fee', 'currency')
        }),
        ('Статус', {
            'fields': ('status', 'rejection_reason', 'moderator_notes')
        }),
        ('Продвижение', {
            'fields': ('is_featured', 'is_premium')
        }),
        ('Статистика', {
            'fields': ('views_count', 'favorites_count', 'registrations_count'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ExhibitionImageInline, ExhibitionDocumentInline]
    filter_horizontal = ['tags', 'co_organizers']
    
    actions = ['approve_exhibitions', 'reject_exhibitions', 'publish_exhibitions', 'feature_exhibitions']
    
    def get_status_badge(self, obj):
        colors = {
            'draft': '#6c757d', 'pending': '#fd7e14', 'approved': '#0d6efd',
            'published': '#198754', 'rejected': '#dc3545', 'cancelled': '#6f42c1'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'
    
    def approve_exhibitions(self, request, queryset):
        count = queryset.update(
            status='approved', 
            moderated_by=request.user, 
            moderated_at=timezone.now()
        )
        self.message_user(request, f'Одобрено {count} выставок.')
    approve_exhibitions.short_description = '✅ Одобрить'
    
    def reject_exhibitions(self, request, queryset):
        count = queryset.update(
            status='rejected', 
            moderated_by=request.user, 
            moderated_at=timezone.now()
        )
        self.message_user(request, f'Отклонено {count} выставок.')
    reject_exhibitions.short_description = '❌ Отклонить'
    
    def publish_exhibitions(self, request, queryset):
        count = queryset.filter(status='approved').update(
            status='published', 
            published_at=timezone.now()
        )
        self.message_user(request, f'Опубликовано {count} выставок.')
    publish_exhibitions.short_description = '🚀 Опубликовать'
    
    def feature_exhibitions(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'Отмечено как рекомендуемые {count} выставок.')
    feature_exhibitions.short_description = '⭐ Рекомендовать'


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'get_exhibitions_count', 'is_active', 'is_featured', 'sort_order']
    list_filter = ['is_active', 'is_featured', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured', 'sort_order']
    ordering = ['sort_order', 'name']
    
    def get_exhibitions_count(self, obj):
        return obj.exhibitions.count()
    get_exhibitions_count.short_description = 'Выставки'


@admin.register(ExhibitionRegistration, site=admin_site)
class ExhibitionRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'exhibition', 'email', 'registration_type', 
        'get_status_badge', 'created_at'
    ]
    list_filter = ['registration_type', 'status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'company_name']
    readonly_fields = ['qr_code', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    actions = ['confirm_registrations', 'mark_attended']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Участник'
    
    def get_status_badge(self, obj):
        colors = {
            'pending': '#fd7e14', 'confirmed': '#198754',
            'cancelled': '#dc3545', 'attended': '#6f42c1'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'
    
    def confirm_registrations(self, request, queryset):
        count = queryset.filter(status='pending').update(
            status='confirmed', 
            confirmed_at=timezone.now()
        )
        self.message_user(request, f'Подтверждено {count} регистраций.')
    confirm_registrations.short_description = '✅ Подтвердить'
    
    def mark_attended(self, request, queryset):
        count = queryset.filter(status='confirmed').update(
            status='attended',
            attended_at=timezone.now()
        )
        self.message_user(request, f'Отмечено посещение {count} участников.')
    mark_attended.short_description = '🎯 Отметить посещение'


# ========== КОМПАНИИ ==========

class CompanyProductInline(admin.TabularInline):
    model = CompanyProduct
    extra = 1
    fields = ['name', 'product_type', 'price', 'currency', 'is_featured']


@admin.register(Company, site=admin_site)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'created_by', 'category', 'get_status_badge', 'city', 
        'views_count', 'is_verified', 'is_featured'
    ]
    list_filter = [
        'status', 'category', 'is_verified', 'is_featured', 
        'company_size', 'city', 'created_at'
    ]
    search_fields = ['name', 'description', 'city', 'created_by__email']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    
    readonly_fields = [
        'views_count', 'favorites_count', 'contact_requests_count', 
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category', 'tags')
        }),
        ('Владелец', {
            'fields': ('created_by',)
        }),
        ('Медиа', {
            'fields': ('logo', 'banner_image')
        }),
        ('Контакты', {
            'fields': ('website', 'email', 'phone', 'address', 'city', 'country')
        }),
        ('Дополнительно', {
            'fields': ('founded_year', 'company_size', 'employees_count')
        }),
        ('Статус', {
            'fields': ('status', 'is_verified', 'is_active', 'is_featured', 'is_premium')
        }),
        ('Статистика', {
            'fields': ('views_count', 'favorites_count', 'contact_requests_count'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CompanyProductInline]
    filter_horizontal = ['tags']
    
    actions = ['approve_companies', 'verify_companies', 'feature_companies']
    
    def get_status_badge(self, obj):
        colors = {
            'draft': '#6c757d', 'pending': '#fd7e14', 'approved': '#0d6efd',
            'active': '#198754', 'rejected': '#dc3545', 'suspended': '#6f42c1'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'
    
    def approve_companies(self, request, queryset):
        count = queryset.update(
            status='approved', 
            moderated_by=request.user, 
            moderated_at=timezone.now()
        )
        self.message_user(request, f'Одобрено {count} компаний.')
    approve_companies.short_description = '✅ Одобрить'
    
    def verify_companies(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'Верифицировано {count} компаний.')
    verify_companies.short_description = '🔒 Верифицировать'
    
    def feature_companies(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'Отмечено как рекомендуемые {count} компаний.')
    feature_companies.short_description = '⭐ Рекомендовать'


@admin.register(CompanyReview, site=admin_site)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'user', 'rating', 'get_status_badge', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_published', 'created_at']
    search_fields = ['company__name', 'user__email', 'title', 'text']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_reviews', 'reject_reviews']
    
    def get_status_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="color: #198754;">● Опубликован</span>')
        elif obj.is_approved:
            return format_html('<span style="color: #0d6efd;">● Одобрен</span>')
        else:
            return format_html('<span style="color: #fd7e14;">● На модерации</span>')
    get_status_badge.short_description = 'Статус'
    
    def approve_reviews(self, request, queryset):
        count = queryset.update(
            is_approved=True, 
            is_published=True,
            moderated_by=request.user, 
            moderated_at=timezone.now()
        )
        self.message_user(request, f'Одобрено {count} отзывов.')
    approve_reviews.short_description = '✅ Одобрить'
    
    def reject_reviews(self, request, queryset):
        count = queryset.update(is_approved=False, is_published=False)
        self.message_user(request, f'Отклонено {count} отзывов.')
    reject_reviews.short_description = '❌ Отклонить'


# ========== ПОДПИСКИ ==========

@admin.register(SubscriptionPlan, site=admin_site)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'name', 'price_monthly', 'price_yearly', 
        'max_exhibitions', 'is_active'
    ]
    list_filter = ['is_active', 'name']
    search_fields = ['display_name', 'description']
    list_editable = ['price_monthly', 'price_yearly', 'is_active']


@admin.register(Subscription, site=admin_site)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'plan', 'get_status_badge', 'billing_period', 
        'start_date', 'end_date', 'auto_renewal'
    ]
    list_filter = ['status', 'billing_period', 'plan', 'auto_renewal', 'created_at']
    search_fields = ['user__email', 'plan__display_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_status_badge(self, obj):
        colors = {
            'active': '#198754', 'expired': '#dc3545',
            'cancelled': '#6c757d', 'pending': '#fd7e14'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'


@admin.register(Payment, site=admin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'subscription', 'amount', 'currency', 'get_status_badge', 
        'payment_method', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['subscription__user__email', 'external_id']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_status_badge(self, obj):
        colors = {
            'completed': '#198754', 'pending': '#fd7e14',
            'failed': '#dc3545', 'refunded': '#6f42c1', 'cancelled': '#6c757d'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'

# ========== ОСНОВНЫЕ МОДЕЛИ (продолжение) ==========

@admin.register(SiteSettings, site=admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'setting_type', 'is_active', 'is_public']
    list_filter = ['setting_type', 'is_active', 'is_public']
    search_fields = ['key', 'description']
    list_editable = ['is_active', 'is_public']
    ordering = ['key']


@admin.register(ContactMessage, site=admin_site)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'get_status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    
    actions = ['mark_in_progress', 'mark_resolved']
    
    def get_status_badge(self, obj):
        colors = {
            'new': '#fd7e14', 'in_progress': '#0d6efd',
            'resolved': '#198754', 'closed': '#6c757d'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'
    
    def mark_in_progress(self, request, queryset):
        count = queryset.update(status='in_progress')
        self.message_user(request, f'{count} сообщений взято в работу.')
    mark_in_progress.short_description = '🔄 Взять в работу'
    
    def mark_resolved(self, request, queryset):
        count = queryset.update(status='resolved')
        self.message_user(request, f'{count} сообщений отмечено как решенные.')
    mark_resolved.short_description = '✅ Отметить решенными'


@admin.register(Notification, site=admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        self.message_user(request, f'{count} уведомлений отмечено как прочитанные.')
    mark_as_read.short_description = '📖 Отметить прочитанными'


# ========== ДОПОЛНИТЕЛЬНЫЕ МОДЕЛИ ==========

@admin.register(ExhibitionTag, site=admin_site)
class ExhibitionTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'get_exhibitions_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['color', 'is_active']
    
    def get_exhibitions_count(self, obj):
        return obj.exhibitions_count
    get_exhibitions_count.short_description = 'Выставки'


@admin.register(CompanyTag, site=admin_site)
class CompanyTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'get_companies_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['color', 'is_active']
    
    def get_companies_count(self, obj):
        return obj.companies_count
    get_companies_count.short_description = 'Компании'


@admin.register(ExhibitionSpeaker, site=admin_site)
class ExhibitionSpeakerAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'exhibition', 'company', 'is_keynote', 'is_featured']
    list_filter = ['is_keynote', 'is_featured', 'exhibition__status']
    search_fields = ['first_name', 'last_name', 'company', 'bio']
    list_editable = ['is_keynote', 'is_featured']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Имя'


@admin.register(ExhibitionSponsor, site=admin_site)
class ExhibitionSponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'exhibition', 'sponsor_type', 'is_featured']
    list_filter = ['sponsor_type', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['sponsor_type', 'is_featured']


@admin.register(CompanyContact, site=admin_site)
class CompanyContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'contact_type', 'get_status_badge', 'created_at']
    list_filter = ['contact_type', 'status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'company__name']
    readonly_fields = ['created_at', 'updated_at', 'ip_address']
    
    def get_status_badge(self, obj):
        colors = {
            'new': '#fd7e14', 'in_progress': '#0d6efd',
            'replied': '#198754', 'closed': '#6c757d'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#6c757d'), obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'


# ========== АНАЛИТИКА ==========

@admin.register(ExhibitionAnalytics, site=admin_site)
class ExhibitionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['exhibition', 'metric_type', 'value', 'date']
    list_filter = ['metric_type', 'date']
    search_fields = ['exhibition__title']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(CompanyAnalytics, site=admin_site)
class CompanyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['company', 'metric_type', 'value', 'date']
    list_filter = ['metric_type', 'date']
    search_fields = ['company__name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(ViewHistory, site=admin_site)
class ViewHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'object_id', 'created_at', 'ip_address']
    list_filter = ['content_type', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserActivity, site=admin_site)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'description', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ========== ТОКЕНЫ ==========

@admin.register(EmailVerificationToken, site=admin_site)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at', 'used_at']
    date_hierarchy = 'created_at'


@admin.register(PasswordResetToken, site=admin_site)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at', 'used_at']
    date_hierarchy = 'created_at'


# ========== НАСТРОЙКА ГЛАВНОЙ СТРАНИЦЫ АДМИНКИ ==========

admin_site.index_template = 'admin/custom_index.html'

# Настройка группировки моделей в админке
def get_app_list(self, request):
    """Кастомная группировка моделей"""
    app_list = [
        {
            'name': '📊 Дашборд',
            'app_label': 'dashboard',
            'models': [
                {
                    'name': 'Главная страница',
                    'object_name': 'dashboard',
                    'admin_url': '/admin/dashboard/',
                    'view_only': True,
                },
                {
                    'name': 'Статистика',
                    'object_name': 'statistics',
                    'admin_url': '/admin/statistics/',
                    'view_only': True,
                },
                {
                    'name': 'Модерация',
                    'object_name': 'moderation',
                    'admin_url': '/admin/moderation/',
                    'view_only': True,
                },
                {
                    'name': 'Аналитика',
                    'object_name': 'analytics',
                    'admin_url': '/admin/analytics/',
                    'view_only': True,
                },
            ]
        },
        {
            'name': '👥 Пользователи',
            'app_label': 'users',
            'models': [
                {
                    'name': 'Пользователи',
                    'object_name': 'user',
                    'admin_url': '/admin/users/user/',
                },
                {
                    'name': 'Активность пользователей',
                    'object_name': 'useractivity',
                    'admin_url': '/admin/users/useractivity/',
                },
                {
                    'name': 'Токены подтверждения',
                    'object_name': 'emailverificationtoken',
                    'admin_url': '/admin/users/emailverificationtoken/',
                },
            ]
        },
        {
            'name': '🎪 Выставки',
            'app_label': 'exhibitions',
            'models': [
                {
                    'name': 'Выставки',
                    'object_name': 'exhibition',
                    'admin_url': '/admin/exhibitions/exhibition/',
                },
                {
                    'name': 'Категории',
                    'object_name': 'category',
                    'admin_url': '/admin/exhibitions/category/',
                },
                {
                    'name': 'Регистрации',
                    'object_name': 'exhibitionregistration',
                    'admin_url': '/admin/exhibitions/exhibitionregistration/',
                },
                {
                    'name': 'Спикеры',
                    'object_name': 'exhibitionspeaker',
                    'admin_url': '/admin/exhibitions/exhibitionspeaker/',
                },
                {
                    'name': 'Теги выставок',
                    'object_name': 'exhibitiontag',
                    'admin_url': '/admin/exhibitions/exhibitiontag/',
                },
            ]
        },
        {
            'name': '🏢 Компании',
            'app_label': 'companies',
            'models': [
                {
                    'name': 'Компании',
                    'object_name': 'company',
                    'admin_url': '/admin/companies/company/',
                },
                {
                    'name': 'Отзывы о компаниях',
                    'object_name': 'companyreview',
                    'admin_url': '/admin/companies/companyreview/',
                },
                {
                    'name': 'Обращения к компаниям',
                    'object_name': 'companycontact',
                    'admin_url': '/admin/companies/companycontact/',
                },
                {
                    'name': 'Теги компаний',
                    'object_name': 'companytag',
                    'admin_url': '/admin/companies/companytag/',
                },
            ]
        },
        {
            'name': '💳 Подписки',
            'app_label': 'subscriptions',
            'models': [
                {
                    'name': 'Планы подписок',
                    'object_name': 'subscriptionplan',
                    'admin_url': '/admin/subscriptions/subscriptionplan/',
                },
                {
                    'name': 'Подписки',
                    'object_name': 'subscription',
                    'admin_url': '/admin/subscriptions/subscription/',
                },
                {
                    'name': 'Платежи',
                    'object_name': 'payment',
                    'admin_url': '/admin/subscriptions/payment/',
                },
                {
                    'name': 'Счета',
                    'object_name': 'invoice',
                    'admin_url': '/admin/subscriptions/invoice/',
                },
            ]
        },
        {
            'name': '⚙️ Система',
            'app_label': 'core',
            'models': [
                {
                    'name': 'Настройки сайта',
                    'object_name': 'sitesettings',
                    'admin_url': '/admin/core/sitesettings/',
                },
                {
                    'name': 'Уведомления',
                    'object_name': 'notification',
                    'admin_url': '/admin/core/notification/',
                },
                {
                    'name': 'Обратная связь',
                    'object_name': 'contactmessage',
                    'admin_url': '/admin/core/contactmessage/',
                },
                {
                    'name': 'История просмотров',
                    'object_name': 'viewhistory',
                    'admin_url': '/admin/core/viewhistory/',
                },
            ]
        },
        {
            'name': '📈 Аналитика',
            'app_label': 'analytics',
            'models': [
                {
                    'name': 'Аналитика выставок',
                    'object_name': 'exhibitionanalytics',
                    'admin_url': '/admin/exhibitions/exhibitionanalytics/',
                },
                {
                    'name': 'Аналитика компаний',
                    'object_name': 'companyanalytics',
                    'admin_url': '/admin/companies/companyanalytics/',
                },
            ]
        },
    ]
    return app_list

# Применяем кастомную группировку
admin_site.get_app_list = get_app_list.__get__(admin_site, ExhibitionAdminSite)