from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Company(models.Model):
    """Модель компании-экспонента"""
    
    class CompanySize(models.TextChoices):
        STARTUP = 'startup', _('Стартап')
        SMALL = 'small', _('Малая (до 50 сотрудников)')
        MEDIUM = 'medium', _('Средняя (50-250 сотрудников)')
        LARGE = 'large', _('Крупная (250+ сотрудников)')
        ENTERPRISE = 'enterprise', _('Корпорация')
    
    # Основная информация
    name = models.CharField(_('Название компании'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True, blank=True)
    description = models.TextField(_('Описание деятельности'))
    short_description = models.CharField(_('Краткое описание'), max_length=300, blank=True)
    
    # Создатель/владелец карточки компании
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_companies',
        verbose_name=_('Создал')
    )
    
    # Категория деятельности
    category = models.ForeignKey(
        'exhibitions.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name=_('Категория деятельности')
    )
    
    # Медиа
    logo = models.ImageField(_('Логотип компании'), upload_to='company_logos/', blank=True, null=True)
    banner_image = models.ImageField(_('Баннер компании'), upload_to='company_banners/', blank=True, null=True)
    
    # Контактная информация
    website = models.URLField(_('Веб-сайт'), blank=True)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    
    # Адрес
    address = models.TextField(_('Адрес'), blank=True)
    city = models.CharField(_('Город'), max_length=100, blank=True)
    country = models.CharField(_('Страна'), max_length=100, default='Россия')
    
    # Дополнительная информация
    founded_year = models.PositiveIntegerField(_('Год основания'), null=True, blank=True)
    company_size = models.CharField(
        _('Размер компании'),
        max_length=20,
        choices=CompanySize.choices,
        blank=True
    )
    employees_count = models.PositiveIntegerField(_('Количество сотрудников'), null=True, blank=True)
    
    # Социальные сети
    facebook_url = models.URLField(_('Facebook'), blank=True)
    twitter_url = models.URLField(_('Twitter'), blank=True)
    linkedin_url = models.URLField(_('LinkedIn'), blank=True)
    instagram_url = models.URLField(_('Instagram'), blank=True)
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    favorites_count = models.PositiveIntegerField(_('Количество добавлений в избранное'), default=0)
    
    # Служебные поля
    is_verified = models.BooleanField(_('Верифицирована'), default=False)
    is_active = models.BooleanField(_('Активна'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Компания')
        verbose_name_plural = _('Компании')
        db_table = 'companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('company_detail', kwargs={'slug': self.slug})


class CompanyProduct(models.Model):
    """Продукты/услуги компании"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Компания')
    )
    name = models.CharField(_('Название продукта/услуги'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    image = models.ImageField(_('Изображение'), upload_to='company_products/', blank=True, null=True)
    price_info = models.CharField(_('Информация о цене'), max_length=100, blank=True)
    product_url = models.URLField(_('Ссылка на продукт'), blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Продукт компании')
        verbose_name_plural = _('Продукты компании')
        db_table = 'company_products'
        ordering = ['name']

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class ExhibitionParticipant(models.Model):
    """Участие компании в выставке"""
    
    class ParticipationType(models.TextChoices):
        EXHIBITOR = 'exhibitor', _('Экспонент')
        SPONSOR = 'sponsor', _('Спонсор')
        PARTNER = 'partner', _('Партнер')
        SPEAKER = 'speaker', _('Спикер')
    
    exhibition = models.ForeignKey(
        'exhibitions.Exhibition',
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('Выставка')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name=_('Компания')
    )
    participation_type = models.CharField(
        _('Тип участия'),
        max_length=20,
        choices=ParticipationType.choices,
        default=ParticipationType.EXHIBITOR
    )
    
    # Дополнительная информация об участии
    booth_number = models.CharField(_('Номер стенда'), max_length=20, blank=True)
    booth_size = models.CharField(_('Размер стенда'), max_length=50, blank=True)
    special_offers = models.TextField(_('Специальные предложения'), blank=True)
    presentation_title = models.CharField(_('Название презентации'), max_length=200, blank=True)
    presentation_time = models.DateTimeField(_('Время презентации'), null=True, blank=True)
    
    # Контактное лицо на выставке
    contact_person = models.CharField(_('Контактное лицо'), max_length=100, blank=True)
    contact_position = models.CharField(_('Должность'), max_length=100, blank=True)
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20, blank=True)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    favorites_count = models.PositiveIntegerField(_('Количество добавлений в избранное'), default=0)
    
    # Служебные поля
    is_featured = models.BooleanField(_('Рекомендуемый участник'), default=False)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Участник выставки')
        verbose_name_plural = _('Участники выставки')
        db_table = 'exhibition_participants'
        unique_together = ('exhibition', 'company')
        ordering = ['company__name']

    def __str__(self):
        return f"{self.company.name} на {self.exhibition.title}"


class FavoriteCompany(models.Model):
    """Избранные компании пользователей"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_companies',
        verbose_name=_('Пользователь')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('Компания')
    )
    created_at = models.DateTimeField(_('Дата добавления'), auto_now_add=True)

    class Meta:
        verbose_name = _('Избранная компания')
        verbose_name_plural = _('Избранные компании')
        db_table = 'favorite_companies'
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.email} - {self.company.name}"


class CompanyReview(models.Model):
    """Отзывы о компаниях"""
    
    class Rating(models.IntegerChoices):
        ONE = 1, _('1 звезда')
        TWO = 2, _('2 звезды')
        THREE = 3, _('3 звезды')
        FOUR = 4, _('4 звезды')
        FIVE = 5, _('5 звезд')
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Компания')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_reviews',
        verbose_name=_('Пользователь')
    )
    rating = models.IntegerField(_('Рейтинг'), choices=Rating.choices)
    title = models.CharField(_('Заголовок отзыва'), max_length=200, blank=True)
    text = models.TextField(_('Текст отзыва'))
    
    # Модерация
    is_approved = models.BooleanField(_('Одобрен'), default=False)
    is_published = models.BooleanField(_('Опубликован'), default=False)
    moderator_notes = models.TextField(_('Заметки модератора'), blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Отзыв о компании')
        verbose_name_plural = _('Отзывы о компаниях')
        db_table = 'company_reviews'
        unique_together = ('company', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв {self.user.email} о {self.company.name}"