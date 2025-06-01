from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class SubscriptionPlan(models.Model):
    """Планы подписок для организаторов"""
    
    class PlanType(models.TextChoices):
        BASIC = 'basic', _('Базовая')
        STANDARD = 'standard', _('Стандартная')
        PROFESSIONAL = 'professional', _('Профессиональная')
        EXCLUSIVE = 'exclusive', _('Эксклюзивная')
    
    name = models.CharField(
        max_length=100,
        choices=PlanType.choices,
        unique=True,
        verbose_name=_('Тип плана')
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name=_('Название для отображения')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Цена за месяц (руб.)')
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Цена за год (руб.)')
    )
    max_exhibitions = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Максимальное количество выставок')
    )
    max_companies_per_exhibition = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Максимальное количество компаний на выставку')
    )
    has_advanced_analytics = models.BooleanField(
        default=False,
        verbose_name=_('Расширенная аналитика')
    )
    has_custom_cards = models.BooleanField(
        default=False,
        verbose_name=_('Кастомизация карточек')
    )
    has_promotion_tools = models.BooleanField(
        default=False,
        verbose_name=_('Инструменты продвижения')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
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
        verbose_name = _('План подписки')
        verbose_name_plural = _('Планы подписок')
        ordering = ['price_monthly']

    def __str__(self):
        return self.display_name


class Subscription(models.Model):
    """Подписка пользователя"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Активна')
        EXPIRED = 'expired', _('Истекла')
        CANCELLED = 'cancelled', _('Отменена')
        PENDING = 'pending', _('Ожидает оплаты')
    
    class BillingPeriod(models.TextChoices):
        MONTHLY = 'monthly', _('Ежемесячно')
        YEARLY = 'yearly', _('Ежегодно')
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_('Пользователь')
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('План подписки')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Статус')
    )
    billing_period = models.CharField(
        max_length=20,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
        verbose_name=_('Период оплаты')
    )
    start_date = models.DateTimeField(
        verbose_name=_('Дата начала')
    )
    end_date = models.DateTimeField(
        verbose_name=_('Дата окончания')
    )
    auto_renewal = models.BooleanField(
        default=True,
        verbose_name=_('Автопродление')
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
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.plan.display_name}'

    @property
    def is_active(self):
        """Проверяет, активна ли подписка"""
        return (
            self.status == self.Status.ACTIVE and 
            self.end_date > timezone.now()
        )

    @property
    def days_until_expiry(self):
        """Количество дней до истечения подписки"""
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

    def extend_subscription(self, months=1):
        """Продлевает подписку на указанное количество месяцев"""
        from dateutil.relativedelta import relativedelta
        
        if self.is_active:
            # Продлеваем от текущей даты окончания
            self.end_date += relativedelta(months=months)
        else:
            # Если подписка неактивна, начинаем с текущего момента
            self.start_date = timezone.now()
            self.end_date = self.start_date + relativedelta(months=months)
            self.status = self.Status.ACTIVE
        
        self.save()


class Payment(models.Model):
    """История платежей"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Ожидает оплаты')
        COMPLETED = 'completed', _('Оплачено')
        FAILED = 'failed', _('Ошибка оплаты')
        REFUNDED = 'refunded', _('Возвращено')
        CANCELLED = 'cancelled', _('Отменено')
    
    class PaymentMethod(models.TextChoices):
        ONLINE = 'online', _('Онлайн-платеж')
        INVOICE = 'invoice', _('По счету')
        BANK_TRANSFER = 'bank_transfer', _('Банковский перевод')
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Подписка')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Сумма')
    )
    currency = models.CharField(
        max_length=3,
        default='RUB',
        verbose_name=_('Валюта')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Статус')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.ONLINE,
        verbose_name=_('Способ оплаты')
    )
    external_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Внешний ID платежа')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Дата оплаты')
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
        verbose_name = _('Платеж')
        verbose_name_plural = _('Платежи')
        ordering = ['-created_at']

    def __str__(self):
        return f'Платеж #{self.id} - {self.amount} {self.currency}'


class Invoice(models.Model):
    """Счета для юридических лиц"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        SENT = 'sent', _('Отправлен')
        PAID = 'paid', _('Оплачен')
        OVERDUE = 'overdue', _('Просрочен')
        CANCELLED = 'cancelled', _('Отменен')
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('Подписка')
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Номер счета')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Сумма')
    )
    currency = models.CharField(
        max_length=3,
        default='RUB',
        verbose_name=_('Валюта')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Статус')
    )
    issue_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Дата выставления')
    )
    due_date = models.DateField(
        verbose_name=_('Срок оплаты')
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name=_('Название компании')
    )
    company_address = models.TextField(
        verbose_name=_('Адрес компании')
    )
    company_inn = models.CharField(
        max_length=12,
        verbose_name=_('ИНН')
    )
    company_kpp = models.CharField(
        max_length=9,
        blank=True,
        verbose_name=_('КПП')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
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
        verbose_name = _('Счет')
        verbose_name_plural = _('Счета')
        ordering = ['-created_at']

    def __str__(self):
        return f'Счет №{self.invoice_number}'

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Генерируем номер счета
            from datetime import datetime
            year = datetime.now().year
            count = Invoice.objects.filter(
                created_at__year=year
            ).count() + 1
            self.invoice_number = f'INV-{year}-{count:04d}'
        super().save(*args, **kwargs)
