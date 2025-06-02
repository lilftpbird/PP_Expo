from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class CategoryManager(models.Manager):
    """Менеджер для категорий"""
    
    def active(self):
        """Возвращает только активные категории"""
        return self.filter(is_active=True)
    
    def with_exhibitions(self):
        """Категории с выставками"""
        return self.active().filter(exhibitions__isnull=False).distinct()
    
    def with_companies(self):
        """Категории с компаниями"""
        return self.active().filter(companies__isnull=False).distinct()
    
    def featured(self):
        """Рекомендуемые категории"""
        return self.active().filter(is_featured=True)


class Category(models.Model):
    """Категории/отрасли выставок"""
    
    name = models.CharField(_('Название категории'), max_length=100, db_index=True)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True, blank=True)
    description = models.TextField(_('Описание'), blank=True)
    short_description = models.CharField(_('Краткое описание'), max_length=200, blank=True)
    
    # Медиа
    icon = models.ImageField(
        _('Иконка категории'), 
        upload_to='category_icons/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 64x64 пикселя')
    )
    banner_image = models.ImageField(
        _('Баннер категории'),
        upload_to='category_banners/',
        blank=True,
        null=True,
        help_text=_('Рекомендуемый размер: 1200x300 пикселей')
    )
    
    # Иерархия
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Родительская категория')
    )
    
    # Цвет для UI
    color = models.CharField(_('Цвет'), max_length=7, default='#6c757d')
    
    # Настройки
    is_active = models.BooleanField(_('Активна'), default=True)
    is_featured = models.BooleanField(_('Рекомендуемая'), default=False)
    sort_order = models.PositiveIntegerField(_('Порядок сортировки'), default=0)
    
    # SEO
    meta_title = models.CharField(_('META заголовок'), max_length=60, blank=True)
    meta_description = models.CharField(_('META описание'), max_length=160, blank=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    objects = CategoryManager()

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        db_table = 'categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # SEO поля по умолчанию
        if not self.meta_title:
            self.meta_title = self.name[:60]
        if not self.meta_description:
            self.meta_description = (self.short_description or self.description)[:160]
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('exhibitions:category_detail', kwargs={'slug': self.slug})

    @property
    def exhibitions_count(self):
        """Количество выставок в категории"""
        return self.exhibitions.filter(status='published').count()

    @property
    def companies_count(self):
        """Количество компаний в категории"""
        return self.companies.filter(is_active=True, status='active').count()

    def get_subcategories(self):
        """Возвращает подкategории"""
        return self.children.filter(is_active=True).order_by('sort_order', 'name')

    def get_all_children(self):
        """Возвращает все дочерние категории (рекурсивно)"""
        children = list(self.children.filter(is_active=True))
        for child in self.children.filter(is_active=True):
            children.extend(child.get_all_children())
        return children

    def get_breadcrumbs(self):
        """Возвращает хлебные крошки"""
        breadcrumbs = [self]
        current = self.parent
        while current:
            breadcrumbs.insert(0, current)
            current = current.parent
        return breadcrumbs


class ExhibitionManager(models.Manager):
    """Менеджер для выставок"""
    
    def published(self):
        """Опубликованные выставки"""
        return self.filter(status=Exhibition.Status.PUBLISHED)
    
    def upcoming(self):
        """Предстоящие выставки"""
        return self.published().filter(start_date__gt=timezone.now())
    
    def current(self):
        """Текущие выставки"""
        now = timezone.now()
        return self.published().filter(start_date__lte=now, end_date__gte=now)
    
    def past(self):
        """Прошедшие выставки"""
        return self.published().filter(end_date__lt=timezone.now())
    
    def featured(self):
        """Рекомендуемые выставки"""
        return self.published().filter(is_featured=True)
    
    def by_category(self, category):
        """Выставки по категории"""
        return self.published().filter(category=category)
    
    def search(self, query):
        """Поиск выставок"""
        return self.published().filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(short_description__icontains=query) |
            models.Q(city__icontains=query) |
            models.Q(venue_name__icontains=query)
        )
    
    def in_city(self, city):
        """Выставки в городе"""
        return self.published().filter(city__icontains=city)
    
    def by_format(self, format_type):
        """Выставки по формату"""
        return self.published().filter(format=format_type)


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
        COMPLETED = 'completed', _('Завершено')
    
    class ExhibitionType(models.TextChoices):
        TRADE_SHOW = 'trade_show', _('Торговая выставка')
        CONFERENCE = 'conference', _('Конференция')
        SEMINAR = 'seminar', _('Семинар')
        WORKSHOP = 'workshop', _('Воркшоп')
        NETWORKING = 'networking', _('Нетворкинг')
        EXPO = 'expo', _('Экспо')
        FAIR = 'fair', _('Ярмарка')
        FORUM = 'forum', _('Форум')
        CONGRESS = 'congress', _('Конгресс')
        SYMPOSIUM = 'symposium', _('Симпозиум')
    
    class Format(models.TextChoices):
        OFFLINE = 'offline', _('Очный')
        ONLINE = 'online', _('Онлайн')
        HYBRID = 'hybrid', _('Гибридный')
    
    # Основная информация
    title = models.CharField(_('Название выставки'), max_length=200, db_index=True)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True, blank=True)
    description = models.TextField(_('Описание'))
    short_description = models.CharField(_('Краткое описание'), max_length=500, blank=True)
    
    # Тип и формат
    exhibition_type = models.CharField(
        _('Тип мероприятия'),
        max_length=20,
        choices=ExhibitionType.choices,
        default=ExhibitionType.TRADE_SHOW
    )
    format = models.CharField(
        _('Формат проведения'),
        max_length=20,
        choices=Format.choices,
        default=Format.OFFLINE
    )
    
    # Организатор
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_exhibitions',
        verbose_name=_('Организатор')
    )
    
    # Соорганизаторы
    co_organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='co_organized_exhibitions',
        verbose_name=_('Соорганизаторы')
    )
    
    # Категория
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='exhibitions',
        verbose_name=_('Категория')
    )
    
    # Дополнительные категории
    additional_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='additional_exhibitions',
        verbose_name=_('Дополнительные категории')
    )
    
    # Теги
    tags = models.ManyToManyField(
        'ExhibitionTag',
        blank=True,
        related_name='exhibitions',
        verbose_name=_('Теги')
    )
    
    # Даты и время
    start_date = models.DateTimeField(_('Дата начала'))
    end_date = models.DateTimeField(_('Дата окончания'))
    registration_start = models.DateTimeField(_('Начало регистрации'), null=True, blank=True)
    registration_deadline = models.DateTimeField(_('Крайний срок регистрации'), null=True, blank=True)
    
    # Место проведения
    venue_name = models.CharField(_('Название площадки'), max_length=200)
    venue_description = models.TextField(_('Описание площадки'), blank=True)
    address = models.TextField(_('Адрес проведения'))
    city = models.CharField(_('Город'), max_length=100)
    region = models.CharField(_('Регион/Область'), max_length=100, blank=True)
    country = models.CharField(_('Страна'), max_length=100, default='Россия')
    postal_code = models.CharField(_('Почтовый индекс'), max_length=10, blank=True)
    
    # Координаты
    latitude = models.DecimalField(_('Широта'), max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(_('Долгота'), max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Онлайн параметры
    online_platform = models.CharField(_('Платформа'), max_length=100, blank=True)
    online_link = models.URLField(_('Ссылка на мероприятие'), blank=True)
    meeting_id = models.CharField(_('ID встречи'), max_length=100, blank=True)
    meeting_password = models.CharField(_('Пароль встречи'), max_length=100, blank=True)
    
    # Медиа
    logo = models.ImageField(
        _('Логотип выставки'), 
        upload_to='exhibition_logos/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 300x300 пикселей')
    )
    banner_image = models.ImageField(
        _('Баннер'), 
        upload_to='exhibition_banners/', 
        blank=True, 
        null=True,
        help_text=_('Рекомендуемый размер: 1200x400 пикселей')
    )
    
    # Контактная информация
    contact_person = models.CharField(_('Контактное лицо'), max_length=100, blank=True)
    contact_email = models.EmailField(_('Контактный email'), blank=True)
    contact_phone = models.CharField(_('Контактный телефон'), max_length=20, blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)
    
    # Стоимость участия
    is_free = models.BooleanField(_('Бесплатное участие'), default=False)
    visitor_fee = models.DecimalField(
        _('Стоимость для посетителей'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    exhibitor_fee = models.DecimalField(
        _('Стоимость для экспонентов'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(_('Валюта'), max_length=3, default='RUB')
    
    # Ограничения
    max_participants = models.PositiveIntegerField(_('Максимальное количество участников'), null=True, blank=True)
    max_exhibitors = models.PositiveIntegerField(_('Максимальное количество экспонентов'), null=True, blank=True)
    min_age = models.PositiveIntegerField(_('Минимальный возраст'), null=True, blank=True)
    
    # Требования
    dress_code = models.CharField(_('Дресс-код'), max_length=200, blank=True)
    requirements = models.TextField(_('Требования к участникам'), blank=True)
    
    # Статус и модерация
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    rejection_reason = models.TextField(_('Причина отклонения'), blank=True)
    moderator_notes = models.TextField(_('Заметки модератора'), blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_exhibitions',
        verbose_name=_('Модератор')
    )
    moderated_at = models.DateTimeField(_('Дата модерации'), null=True, blank=True)
    
    # Статистика
    views_count = models.PositiveIntegerField(_('Количество просмотров'), default=0)
    favorites_count = models.PositiveIntegerField(_('Количество добавлений в избранное'), default=0)
    registrations_count = models.PositiveIntegerField(_('Количество регистраций'), default=0)
    
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
    is_featured = models.BooleanField(_('Рекомендуемая'), default=False)
    is_premium = models.BooleanField(_('Премиум размещение'), default=False)
    is_recurring = models.BooleanField(_('Регулярное мероприятие'), default=False)
    
    # Даты
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    published_at = models.DateTimeField(_('Дата публикации'), null=True, blank=True)
    
    # Менеджер
    objects = ExhibitionManager()

    class Meta:
        verbose_name = _('Выставка')
        verbose_name_plural = _('Выставки')
        db_table = 'exhibitions'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['-views_count']),
            models.Index(fields=['-rating']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Автоматическое создание slug
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Exhibition.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Устанавливаем дату публикации
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        # Автоматическое завершение прошедших выставок
        if self.end_date < timezone.now() and self.status == self.Status.PUBLISHED:
            self.status = self.Status.COMPLETED
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('exhibitions:detail', kwargs={'slug': self.slug})

    @property
    def exhibition_status(self):
        """Определяет статус выставки по датам"""
        now = timezone.now()
        
        if now < self.start_date:
            return 'upcoming'
        elif self.start_date <= now <= self.end_date:
            return 'current'
        else:
            return 'completed'

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_active(self):
        """Проверяет, активна ли выставка"""
        return self.is_published and timezone.now() <= self.end_date

    @property
    def days_until_start(self):
        """Количество дней до начала"""
        if self.start_date > timezone.now():
            return (self.start_date - timezone.now()).days
        return 0

    @property
    def days_until_end(self):
        """Количество дней до окончания"""
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

    @property
    def duration_days(self):
        """Продолжительность в днях"""
        return (self.end_date - self.start_date).days + 1

    @property
    def registration_open(self):
        """Открыта ли регистрация"""
        now = timezone.now()
        
        # Проверяем период регистрации
        if self.registration_start and now < self.registration_start:
            return False
        
        if self.registration_deadline and now > self.registration_deadline:
            return False
        
        return (
            self.is_published and 
            self.exhibition_status == 'upcoming'
        )

    @property
    def can_register(self):
        """Можно ли регистрироваться"""
        if not self.registration_open:
            return False
        
        if self.max_participants:
            return self.registrations_count < self.max_participants
        
        return True

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_registrations(self):
        """Увеличивает счетчик регистраций"""
        self.registrations_count += 1
        self.save(update_fields=['registrations_count'])

    def update_rating(self):
        """Обновляет рейтинг на основе отзывов"""
        from apps.core.models import Review
        reviews = Review.objects.filter(
            exhibition=self,
            status='approved'
        )
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2)
            self.reviews_count = reviews.count()
        else:
            self.rating = 0.00
            self.reviews_count = 0
        self.save(update_fields=['rating', 'reviews_count'])

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать выставку"""
        return (
            user == self.organizer or 
            user in self.co_organizers.all() or
            user.is_admin_user or 
            user.is_superuser
        )

    def can_moderate(self, user):
        """Может ли пользователь модерировать выставку"""
        return user.is_admin_user or user.is_superuser

    def get_participants_by_type(self, participation_type):
        """Возвращает участников по типу"""
        from apps.companies.models import ExhibitionParticipant
        return ExhibitionParticipant.objects.filter(
            exhibition=self,
            participation_type=participation_type
        )

    def get_exhibitors(self):
        """Возвращает экспонентов"""
        return self.get_participants_by_type('exhibitor')

    def get_sponsors(self):
        """Возвращает спонсоров"""
        return self.get_participants_by_type('sponsor')

    def get_speakers(self):
        """Возвращает спикеров"""
        return self.get_participants_by_type('speaker')

    @property
    def completion_percentage(self):
        """Процент заполнения информации о выставке"""
        fields_to_check = [
            'description', 'short_description', 'venue_name', 'address',
            'contact_person', 'contact_email', 'contact_phone', 'website'
        ]
        filled_fields = sum(1 for field in fields_to_check if getattr(self, field))
        
        # Добавляем баллы за медиа
        if self.logo:
            filled_fields += 1
        if self.banner_image:
            filled_fields += 1
        if self.images.exists():
            filled_fields += 1
        if self.documents.exists():
            filled_fields += 1
        
        total_fields = len(fields_to_check) + 4
        return int((filled_fields / total_fields) * 100)

    def get_price_display(self):
        """Отображение цены"""
        if self.is_free:
            return 'Бесплатно'
        
        currency_symbols = {'RUB': '₽', 'USD': '$', 'EUR': '€'}
        symbol = currency_symbols.get(self.currency, self.currency)
        
        if self.visitor_fee:
            return f"от {self.visitor_fee:,.0f} {symbol}"
        
        return 'По запросу'

    def get_related_exhibitions(self, limit=5):
        """Возвращает похожие выставки"""
        return Exhibition.objects.published().filter(
            category=self.category
        ).exclude(pk=self.pk).order_by('-rating', '-views_count')[:limit]


class ExhibitionTag(models.Model):
    """Теги для выставок"""
    
    name = models.CharField(_('Название'), max_length=50, unique=True)
    slug = models.SlugField(_('Slug'), max_length=50, unique=True, blank=True)
    color = models.CharField(_('Цвет'), max_length=7, default='#6c757d')
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активен'), default=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Тег выставки')
        verbose_name_plural = _('Теги выставок')
        db_table = 'exhibition_tags'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def exhibitions_count(self):
        """Количество выставок с этим тегом"""
        return self.exhibitions.filter(status='published').count()


class ExhibitionImage(models.Model):
    """Дополнительные изображения выставки"""
    
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Выставка')
    )
    image = models.ImageField(_('Изображение'), upload_to='exhibition_images/')
    title = models.CharField(_('Название'), max_length=200, blank=True)
    caption = models.CharField(_('Подпись'), max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Изображение выставки')
        verbose_name_plural = _('Изображения выставки')
        db_table = 'exhibition_images'
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"Изображение для {self.exhibition.title} - {self.title or self.id}"


class ExhibitionDocument(models.Model):
    """Документы выставки"""
    
    class DocumentType(models.TextChoices):
        PROGRAM = 'program', _('Программа мероприятия')
        PRESENTATION = 'presentation', _('Презентация')
        BROCHURE = 'brochure', _('Брошюра')
        PRICE_LIST = 'price_list', _('Прайс-лист')
        REGULATIONS = 'regulations', _('Регламент')
        CONTRACT = 'contract', _('Договор')
        OTHER = 'other', _('Другое')
    
    exhibition = models.ForeignKey(
        Exhibition,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Выставка')
    )
    title = models.CharField(_('Название документа'), max_length=200)
    document_type = models.CharField(
        _('Тип документа'),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    file = models.FileField(_('Файл'), upload_to='exhibition_documents/')
    description = models.TextField(_('Описание'), blank=True)
    file_size = models.PositiveIntegerField(_('Размер файла'), null=True, blank=True)
    download_count = models.PositiveIntegerField(_('Количество скачиваний'), default=0)
    
    is_public = models.BooleanField(_('Публичный доступ'), default=True)
    
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Документ выставки')
        verbose_name_plural = _('Документы выставки')
        db_table = 'exhibition_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.exhibition.title}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def increment_downloads(self):
        """Увеличивает счетчик скачиваний"""
        self.download_count += 1
        self.save(update_fields=['download_count'])

    @property
    def file_size_display(self):
        """Отображение размера файла"""
        if not self.file_size:
            return 'Неизвестно'
        
        for unit in ['байт', 'КБ', 'МБ', 'ГБ']:
            if self.file_size < 1024:
                return f"{self.file_size} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} ГБ"


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
        
        # Заметки пользователя
        notes = models.TextField(_('Заметки'), blank=True)
        
        # Напоминания
        reminder_date = models.DateTimeField(_('Дата напоминания'), null=True, blank=True)
        is_reminded = models.BooleanField(_('Напоминание отправлено'), default=False)

        class Meta:
            verbose_name = _('Избранная выставка')
            verbose_name_plural = _('Избранные выставки')
            db_table = 'favorite_exhibitions'
            unique_together = ('user', 'exhibition')
            ordering = ['-created_at']

        def __str__(self):
            return f"{self.user.email} - {self.exhibition.title}"


    class ExhibitionRegistration(models.Model):
        """Регистрация на выставку"""
        
        class RegistrationType(models.TextChoices):
            VISITOR = 'visitor', _('Посетитель')
            EXHIBITOR = 'exhibitor', _('Экспонент')
            SPEAKER = 'speaker', _('Спикер')
            PRESS = 'press', _('Пресса')
            VIP = 'vip', _('VIP')
        
        class Status(models.TextChoices):
            PENDING = 'pending', _('Ожидает подтверждения')
            CONFIRMED = 'confirmed', _('Подтвержден')
            CANCELLED = 'cancelled', _('Отменен')
            ATTENDED = 'attended', _('Посетил')
            NO_SHOW = 'no_show', _('Не явился')
        
        exhibition = models.ForeignKey(
            Exhibition,
            on_delete=models.CASCADE,
            related_name='registrations',
            verbose_name=_('Выставка')
        )
        user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='exhibition_registrations',
            verbose_name=_('Пользователь'),
            null=True,
            blank=True
        )
        
        # Информация о регистрации (для незарегистрированных пользователей)
        first_name = models.CharField(_('Имя'), max_length=100)
        last_name = models.CharField(_('Фамилия'), max_length=100)
        email = models.EmailField(_('Email'))
        phone = models.CharField(_('Телефон'), max_length=20, blank=True)
        company_name = models.CharField(_('Компания'), max_length=200, blank=True)
        position = models.CharField(_('Должность'), max_length=100, blank=True)
        
        # Тип регистрации
        registration_type = models.CharField(
            _('Тип регистрации'),
            max_length=20,
            choices=RegistrationType.choices,
            default=RegistrationType.VISITOR
        )
        
        # Статус
        status = models.CharField(
            _('Статус'),
            max_length=20,
            choices=Status.choices,
            default=Status.PENDING
        )
        
        # Дополнительная информация
        interests = models.TextField(_('Интересы/Цели посещения'), blank=True)
        dietary_requirements = models.CharField(_('Диетические требования'), max_length=200, blank=True)
        accessibility_needs = models.CharField(_('Потребности в доступности'), max_length=200, blank=True)
        
        # QR код для входа
        qr_code = models.CharField(_('QR код'), max_length=100, unique=True, blank=True)
        
        # Подтверждение и посещение
        confirmed_at = models.DateTimeField(_('Дата подтверждения'), null=True, blank=True)
        attended_at = models.DateTimeField(_('Дата посещения'), null=True, blank=True)
        check_in_notes = models.TextField(_('Заметки при регистрации'), blank=True)
        
        # Метаданные
        ip_address = models.GenericIPAddressField(_('IP адрес'), null=True, blank=True)
        user_agent = models.TextField(_('User Agent'), blank=True)
        source = models.CharField(_('Источник регистрации'), max_length=100, blank=True)
        
        created_at = models.DateTimeField(_('Дата регистрации'), auto_now_add=True)
        updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

        class Meta:
            verbose_name = _('Регистрация на выставку')
            verbose_name_plural = _('Регистрации на выставки')
            db_table = 'exhibition_registrations'
            unique_together = ('exhibition', 'email')
            ordering = ['-created_at']
            indexes = [
                models.Index(fields=['exhibition', 'status']),
                models.Index(fields=['user']),
                models.Index(fields=['email']),
                models.Index(fields=['qr_code']),
                models.Index(fields=['-created_at']),
            ]

        def __str__(self):
            return f"Регистрация {self.get_full_name()} на {self.exhibition.title}"

        def save(self, *args, **kwargs):
            # Заполняем информацию из профиля пользователя
            if self.user and not self.first_name:
                self.first_name = self.user.first_name or self.user.email.split('@')[0]
                self.last_name = self.user.last_name
                self.email = self.user.email
                if hasattr(self.user, 'phone'):
                    self.phone = self.user.phone
                if hasattr(self.user, 'company_name'):
                    self.company_name = self.user.company_name
                if hasattr(self.user, 'position'):
                    self.position = self.user.position
            
            # Генерируем QR код
            if not self.qr_code:
                import uuid
                self.qr_code = str(uuid.uuid4())
            
            # Устанавливаем дату подтверждения
            if self.status == self.Status.CONFIRMED and not self.confirmed_at:
                self.confirmed_at = timezone.now()
            
            super().save(*args, **kwargs)
            
            # Увеличиваем счетчик регистраций
            if self._state.adding:  # Только при создании
                self.exhibition.increment_registrations()

        def get_full_name(self):
            """Полное имя"""
            return f"{self.first_name} {self.last_name}".strip()

        def confirm_registration(self):
            """Подтверждает регистрацию"""
            self.status = self.Status.CONFIRMED
            self.confirmed_at = timezone.now()
            self.save()

        def mark_attended(self, notes=''):
            """Отмечает посещение"""
            self.status = self.Status.ATTENDED
            self.attended_at = timezone.now()
            self.check_in_notes = notes
            self.save()

        def generate_ticket_pdf(self):
            """Генерирует PDF билет (заглушка)"""
            # Здесь можно реализовать генерацию PDF с QR кодом
            pass


    class ExhibitionSchedule(models.Model):
        """Расписание мероприятий выставки"""
        
        class EventType(models.TextChoices):
            OPENING = 'opening', _('Торжественное открытие')
            PRESENTATION = 'presentation', _('Презентация')
            SEMINAR = 'seminar', _('Семинар')
            WORKSHOP = 'workshop', _('Мастер-класс')
            PANEL = 'panel', _('Панельная дискуссия')
            NETWORKING = 'networking', _('Нетворкинг')
            BREAK = 'break', _('Перерыв')
            LUNCH = 'lunch', _('Обед')
            CLOSING = 'closing', _('Закрытие')
            OTHER = 'other', _('Другое')
        
        exhibition = models.ForeignKey(
            Exhibition,
            on_delete=models.CASCADE,
            related_name='schedule',
            verbose_name=_('Выставка')
        )
        
        title = models.CharField(_('Название мероприятия'), max_length=200)
        description = models.TextField(_('Описание'), blank=True)
        event_type = models.CharField(
            _('Тип мероприятия'),
            max_length=20,
            choices=EventType.choices,
            default=EventType.OTHER
        )
        
        # Время
        start_time = models.DateTimeField(_('Время начала'))
        end_time = models.DateTimeField(_('Время окончания'))
        
        # Место
        location = models.CharField(_('Место проведения'), max_length=200, blank=True)
        room = models.CharField(_('Зал/Комната'), max_length=100, blank=True)
        
        # Спикеры
        speakers = models.ManyToManyField(
            'ExhibitionSpeaker',
            blank=True,
            related_name='schedule_events',
            verbose_name=_('Спикеры')
        )
        
        # Дополнительная информация
        max_attendees = models.PositiveIntegerField(_('Максимум участников'), null=True, blank=True)
        registration_required = models.BooleanField(_('Требуется регистрация'), default=False)
        is_featured = models.BooleanField(_('Рекомендуемое'), default=False)
        
        # Онлайн параметры
        online_link = models.URLField(_('Ссылка на онлайн-трансляцию'), blank=True)
        
        created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
        updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

        class Meta:
            verbose_name = _('Событие расписания')
            verbose_name_plural = _('Расписание выставки')
            db_table = 'exhibition_schedule'
            ordering = ['start_time']

        def __str__(self):
            return f"{self.exhibition.title} - {self.title}"

        @property
        def duration_minutes(self):
            """Продолжительность в минутах"""
            return int((self.end_time - self.start_time).total_seconds() / 60)

        @property
        def is_current(self):
            """Проходит ли мероприятие сейчас"""
            now = timezone.now()
            return self.start_time <= now <= self.end_time

        @property
        def is_upcoming(self):
            """Предстоящее ли мероприятие"""
            return timezone.now() < self.start_time


    class ExhibitionSpeaker(models.Model):
        """Спикеры выставки"""
        
        exhibition = models.ForeignKey(
            Exhibition,
            on_delete=models.CASCADE,
            related_name='speakers',
            verbose_name=_('Выставка')
        )
        
        # Личная информация
        first_name = models.CharField(_('Имя'), max_length=100)
        last_name = models.CharField(_('Фамилия'), max_length=100)
        title = models.CharField(_('Звание/Степень'), max_length=100, blank=True)
        bio = models.TextField(_('Биография'))
        
        # Профессиональная информация
        company = models.CharField(_('Компания'), max_length=200, blank=True)
        position = models.CharField(_('Должность'), max_length=200, blank=True)
        
        # Контакты
        email = models.EmailField(_('Email'), blank=True)
        phone = models.CharField(_('Телефон'), max_length=20, blank=True)
        website = models.URLField(_('Веб-сайт'), blank=True)
        
        # Медиа
        photo = models.ImageField(
            _('Фотография'),
            upload_to='speakers/',
            blank=True,
            null=True,
            help_text=_('Рекомендуемый размер: 300x300 пикселей')
        )
        
        # Социальные сети
        linkedin_url = models.URLField(_('LinkedIn'), blank=True)
        twitter_url = models.URLField(_('Twitter'), blank=True)
        
        # Настройки
        is_keynote = models.BooleanField(_('Ключевой спикер'), default=False)
        is_featured = models.BooleanField(_('Рекомендуемый'), default=False)
        sort_order = models.PositiveIntegerField(_('Порядок'), default=0)
        
        created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
        updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

        class Meta:
            verbose_name = _('Спикер выставки')
            verbose_name_plural = _('Спикеры выставки')
            db_table = 'exhibition_speakers'
            ordering = ['sort_order', 'last_name', 'first_name']

        def __str__(self):
            return f"{self.get_full_name()} - {self.exhibition.title}"

        def get_full_name(self):
            """Полное имя"""
            name_parts = []
            if self.title:
                name_parts.append(self.title)
            name_parts.extend([self.first_name, self.last_name])
            return ' '.join(name_parts)

        def get_short_bio(self, max_length=200):
            """Краткая биография"""
            if len(self.bio) <= max_length:
                return self.bio
            return self.bio[:max_length].rsplit(' ', 1)[0] + '...'


    class ExhibitionSponsor(models.Model):
        """Спонсоры выставки"""
        
        class SponsorType(models.TextChoices):
            TITLE = 'title', _('Титульный спонсор')
            GENERAL = 'general', _('Генеральный спонсор')
            OFFICIAL = 'official', _('Официальный спонсор')
            PARTNER = 'partner', _('Партнер')
            MEDIA = 'media', _('Медиа-партнер')
            TECH = 'tech', _('Технический партнер')
            SUPPORTER = 'supporter', _('Поддерживающий партнер')
        
        exhibition = models.ForeignKey(
            Exhibition,
            on_delete=models.CASCADE,
            related_name='sponsors',
            verbose_name=_('Выставка')
        )
        
        # Основная информация
        name = models.CharField(_('Название'), max_length=200)
        description = models.TextField(_('Описание'), blank=True)
        sponsor_type = models.CharField(
            _('Тип спонсорства'),
            max_length=20,
            choices=SponsorType.choices,
            default=SponsorType.PARTNER
        )
        
        # Медиа
        logo = models.ImageField(
            _('Логотип'),
            upload_to='sponsors/',
            help_text=_('Рекомендуемый размер: 300x150 пикселей')
        )
        
        # Контакты
        website = models.URLField(_('Веб-сайт'), blank=True)
        contact_email = models.EmailField(_('Контактный email'), blank=True)
        
        # Настройки отображения
        sort_order = models.PositiveIntegerField(_('Порядок'), default=0)
        is_featured = models.BooleanField(_('Показывать на главной'), default=True)
        
        created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

        class Meta:
            verbose_name = _('Спонсор выставки')
            verbose_name_plural = _('Спонсоры выставки')
            db_table = 'exhibition_sponsors'
            ordering = ['sort_order', 'name']

        def __str__(self):
            return f"{self.name} - {self.exhibition.title}"


    class ExhibitionAnalytics(models.Model):
        """Аналитика по выставкам"""
        
        class MetricType(models.TextChoices):
            VIEWS = 'views', _('Просмотры')
            REGISTRATIONS = 'registrations', _('Регистрации')
            FAVORITES = 'favorites', _('Добавления в избранное')
            DOCUMENT_DOWNLOADS = 'document_downloads', _('Скачивания документов')
            WEBSITE_CLICKS = 'website_clicks', _('Клики на сайт')
            CONTACT_CLICKS = 'contact_clicks', _('Клики на контакты')
        
        exhibition = models.ForeignKey(
            Exhibition,
            on_delete=models.CASCADE,
            related_name='analytics',
            verbose_name=_('Выставка')
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
            verbose_name = _('Аналитика выставки')
            verbose_name_plural = _('Аналитика выставок')
            db_table = 'exhibition_analytics'
            unique_together = ('exhibition', 'metric_type', 'date')
            ordering = ['-date']
            indexes = [
                models.Index(fields=['exhibition', 'metric_type']),
                models.Index(fields=['date']),
                models.Index(fields=['-created_at']),
            ]

        def __str__(self):
            return f"{self.exhibition.title} - {self.get_metric_type_display()} - {self.date}"

        @classmethod
        def record_metric(cls, exhibition, metric_type, value=1, date=None, **kwargs):
            """Записывает метрику"""
            if date is None:
                date = timezone.now().date()
            
            metric, created = cls.objects.get_or_create(
                exhibition=exhibition,
                metric_type=metric_type,
                date=date,
                defaults={'value': value, **kwargs}
            )
            
            if not created:
                metric.value += value
                metric.save(update_fields=['value'])
            
            return metric

        @classmethod
        def get_exhibition_stats(cls, exhibition, start_date=None, end_date=None):
            """Получает статистику выставки за период"""
            queryset = cls.objects.filter(exhibition=exhibition)
            
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


    # Сигналы для автоматических действи

    from django.db.models.signals import post_save, post_delete
    from django.dispatch import receiver

    @receiver(post_save, sender=Exhibition)
    def exhibition_post_save(sender, instance, created, **kwargs):
        """Действия после сохранения выставки"""
        if created:
            # Логируем создание выставки
            try:
                from apps.users.models import UserActivity
                UserActivity.log_activity(
                    user=instance.organizer,
                    activity_type=UserActivity.ActivityType.EXHIBITION_CREATE,
                    description=f"Создана выставка: {instance.title}"
                )
            except ImportError:
                pass

    @receiver(post_save, sender=FavoriteExhibition)
    def favorite_exhibition_post_save(sender, instance, created, **kwargs):
        """Действия после добавления в избранное"""
        if created:
            # Увеличиваем счетчик
            instance.exhibition.favorites_count += 1
            instance.exhibition.save(update_fields=['favorites_count'])
            
            # Логируем активность
            try:
                from apps.users.models import UserActivity
                UserActivity.log_activity(
                    user=instance.user,
                    activity_type=UserActivity.ActivityType.FAVORITE_ADD,
                    description=f"Добавлена в избранное выставка: {instance.exhibition.title}"
                )
            except ImportError:
                pass

    @receiver(post_delete, sender=FavoriteExhibition)
    def favorite_exhibition_post_delete(sender, instance, **kwargs):
        """Действия после удаления из избранного"""
        # Уменьшаем счетчик
        if instance.exhibition.favorites_count > 0:
            instance.exhibition.favorites_count -= 1
            instance.exhibition.save(update_fields=['favorites_count'])
        
        # Логируем активность
        try:
            from apps.users.models import UserActivity
            UserActivity.log_activity(
                user=instance.user,
                activity_type=UserActivity.ActivityType.FAVORITE_REMOVE,
                description=f"Удалена из избранного выставка: {instance.exhibition.title}"
            )
        except ImportError:
            pass

    @receiver(post_save, sender=ExhibitionRegistration)
    def exhibition_registration_post_save(sender, instance, created, **kwargs):
        """Действия после регистрации на выставку"""
        if created:
            # Записываем в аналитику
            ExhibitionAnalytics.record_metric(
                exhibition=instance.exhibition,
                metric_type=ExhibitionAnalytics.MetricType.REGISTRATIONS
            )




    # Дополнительные QuerySet и методы
    class ExhibitionQuerySet(models.QuerySet):
        """Дополнительные методы для запросов выставок"""
        
        def with_location(self):
            """Выставки с указанным местоположением"""
            return self.exclude(
                models.Q(city='') | models.Q(city__isnull=True)
            )
        
        def with_contacts(self):
            """Выставки с контактной информацией"""
            return self.exclude(
                models.Q(contact_email='') & 
                models.Q(contact_phone='') & 
                models.Q(website='')
            )
        
        def this_month(self):
            """Выставки в этом месяце"""
            from django.utils import timezone
            now = timezone.now()
            return self.filter(
                start_date__year=now.year,
                start_date__month=now.month
            )
        
        def next_month(self):
            """Выставки в следующем месяце"""
            from django.utils import timezone
            import calendar
            
            now = timezone.now()
            if now.month == 12:
                next_month = 1
                next_year = now.year + 1
            else:
                next_month = now.month + 1
                next_year = now.year
                
            return self.filter(
                start_date__year=next_year,
                start_date__month=next_month
            )
        
        def by_rating(self, min_rating=3.0):
            """Выставки с рейтингом выше указанного"""
            return self.filter(rating__gte=min_rating)
        
        def free_events(self):
            """Бесплатные мероприятия"""
            return self.filter(is_free=True)
        
        def paid_events(self):
            """Платные мероприятия"""
            return self.filter(is_free=False)
        
        def online_events(self):
            """Онлайн мероприятия"""
            return self.filter(format__in=['online', 'hybrid'])
        
        def offline_events(self):
            """Оффлайн мероприятия"""
            return self.filter(format__in=['offline', 'hybrid'])

    # Добавляем QuerySet к менеджеру
    ExhibitionManager = ExhibitionManager.from_queryset(ExhibitionQuerySet)
    Exhibition.add_to_class('objects', ExhibitionManager())