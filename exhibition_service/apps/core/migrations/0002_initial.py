# Generated by Django 4.2.7 on 2025-06-01 02:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('exhibitions', '0002_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='viewhistory',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='view_history', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='review',
            name='exhibition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='exhibitions.exhibition', verbose_name='Выставка'),
        ),
        migrations.AddField(
            model_name='review',
            name='moderated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moderated_reviews', to=settings.AUTH_USER_MODEL, verbose_name='Модератор'),
        ),
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='notification',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Тип объекта'),
        ),
        migrations.AddField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='favorite',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Тип объекта'),
        ),
        migrations.AddField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='analytics',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Тип объекта'),
        ),
        migrations.AddField(
            model_name='analytics',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='analytics', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddIndex(
            model_name='viewhistory',
            index=models.Index(fields=['user', 'content_type', 'object_id'], name='core_viewhi_user_id_1c1867_idx'),
        ),
        migrations.AddIndex(
            model_name='viewhistory',
            index=models.Index(fields=['content_type', 'object_id'], name='core_viewhi_content_fad3e1_idx'),
        ),
        migrations.AddIndex(
            model_name='viewhistory',
            index=models.Index(fields=['-created_at'], name='core_viewhi_created_98dc53_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('user', 'exhibition')},
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='core_notifi_user_id_cb8f07_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['-created_at'], name='core_notifi_created_f19d5e_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='favorite',
            unique_together={('user', 'content_type', 'object_id')},
        ),
        migrations.AddIndex(
            model_name='analytics',
            index=models.Index(fields=['content_type', 'object_id'], name='core_analyt_content_cc8700_idx'),
        ),
        migrations.AddIndex(
            model_name='analytics',
            index=models.Index(fields=['event_type'], name='core_analyt_event_t_48fd43_idx'),
        ),
        migrations.AddIndex(
            model_name='analytics',
            index=models.Index(fields=['-created_at'], name='core_analyt_created_fdcd57_idx'),
        ),
    ]
