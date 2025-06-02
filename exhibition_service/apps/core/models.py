 #exhibition_service/apps/core/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Абстрактная модель с полями времени создания и обновления"""
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        abstract = True


class SlugModel(models.Model):
    """Абстрактная модель с полем slug"""
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug')
    )

    class Meta:
        abstract = True



class ViewHistory(TimeStampedModel):
    """История просмотров пользователя"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='view_history',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True  # Для анонимных пользователей
    )
    
    # Универсальная связь для любых объектов
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Тип объекта')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('ID объекта')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP адрес')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name=_('Ключ сессии')
    )
    referrer = models.URLField(
        blank=True,
        verbose_name=_('Источник перехода')
    )

    class Meta:
        verbose_name = _('История просмотров')
        verbose_name_plural = _('История просмотров')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'content_type', 'object_id']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        user_display = self.user.email if self.user else 'Анонимный'
        return f'{user_display} - {self.content_object} ({self.created_at})'


class Analytics(TimeStampedModel):
    """Аналитические данные"""
    class EventType(models.TextChoices):
        VIEW = 'view', _('Просмотр')
        CLICK = 'click', _('Клик')
        CONTACT = 'contact', _('Обращение')
        FAVORITE = 'favorite', _('Добавление в избранное')
        SHARE = 'share', _('Поделиться')
        SEARCH = 'search', _('Поиск')
        DOWNLOAD = 'download', _('Скачивание')
        REGISTRATION = 'registration', _('Регистрация')
    
    # Связь с объектом
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Тип объекта')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('ID объекта')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        verbose_name=_('Тип события')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics',
        verbose_name=_('Пользователь')
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name=_('Ключ сессии')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP адрес')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    referrer = models.URLField(
        blank=True,
        verbose_name=_('Источник перехода')
    )
    
    # Дополнительные данные
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Дополнительные данные')
    )
    
    # Геолокация
    country = models.CharField(_('Страна'), max_length=100, blank=True)
    city = models.CharField(_('Город'), max_length=100, blank=True)
    
    # Устройство
    device_type = models.CharField(_('Тип устройства'), max_length=20, blank=True)
    browser = models.CharField(_('Браузер'), max_length=50, blank=True)
    os = models.CharField(_('Операционная система'), max_length=50, blank=True)

    class Meta:
        verbose_name = _('Аналитика')
        verbose_name_plural = _('Аналитика')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        return f'{self.event_type} - {self.content_object} ({self.created_at})'


class Notification(TimeStampedModel):
    """Уведомления пользователей"""
    class Type(models.TextChoices):
        INFO = 'info', _('Информация')
        SUCCESS = 'success', _('Успех')
        WARNING = 'warning', _('Предупреждение')
        ERROR = 'error', _('Ошибка')
        SUBSCRIPTION = 'subscription', _('Подписка')
        MODERATION = 'moderation', _('Модерация')
        REMINDER = 'reminder', _('Напоминание')
        PROMOTION = 'promotion', _('Акция')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Пользователь')
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INFO,
        verbose_name=_('Тип')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Заголовок')
    )
    message = models.TextField(
        verbose_name=_('Сообщение')
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано')
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Время прочтения')
    )
    
    # Опциональная ссылка на связанный объект
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Тип объекта')
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID объекта')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Дополнительные поля
    action_url = models.URLField(_('Ссылка для действия'), blank=True)
    action_text = models.CharField(_('Текст кнопки действия'), max_length=50, blank=True)
    expires_at = models.DateTimeField(_('Срок действия'), null=True, blank=True)
    
    # Метаданные
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Дополнительные данные')
    )

    class Meta:
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['type']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.title}'

    def mark_as_read(self):
        """Отметить уведомление как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def is_expired(self):
        """Проверить, истекло ли уведомление"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class SiteSettings(models.Model):
    """Настройки сайта"""
    class SettingType(models.TextChoices):
        STRING = 'string', _('Строка')
        INTEGER = 'integer', _('Число')
        BOOLEAN = 'boolean', _('Логическое значение')
        JSON = 'json', _('JSON')
        TEXT = 'text', _('Текст')
    
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Ключ')
    )
    value = models.TextField(
        verbose_name=_('Значение')
    )
    setting_type = models.CharField(
        max_length=20,
        choices=SettingType.choices,
        default=SettingType.STRING,
        verbose_name=_('Тип настройки')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активно')
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Публичная настройка'),
        help_text=_('Доступна через API без авторизации')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Настройка сайта')
        verbose_name_plural = _('Настройки сайта')
        ordering = ['key']

    def __str__(self):
        return f'{self.key}: {self.value[:50]}'

    @classmethod
    def get_setting(cls, key, default=None):
        """Получить значение настройки"""
        try:
            setting = cls.objects.get(key=key, is_active=True)
            return cls._convert_value(setting.value, setting.setting_type)
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, setting_type='string', description=''):
        """Установить значение настройки"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value': str(value),
                'setting_type': setting_type,
                'description': description
            }
        )
        if not created:
            setting.value = str(value)
            setting.setting_type = setting_type
            if description:
                setting.description = description
            setting.save()
        return setting

    @staticmethod
    def _convert_value(value, setting_type):
        """Конвертировать значение в нужный тип"""
        if setting_type == SiteSettings.SettingType.INTEGER:
            return int(value)
        elif setting_type == SiteSettings.SettingType.BOOLEAN:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif setting_type == SiteSettings.SettingType.JSON:
            import json
            return json.loads(value)
        else:
            return value


class ContactMessage(TimeStampedModel):
    """Сообщения с формы обратной связи"""
    class Status(models.TextChoices):
        NEW = 'new', _('Новое')
        IN_PROGRESS = 'in_progress', _('В обработке')
        RESOLVED = 'resolved', _('Решено')
        CLOSED = 'closed', _('Закрыто')
    
    name = models.CharField(_('Имя'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    company = models.CharField(_('Компания'), max_length=200, blank=True)
    subject = models.CharField(_('Тема'), max_length=200)
    message = models.TextField(_('Сообщение'))
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name=_('Статус')
    )
    
    # Связанный пользователь (если авторизован)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_messages',
        verbose_name=_('Пользователь')
    )
    
    # Ответ администратора
    admin_response = models.TextField(_('Ответ администратора'), blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responded_messages',
        verbose_name=_('Ответил')
    )
    responded_at = models.DateTimeField(_('Дата ответа'), null=True, blank=True)
    
    # Метаданные
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)

    class Meta:
        verbose_name = _('Сообщение обратной связи')
        verbose_name_plural = _('Сообщения обратной связи')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'{self.name} - {self.subject}'
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Тип объекта')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('ID объекта')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Дополнительная информация
    notes = models.TextField(_('Заметки'), blank=True)
    tags = models.CharField(_('Теги'), max_length=200, blank=True)
    
    # Напоминания
    reminder_date = models.DateTimeField(_('Дата напоминания'), null=True, blank=True)
    is_reminded = models.BooleanField(_('Напоминание отправлено'), default=False)

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'content_type']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.content_object}'

