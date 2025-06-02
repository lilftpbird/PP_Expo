# exhibition_service/apps/companies/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
import os


class CompanyManager(models.Manager):
    """Менеджер для модели Company"""
    
    def active(self):
        """Возвращает только активные компании"""
        return self.filter(is_active=True, status='active')
    
    def verified(self):
        """Возвращает только верифицированные компании"""
        return self.filter(is_verified=True, is_active=True, status='active')
    
    def by_category(self, category):
        """Компании по категории"""
        return self.active().filter(category=category)
    
    def search(self, query):
        """Поиск компаний"""
        return self.active().filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(short_description__icontains=query) |
            models.Q(city__icontains=query)
        )
    
    def popular(self, limit=10):
        """Популярные компании по просмотрам"""
        return self.active().order_by('-views_count', '-rating')[:limit]
    
    def featured(self):
        """Рекомендуемые компании"""
        return self.active().filter(is_featured=True)


class Company(models.Model):
    """Модель компании-экспонента"""
    
    class CompanySize(models.TextChoices):
        STARTUP = 'startup', _('Стартап (до 10 сотрудников)')
        SMALL = 'small', _('Малая (10-50 сотрудников)')
        MEDIUM = 'medium', _('Средняя (50-250 сотрудников)')
        LARGE = 'large', _('Крупная (250-1000 сотрудников)')
        ENTERPRISE = 'enterprise', _('Корпорация (1000+ сотрудников)')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        PENDING = 'pending', _('На модерации')
        APPROVED = 'approved', _('Одобрено')
        REJECTED = 'rejected', _('Отклонено')
        ACTIVE = 'active', _('Активно')
        SUSPENDED = 'suspended', _('Приостановлено')
    
    # Основная информация
    name = models.CharField(_('Название компании'), max_length=200, db_index=True)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True, blank=True)
    description = models.TextField(_('Описание деятельности'))
    short_description = models.CharField(_('Краткое описание'), max_length=300, blank=True)
    
    # Владелец компании
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_companies',
        verbose_name=_('Создал')
    )
    
    # Модерация
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_companies',
        verbose_name=_('Модератор')
    )
    moderated_at = models.DateTimeField(_('Дата модерации'), null=True, blank=True)
    moderation_notes = models.TextField(_('Заметки модератора'), blank=True)
    
    # Категория деятельности
    category = models.ForeignKey(
        'exhibitions.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name=_('Категория деятельности')
    )
    
    # Теги
    tags = models.ManyToManyField(
        'CompanyTag',
        blank=True,
        related_name='companies',
        verbose_name=_('Теги')
    )
    
    # Медиа
    logo = models.ImageField(
        _('Логотип компании'), 
        upload_to='company_logos/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 300x300 пикселей')
    )
    banner_image = models.ImageField(
        _('Баннер компании'), 
        upload_to='company_banners/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 1200x400 пикселей')
    )
    
    # Контактная информация
    website = models.URLField(_('Веб-сайт'), blank=True)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    
    # Адрес
    address = models.TextField(_('Адрес'), blank=True)
    city = models.CharField(_('Город'), max_length=100, blank=True)
    region = models.CharField(_('Регион/Область'), max_length=100, blank=True)
    country = models.CharField(_('Страна'), max_length=100, default='Россия')
    postal_code = models.CharField(_('Почтовый индекс'), max_length=10, blank=True)
    
    # Координаты для карты
    latitude = models.DecimalField(
        _('Широта'), 
        max_digits=10, 
        decimal_places=8, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        _('Долгота'), 
        max_digits=11, 
        decimal_places=8, 
        null=True, 
        blank=True
    )
    
    # Дополнительная информация
    founded_year = models.PositiveIntegerField(
        _('Год основания'), 
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(1800),
            MaxValueValidator(timezone.now().year)
        ]
    )
    company_size = models.CharField(
        _('Размер компании'),
        max_length=20,
        choices=CompanySize.choices,
        blank=True
    )
    employees_count = models.PositiveIntegerField(_('Количество сотрудников'), null=True, blank=True)
    annual_revenue = models.CharField(_('Годовой оборот'), max_length=100, blank=True)
    
    # Социальные сети
    facebook_url = models.URLField(_('Facebook'), blank=True)
    twitter_url = models.URLField(_('Twitter'), blank=True)
    linkedin_url = models.URLField(_('LinkedIn'), blank=True)
    instagram_url = models.URLField(_('Instagram'), blank=True)
    youtube_url = models.URLField(_('YouTube'), blank=True)
    telegram_url = models.URLField(_('Telegram'), blank=True)
    
    # Статус и модерация
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    favorites_count = models.PositiveIntegerField(_('Количество добавлений в избранное'), default=0)
    contact_requests_count = models.PositiveIntegerField(_('Количество обращений'), default=0)
    
    # Рейтинг
    rating = models.DecimalField(
        _('Рейтинг'),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    reviews_count = models.PositiveIntegerField(_('Количество отзывов'), default=0)
    
    # Служебные поля
    is_verified = models.BooleanField(_('Верифицирована'), default=False)
    is_active = models.BooleanField(_('Активна'), default=True)
    is_featured = models.BooleanField(_('Рекомендуемая'), default=False)
    is_premium = models.BooleanField(_('Премиум размещение'), default=False)
    
    # Даты
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    published_at = models.DateTimeField(_('Дата публикации'), null=True, blank=True)
    
    # Менеджер
    objects = CompanyManager()

    class Meta:
        verbose_name = _('Компания')
        verbose_name_plural = _('Компании')
        db_table = 'companies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['-views_count']),
            models.Index(fields=['-rating']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Автоматическое создание slug
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Устанавливаем дату публикации при активации
        if self.status == self.Status.ACTIVE and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Обрабатываем изображения после сохранения
        self._process_images()

    def _process_images(self):
        """Обработка загруженных изображений"""
        if self.logo and os.path.exists(self.logo.path):
            self._resize_image(self.logo.path, (300, 300))
        if self.banner_image and os.path.exists(self.banner_image.path):
            self._resize_image(self.banner_image.path, (1200, 400))

    def _resize_image(self, image_path, size):
        """Изменяет размер изображения"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(image_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")

    def get_absolute_url(self):
        return reverse('companies:detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_contact_requests(self):
        """Увеличивает счетчик обращений"""
        self.contact_requests_count += 1
        self.save(update_fields=['contact_requests_count'])

    def update_rating(self):
        """Обновляет рейтинг на основе отзывов"""
        reviews = self.reviews.filter(is_approved=True, is_published=True)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2)
            self.reviews_count = reviews.count()
        else:
            self.rating = 0.00
            self.reviews_count = 0
        self.save(update_fields=['rating', 'reviews_count'])

    def get_social_links(self):
        """Возвращает список социальных ссылок"""
        links = []
        social_fields = {
            'facebook_url': ('Facebook', 'fab fa-facebook'),
            'twitter_url': ('Twitter', 'fab fa-twitter'),
            'linkedin_url': ('LinkedIn', 'fab fa-linkedin'),
            'instagram_url': ('Instagram', 'fab fa-instagram'),
            'youtube_url': ('YouTube', 'fab fa-youtube'),
            'telegram_url': ('Telegram', 'fab fa-telegram'),
        }
        
        for field, (name, icon) in social_fields.items():
            url = getattr(self, field)
            if url:
                links.append({'name': name, 'url': url, 'icon': icon})
        
        return links

    @property
    def is_published(self):
        """Опубликована ли компания"""
        return self.status == self.Status.ACTIVE

    @property
    def can_edit(self):
        """Может ли компания редактироваться"""
        return self.status in [self.Status.DRAFT, self.Status.REJECTED]

    @property
    def completion_percentage(self):
        """Процент заполнения профиля компании"""
        fields_to_check = [
            'description', 'short_description', 'website', 'email', 
            'phone', 'address', 'city', 'founded_year', 'company_size'
        ]
        filled_fields = sum(1 for field in fields_to_check if getattr(self, field))
        
        # Добавляем баллы за медиа
        if self.logo:
            filled_fields += 1
        if self.banner_image:
            filled_fields += 1
        if self.products.exists():
            filled_fields += 1
        
        total_fields = len(fields_to_check) + 3
        return int((filled_fields / total_fields) * 100)

    def get_related_companies(self, limit=5):
        """Возвращает похожие компании"""
        return Company.objects.active().filter(
            category=self.category
        ).exclude(pk=self.pk).order_by('-rating', '-views_count')[:limit]


class CompanyTag(models.Model):
    """Теги для компаний"""
    
    name = models.CharField(_('Название'), max_length=50, unique=True)
    slug = models.SlugField(_('Slug'), max_length=50, unique=True, blank=True)
    color = models.CharField(_('Цвет'), max_length=7, default='#6c757d')
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активен'), default=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Тег компании')
        verbose_name_plural = _('Теги компаний')
        db_table = 'company_tags'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def companies_count(self):
        """Количество компаний с этим тегом"""
        return self.companies.filter(is_active=True, status='active').count()


class CompanyProduct(models.Model):
    """Продукты/услуги компании"""
    
    class ProductType(models.TextChoices):
        PRODUCT = 'product', _('Продукт')
        SERVICE = 'service', _('Услуга')
        SOFTWARE = 'software', _('Программное обеспечение')
        EQUIPMENT = 'equipment', _('Оборудование')
        MATERIAL = 'material', _('Материал')
        OTHER = 'other', _('Другое')
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('Компания')
    )
    name = models.CharField(_('Название продукта/услуги'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    short_description = models.CharField(_('Краткое описание'), max_length=200, blank=True)
    
    product_type = models.CharField(
        _('Тип'),
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PRODUCT
    )
    
    image = models.ImageField(
        _('Изображение'), 
        upload_to='company_products/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 400x300 пикселей')
    )
    
    # Ценовая информация
    price = models.DecimalField(
        _('Цена'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(_('Валюта'), max_length=3, default='RUB')
    price_info = models.CharField(_('Информация о цене'), max_length=100, blank=True)
    
    # Ссылки
    product_url = models.URLField(_('Ссылка на продукт'), blank=True)
    datasheet_url = models.URLField(_('Техническая документация'), blank=True)
    
    # Характеристики
    specifications = models.JSONField(_('Технические характеристики'), default=dict, blank=True)
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Просмотры'), default=0)
    inquiries_count = models.PositiveIntegerField(_('Запросы'), default=0)
    
    # Настройки
    is_featured = models.BooleanField(_('Рекомендуемый'), default=False)
    is_active = models.BooleanField(_('Активен'), default=True)
    sort_order = models.PositiveIntegerField(_('Порядок сортировки'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Продукт компании')
        verbose_name_plural = _('Продукты компании')
        db_table = 'company_products'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['product_type']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while CompanyProduct.objects.filter(
                company=self.company, slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('companies:product_detail', kwargs={
            'company_slug': self.company.slug,
            'product_slug': self.slug
        })

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_inquiries(self):
        """Увеличивает счетчик запросов"""
        self.inquiries_count += 1
        self.save(update_fields=['inquiries_count'])

    @property
    def price_display(self):
        """Отображение цены"""
        if self.price:
            currency_symbols = {'RUB': '₽', 'USD': '$', 'EUR': '€'}
            symbol = currency_symbols.get(self.currency, self.currency)
            return f"{self.price:,.0f} {symbol}"
        return self.price_info or 'По запросу'


class CompanyGallery(models.Model):
    """Галерея изображений компании"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='gallery',
        verbose_name=_('Компания')
    )
    image = models.ImageField(_('Изображение'), upload_to='company_gallery/')
    title = models.CharField(_('Название'), max_length=200, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    sort_order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Изображение галереи')
        verbose_name_plural = _('Галерея компании')
        db_table = 'company_gallery'
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"Фото {self.company.name} - {self.title or self.id}"


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
    
    # Заметки пользователя
    notes = models.TextField(_('Заметки'), blank=True)
    
    # Напоминания
    reminder_date = models.DateTimeField(_('Дата напоминания'), null=True, blank=True)
    is_reminded = models.BooleanField(_('Напоминание отправлено'), default=False)

    class Meta:
        verbose_name = _('Избранная компания')
        verbose_name_plural = _('Избранные компании')
        db_table = 'favorite_companies'
        unique_together = ('user', 'company')
        ordering = ['-created_at']

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
    
    # Детализированные оценки
    quality_rating = models.IntegerField(_('Качество продукции'), choices=Rating.choices, null=True, blank=True)
    service_rating = models.IntegerField(_('Качество обслуживания'), choices=Rating.choices, null=True, blank=True)
    price_rating = models.IntegerField(_('Соотношение цена/качество'), choices=Rating.choices, null=True, blank=True)
    
    # Модерация
    is_approved = models.BooleanField(_('Одобрен'), default=False)
    is_published = models.BooleanField(_('Опубликован'), default=False)
    
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_company_reviews',
        verbose_name=_('Модератор')
    )
    moderated_at = models.DateTimeField(_('Дата модерации'), null=True, blank=True)
    moderator_notes = models.TextField(_('Заметки модератора'), blank=True)
    
    # Полезность отзыва
    helpful_count = models.PositiveIntegerField(_('Полезен'), default=0)
    not_helpful_count = models.PositiveIntegerField(_('Не полезен'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Отзыв о компании')
        verbose_name_plural = _('Отзывы о компаниях')
        db_table = 'company_reviews'
        unique_together = ('company', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'is_published']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Отзыв {self.user.email} о {self.company.name}"

    def save(self, *args, **kwargs):
        # Автоматическая публикация одобренных отзывов
        if self.is_approved:
            self.is_published = True
            if not self.moderated_at:
                self.moderated_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Обновляем рейтинг компании
        if self.is_published:
            self.company.update_rating()

    @property
    def average_detailed_rating(self):
        """Средняя оценка по детализированным критериям"""
        ratings = [
            self.quality_rating,
            self.service_rating,
            self.price_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            return sum(valid_ratings) / len(valid_ratings)
        return None

    @property
    def helpful_percentage(self):
        """Процент полезности отзыва"""
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes > 0:
            return (self.helpful_count / total_votes) * 100
        return 0


class ExhibitionParticipant(models.Model):
    """Участие компании в выставке"""
    
    class ParticipationType(models.TextChoices):
        EXHIBITOR = 'exhibitor', _('Экспонент')
        SPONSOR = 'sponsor', _('Спонсор')
        PARTNER = 'partner', _('Партнер')
        SPEAKER = 'speaker', _('Спикер')
        MEDIA = 'media', _('Медиа-партнер')
        ORGANIZER = 'organizer', _('Соорганизатор')
    
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
    
    # Информация о стенде
    booth_number = models.CharField(_('Номер стенда'), max_length=20, blank=True)
    booth_size = models.CharField(_('Размер стенда'), max_length=50, blank=True)
    booth_description = models.TextField(_('Описание стенда'), blank=True)
    special_offers = models.TextField(_('Специальные предложения'), blank=True)
    
    # Презентации и мероприятия
    presentation_title = models.CharField(_('Название презентации'), max_length=200, blank=True)
    presentation_time = models.DateTimeField(_('Время презентации'), null=True, blank=True)
    
    # Контактное лицо на выставке
    contact_person = models.CharField(_('Контактное лицо'), max_length=100, blank=True)
    contact_position = models.CharField(_('Должность'), max_length=100, blank=True)
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20, blank=True)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    
    # Демонстрируемые продукты
    featured_products = models.ManyToManyField(
        CompanyProduct,
        blank=True,
        related_name='exhibitions',
        verbose_name=_('Демонстрируемые продукты')
    )
    
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
        indexes = [
            models.Index(fields=['exhibition', 'participation_type']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return f"{self.company.name} на {self.exhibition.title}"

    def get_absolute_url(self):
        return reverse('exhibitions:participant_detail', kwargs={
            'exhibition_slug': self.exhibition.slug,
            'company_slug': self.company.slug
        })


class CompanyContact(models.Model):
    """Обращения к компаниям"""
    
    class ContactType(models.TextChoices):
        GENERAL = 'general', _('Общий вопрос')
        PRODUCT = 'product', _('О продукте/услуге')
        PARTNERSHIP = 'partnership', _('Сотрудничество')
        SUPPORT = 'support', _('Техническая поддержка')
        COMPLAINT = 'complaint', _('Жалоба')
        OTHER = 'other', _('Другое')
    
    class Status(models.TextChoices):
        NEW = 'new', _('Новое')
        IN_PROGRESS = 'in_progress', _('В обработке')
        REPLIED = 'replied', _('Отвечено')
        CLOSED = 'closed', _('Закрыто')
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('Компания')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_contacts',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True
    )
    
    # Контактная информация (для незарегистрированных пользователей)
    name = models.CharField(_('Имя'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    company_name = models.CharField(_('Компания'), max_length=200, blank=True)
    
    # Обращение
    contact_type = models.CharField(
        _('Тип обращения'),
        max_length=20,
        choices=ContactType.choices,
        default=ContactType.GENERAL
    )
    subject = models.CharField(_('Тема'), max_length=200)
    message = models.TextField(_('Сообщение'))
    
    # Дополнительная информация
    product = models.ForeignKey(
        CompanyProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Продукт')
    )
    
    # Статус обработки
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    
    # Ответ
    reply_message = models.TextField(_('Ответ'), blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_replies',
        verbose_name=_('Ответил')
    )
    replied_at = models.DateTimeField(_('Дата ответа'), null=True, blank=True)
    
    # Метаданные
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Обращение к компании')
        verbose_name_plural = _('Обращения к компаниям')
        db_table = 'company_contacts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['user']),
            models.Index(fields=['contact_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Обращение к {self.company.name} от {self.name}"

    def save(self, *args, **kwargs):
        # Заполняем контактную информацию из профиля пользователя
        if self.user and not self.name:
            self.name = self.user.get_full_name() or self.user.email
            self.email = self.user.email
            if hasattr(self.user, 'phone'):
                self.phone = self.user.phone
            if hasattr(self.user, 'company_name'):
                self.company_name = self.user.company_name
        
        # Устанавливаем дату ответа
        if self.status == self.Status.REPLIED and not self.replied_at:
            self.replied_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Увеличиваем счетчик обращений к компании
        if self._state.adding:  # Только при создании
            self.company.increment_contact_requests()

    def mark_as_replied(self, reply_message, replied_by):
        """Отмечает обращение как отвеченное"""
        self.status = self.Status.REPLIED
        self.reply_message = reply_message
        self.replied_by = replied_by
        self.replied_at = timezone.now()
        self.save()


class CompanyAnalytics(models.Model):
    """Аналитика по компаниям"""
    
    class MetricType(models.TextChoices):
        VIEWS = 'views', _('Просмотры')
        CONTACTS = 'contacts', _('Обращения')
        FAVORITES = 'favorites', _('Добавления в избранное')
        PRODUCT_VIEWS = 'product_views', _('Просмотры продуктов')
        REVIEWS = 'reviews', _('Отзывы')
        CLICKS = 'clicks', _('Клики по ссылкам')
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name=_('Компания')
    )
    metric_type = models.CharField(
        _('Тип метрики'),
        max_length=20,
        choices=MetricType.choices
    )
    value = models.PositiveIntegerField(_('Значение'), default=0)
    date = models.DateField(_('Дата'))
    
    # Дополнительные параметры
    source = models.CharField(_('Источник'), max_length=100, blank=True)
    user_agent = models.CharField(_('User Agent'), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Аналитика компании')
        verbose_name_plural = _('Аналитика компаний')
        db_table = 'company_analytics'
        unique_together = ('company', 'metric_type', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['company', 'metric_type']),
            models.Index(fields=['date']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.company.name} - {self.get_metric_type_display()} - {self.date}"

    @classmethod
    def record_metric(cls, company, metric_type, value=1, date=None, **kwargs):
        """Записывает метрику"""
        if date is None:
            date = timezone.now().date()
        
        metric, created = cls.objects.get_or_create(
            company=company,
            metric_type=metric_type,
            date=date,
            defaults={'value': value, **kwargs}
        )
        
        if not created:
            metric.value += value
            metric.save(update_fields=['value'])
        
        return metric

    @classmethod
    def get_company_stats(cls, company, start_date=None, end_date=None):
        """Получает статистику компании за период"""
        queryset = cls.objects.filter(company=company)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        stats = {}
        for metric_type, _ in cls.MetricType.choices:
            stats[metric_type] = queryset.filter(
                metric_type=metric_type
            ).aggregate(
                total=models.Sum('value')
            )['total'] or 0
        
        return stats


class CompanyCertificate(models.Model):
    """Сертификаты и награды компании"""
    
    class CertificateType(models.TextChoices):
        ISO = 'iso', _('ISO стандарт')
        QUALITY = 'quality', _('Сертификат качества')
        SAFETY = 'safety', _('Сертификат безопасности')
        AWARD = 'award', _('Награда')
        ACCREDITATION = 'accreditation', _('Аккредитация')
        OTHER = 'other', _('Другое')
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name=_('Компания')
    )
    
    name = models.CharField(_('Название'), max_length=200)
    certificate_type = models.CharField(
        _('Тип'),
        max_length=20,
        choices=CertificateType.choices,
        default=CertificateType.OTHER
    )
    description = models.TextField(_('Описание'), blank=True)
    
    # Файлы
    certificate_file = models.FileField(
        _('Файл сертификата'),
        upload_to='company_certificates/',
        blank=True,
        null=True
    )
    image = models.ImageField(
        _('Изображение'),
        upload_to='company_certificates/images/',
        blank=True,
        null=True
    )
    
    # Информация о выдаче
    issuer = models.CharField(_('Выдан'), max_length=200, blank=True)
    issue_date = models.DateField(_('Дата выдачи'), null=True, blank=True)
    expiry_date = models.DateField(_('Срок действия'), null=True, blank=True)
    certificate_number = models.CharField(_('Номер сертификата'), max_length=100, blank=True)
    
    # Настройки
    is_active = models.BooleanField(_('Активен'), default=True)
    is_featured = models.BooleanField(_('Показывать в профиле'), default=True)
    sort_order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Сертификат компании')
        verbose_name_plural = _('Сертификаты компании')
        db_table = 'company_certificates'
        ordering = ['sort_order', '-issue_date']

    def __str__(self):
        return f"{self.company.name} - {self.name}"

    @property
    def is_expired(self):
        """Проверяет, истек ли сертификат"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def expires_soon(self):
        """Проверяет, истекает ли сертификат в ближайшие 30 дней"""
        if self.expiry_date:
            return (self.expiry_date - timezone.now().date()).days <= 30
        return False


# Сигналы для автоматических действий
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    """Действия после сохранения компании"""
    if created:
        # Логируем создание компании
        try:
            from apps.users.models import UserActivity
            UserActivity.log_activity(
                user=instance.created_by,
                activity_type=UserActivity.ActivityType.COMPANY_CREATE,
                description=f"Создана компания: {instance.name}"
            )
        except ImportError:
            pass  # Если модель UserActivity еще не создана

@receiver(post_save, sender=FavoriteCompany)
def favorite_company_post_save(sender, instance, created, **kwargs):
    """Действия после добавления в избранное"""
    if created:
        # Увеличиваем счетчик
        instance.company.favorites_count += 1
        instance.company.save(update_fields=['favorites_count'])
        
        # Логируем активность
        try:
            from apps.users.models import UserActivity
            UserActivity.log_activity(
                user=instance.user,
                activity_type=UserActivity.ActivityType.FAVORITE_ADD,
                description=f"Добавлена в избранное компания: {instance.company.name}"
            )
        except ImportError:
            pass

@receiver(post_delete, sender=FavoriteCompany)
def favorite_company_post_delete(sender, instance, **kwargs):
    """Действия после удаления из избранного"""
    # Уменьшаем счетчик
    if instance.company.favorites_count > 0:
        instance.company.favorites_count -= 1
        instance.company.save(update_fields=['favorites_count'])
    
    # Логируем активность
    try:
        from apps.users.models import UserActivity
        UserActivity.log_activity(
            user=instance.user,
            activity_type=UserActivity.ActivityType.FAVORITE_REMOVE,
            description=f"Удалена из избранного компания: {instance.company.name}"
        )
    except ImportError:
        pass

@receiver(post_save, sender=CompanyReview)
def company_review_post_save(sender, instance, created, **kwargs):
    """Действия после сохранения отзыва"""
    if instance.is_published:
        # Обновляем рейтинг компании
        instance.company.update_rating()
        
        # Записываем в аналитику
        CompanyAnalytics.record_metric(
            company=instance.company,
            metric_type=CompanyAnalytics.MetricType.REVIEWS
        )


# Дополнительные менеджеры и методы
class CompanyQuerySet(models.QuerySet):
    """Дополнительные методы для запросов компаний"""
    
    def with_location(self):
        """Компании с указанным местоположением"""
        return self.exclude(
            models.Q(city='') | models.Q(city__isnull=True)
        )
    
    def with_contacts(self):
        """Компании с контактной информацией"""
        return self.exclude(
            models.Q(email='') & models.Q(phone='') & models.Q(website='')
        )
    
    def with_products(self):
        """Компании с продукцией"""
        return self.filter(products__isnull=False).distinct()
    
    def by_rating(self, min_rating=3.0):
        """Компании с рейтингом выше указанного"""
        return self.filter(rating__gte=min_rating)
    
    def recent(self, days=30):
        """Недавно созданные компании"""
        from django.utils import timezone
        date_from = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=date_from)
    
    def in_city(self, city):
        """Компании в определенном городе"""
        return self.filter(city__icontains=city)
    
    def with_tags(self, tags):
        """Компании с определенными тегами"""
        if isinstance(tags, str):
            tags = [tags]
        return self.filter(tags__name__in=tags).distinct()


# Добавляем QuerySet к менеджеру
CompanyManager = CompanyManager.from_queryset(CompanyQuerySet)
Company.add_to_class('objects', CompanyManager())