from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


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


class Favorite(TimeStampedModel):
    """Модель для избранного"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_('Пользователь')
    )
    
    # Универсальная связь для любых объектов (выставки, компании)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Тип объекта')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('ID объекта')
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.content_object}'


class Review(TimeStampedModel):
    """Модель отзывов на выставки"""
    class Rating(models.IntegerChoices):
        ONE = 1, _('1 звезда')
        TWO = 2, _('2 звезды')
        THREE = 3, _('3 звезды')
        FOUR = 4, _('4 звезды')
        FIVE = 5, _('5 звезд')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('На модерации')
        APPROVED = 'approved', _('Одобрен')
        REJECTED = 'rejected', _('Отклонен')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Пользователь')
    )
    exhibition = models.ForeignKey(
        'exhibitions.Exhibition',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Выставка')
    )
    rating = models.IntegerField(
        choices=Rating.choices,
        verbose_name=_('Оценка')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Заголовок')
    )
    text = models.TextField(
        verbose_name=_('Текст отзыва')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Статус')
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews',
        verbose_name=_('Модератор')
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата модерации')
    )
    moderation_comment = models.TextField(
        blank=True,
        verbose_name=_('Комментарий модератора')
    )

    class Meta:
        verbose_name = _('Отзыв')
        verbose_name_plural = _('Отзывы')
        unique_together = ('user', 'exhibition')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.exhibition.title} ({self.rating}★)'


class ViewHistory(TimeStampedModel):
    """История просмотров пользователя"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='view_history',
        verbose_name=_('Пользователь')
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

    class Meta:
        verbose_name = _('История просмотров')
        verbose_name_plural = _('История просмотров')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'content_type', 'object_id']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.content_object} ({self.created_at})'


class Analytics(TimeStampedModel):
    """Аналитические данные"""
    class EventType(models.TextChoices):
        VIEW = 'view', _('Просмотр')
        CLICK = 'click', _('Клик')
        CONTACT = 'contact', _('Обращение')
        FAVORITE = 'favorite', _('Добавление в избранное')
        SHARE = 'share', _('Поделиться')
    
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

    class Meta:
        verbose_name = _('Аналитика')
        verbose_name_plural = _('Аналитика')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['-created_at']),
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

    class Meta:
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.title}'

    def mark_as_read(self):
        """Отметить уведомление как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class SiteSettings(models.Model):
    """Настройки сайта"""
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Ключ')
    )
    value = models.TextField(
        verbose_name=_('Значение')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активно')
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
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, description=''):
        """Установить значение настройки"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description
            }
        )
        if not created:
            setting.value = value
            if description:
                setting.description = description
            setting.save()
        return setting