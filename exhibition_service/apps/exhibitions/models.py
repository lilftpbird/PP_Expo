from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Категории/отрасли выставок"""
    
    name = models.CharField(_('Название категории'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    icon = models.ImageField(_('Иконка категории'), upload_to='category_icons/', blank=True, null=True)
    is_active = models.BooleanField(_('Активна'), default=True)
    sort_order = models.PositiveIntegerField(_('Порядок сортировки'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        db_table = 'categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Exhibition(models.Model):
    """Модель выставки"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        PENDING = 'pending', _('На рассмотрении')
        APPROVED = 'approved', _('Одобрено')
        REJECTED = 'rejected', _('Отклонено')
        REQUIRES_CHANGES = 'requires_changes', _('Требуются изменения')
        PUBLISHED = 'published', _('Опубликовано')
        CANCELLED = 'cancelled', _('Отменено')
    
    class ExhibitionType(models.TextChoices):
        UPCOMING = 'upcoming', _('Предстоящая')
        CURRENT = 'current', _('Текущая')
        COMPLETED = 'completed', _('Завершенная')
    
    # Основная информация
    title = models.CharField(_('Название выставки'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True, blank=True)
    description = models.TextField(_('Описание'))
    short_description = models.CharField(_('Краткое описание'), max_length=500, blank=True)
    
    # Организатор
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_exhibitions',
        verbose_name=_('Организатор')
    )
    
    # Категория
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='exhibitions',
        verbose_name=_('Категория')
    )
    
    # Даты
    start_date = models.DateTimeField(_('Дата начала'))
    end_date = models.DateTimeField(_('Дата окончания'))
    registration_deadline = models.DateTimeField(_('Крайний срок регистрации'), null=True, blank=True)
    
    # Местоположение
    venue_name = models.CharField(_('Название площадки'), max_length=200)
    address = models.TextField(_('Адрес проведения'))
    city = models.CharField(_('Город'), max_length=100)
    country = models.CharField(_('Страна'), max_length=100, default='Россия')
    latitude = models.DecimalField(_('Широта'), max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(_('Долгота'), max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Медиа
    logo = models.ImageField(_('Логотип выставки'), upload_to='exhibition_logos/', blank=True, null=True)
    banner_image = models.ImageField(_('Баннер'), upload_to='exhibition_banners/', blank=True, null=True)
    
    # Контактная информация
    contact_person = models.CharField(_('Контактное лицо'), max_length=100, blank=True)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20, blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)
    
    # Статус и модерация
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    rejection_reason = models.TextField(_('Причина отклонения'), blank=True)
    moderator_notes = models.TextField(_('Заметки модератора'), blank=True)
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    favorites_count = models.PositiveIntegerField(_('Количество добавлений в избранное'), default=0)
    
    # Дополнительные поля
    is_featured = models.BooleanField(_('Рекомендуемая'), default=False)
    is_free = models.BooleanField(_('Бесплатное участие'), default=False)
    max_participants = models.PositiveIntegerField(_('Максимальное количество участников'), null=True, blank=True)
    
    # Служебные поля
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    published_at = models.DateTimeField(_('Дата публикации'), null=True, blank=True)

    class Meta:
        verbose_name = _('Выставка')
        verbose_name_plural = _('Выставки')
        db_table = 'exhibitions'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('exhibition_detail', kwargs={'slug': self.slug})

    @property
    def exhibition_type(self):
        """Определяет тип выставки по датам"""
        from django.utils import timezone
        now = timezone.now()
        
        if now < self.start_date:
            return self.ExhibitionType.UPCOMING
        elif self.start_date <= now <= self.end_date:
            return self.ExhibitionType.CURRENT
        else:
            return self.ExhibitionType.COMPLETED

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_active(self):
        """Проверяет, активна ли выставка (опубликована и не завершена)"""
        from django.utils import timezone
        return self.is_published and timezone.now() <= self.end_date

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать выставку"""
        return (
            user == self.organizer or 
            user.is_admin_user or 
            user.is_superuser
        )


class ExhibitionImage(models.Model):
    """Дополнительные изображения выставки"""
    
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Выставка')
    )
    image = models.ImageField(_('Изображение'), upload_to='exhibition_images/')
    caption = models.CharField(_('Подпись'), max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Изображение выставки')
        verbose_name_plural = _('Изображения выставки')
        db_table = 'exhibition_images'
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"Изображение для {self.exhibition.title}"


class ExhibitionDocument(models.Model):
    """Документы выставки"""
    
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Выставка')
    )
    title = models.CharField(_('Название документа'), max_length=200)
    file = models.FileField(_('Файл'), upload_to='exhibition_documents/')
    file_size = models.PositiveIntegerField(_('Размер файла'), null=True, blank=True)
    download_count = models.PositiveIntegerField(_('Количество скачиваний'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Документ выставки')
        verbose_name_plural = _('Документы выставки')
        db_table = 'exhibition_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.exhibition.title}"


class FavoriteExhibition(models.Model):
    """Избранные выставки пользователей"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_exhibitions',
        verbose_name=_('Пользователь')
    )
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('Выставка')
    )
    created_at = models.DateTimeField(_('Дата добавления'), auto_now_add=True)

    class Meta:
        verbose_name = _('Избранная выставка')
        verbose_name_plural = _('Избранные выставки')
        db_table = 'favorite_exhibitions'
        unique_together = ('user', 'exhibition')

    def __str__(self):
        return f"{self.user.email} - {self.exhibition.title}"