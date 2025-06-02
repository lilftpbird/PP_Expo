# exhibition_service/apps/users/views.py
import secrets
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from .models import User, UserProfile, EmailVerificationToken, PasswordResetToken
from .forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    PasswordResetRequestForm, 
    PasswordResetForm,
    UserProfileForm
)


class RegisterView(View):
    """Регистрация нового пользователя"""
    template_name = 'users/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:index')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('core:index')
            
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Создаем пользователя
            user = form.save(commit=False)
            user.is_active = True  # Пользователь активен, но email не подтвержден
            user.gdpr_consent_date = timezone.now()
            user.save()
            
            # Создаем профиль пользователя
            UserProfile.objects.create(user=user)
            
            # Создаем токен для подтверждения email
            token = secrets.token_urlsafe(32)
            EmailVerificationToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # Отправляем email с подтверждением
            self.send_verification_email(user, token, request)
            
            messages.success(
                request, 
                'Регистрация прошла успешно! Проверьте свою почту для подтверждения email.'
            )
            return redirect('users:login')
        
        return render(request, self.template_name, {'form': form})
    
    def send_verification_email(self, user, token, request):
        """Отправка email с подтверждением"""
        verification_url = request.build_absolute_uri(
            reverse('users:verify_email', kwargs={'token': token})
        )
        
        subject = 'Подтверждение регистрации на ПП Expo'
        message = f'''
        Здравствуйте, {user.first_name or user.username}!
        
        Спасибо за регистрацию на нашем сайте ПП Expo.
        
        Для подтверждения вашего email адреса, пожалуйста, перейдите по ссылке:
        {verification_url}
        
        Ссылка действительна в течение 24 часов.
        
        Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.
        
        С уважением,
        Команда ПП Expo
        '''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            messages.warning(
                request, 
                'Не удалось отправить письмо с подтверждением. Обратитесь в поддержку.'
            )


class LoginView(View):
    """Вход пользователя в систему"""
    template_name = 'users/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:index')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('core:index')
            
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                
                # Перенаправляем на запрошенную страницу или на главную
                next_page = request.GET.get('next', 'core:index')
                messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.email}!')
                return redirect(next_page)
            else:
                messages.error(request, 'Неверный email или пароль.')
        
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Выход пользователя из системы"""
    
    def post(self, request):
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы.')
        return redirect('core:index')
    
    def get(self, request):
        return redirect('users:login')


class EmailVerificationView(View):
    """Подтверждение email адреса"""
    
    def get(self, request, token):
        try:
            verification_token = get_object_or_404(
                EmailVerificationToken, 
                token=token
            )
            
            if not verification_token.is_valid:
                messages.error(
                    request, 
                    'Ссылка для подтверждения недействительна или истекла.'
                )
                return redirect('users:login')
            
            # Подтверждаем email
            user = verification_token.user
            user.is_email_verified = True
            user.save()
            
            # Помечаем токен как использованный
            verification_token.is_used = True
            verification_token.save()
            
            messages.success(
                request, 
                'Email успешно подтвержден! Теперь вы можете пользоваться всеми функциями сайта.'
            )
            
            # Автоматически входим в систему
            login(request, user)
            return redirect('core:index')
            
        except Exception as e:
            messages.error(request, 'Произошла ошибка при подтверждении email.')
            return redirect('users:login')


class PasswordResetRequestView(View):
    """Запрос на сброс пароля"""
    template_name = 'users/password_reset_request.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:index')
        form = PasswordResetRequestForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Деактивируем старые токены
                PasswordResetToken.objects.filter(
                    user=user, 
                    is_used=False
                ).update(is_used=True)
                
                # Создаем новый токен
                token = secrets.token_urlsafe(32)
                PasswordResetToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=timezone.now() + timedelta(hours=2)
                )
                
                # Отправляем email
                self.send_reset_email(user, token, request)
                
                messages.success(
                    request,
                    'Инструкции по сбросу пароля отправлены на ваш email.'
                )
                return redirect('users:login')
                
            except User.DoesNotExist:
                messages.success(
                    request,
                    'Если такой email существует, инструкции будут отправлены.'
                )
                return redirect('users:login')
        
        return render(request, self.template_name, {'form': form})
    
    def send_reset_email(self, user, token, request):
        """Отправка email со ссылкой для сброса пароля"""
        reset_url = request.build_absolute_uri(
            reverse('users:password_reset', kwargs={'token': token})
        )
        
        subject = 'Сброс пароля на ПП Expo'
        message = f'''
        Здравствуйте, {user.first_name or user.username}!
        
        Вы запросили сброс пароля для вашего аккаунта на ПП Expo.
        
        Для установки нового пароля перейдите по ссылке:
        {reset_url}
        
        Ссылка действительна в течение 2 часов.
        
        Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
        
        С уважением,
        Команда ПП Expo
        '''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            messages.warning(
                request,
                'Не удалось отправить email. Обратитесь в поддержку.'
            )


class PasswordResetView(View):
    """Сброс пароля по токену"""
    template_name = 'users/password_reset.html'
    
    def get(self, request, token):
        try:
            reset_token = get_object_or_404(PasswordResetToken, token=token)
            
            if not reset_token.is_valid:
                messages.error(
                    request, 
                    'Ссылка для сброса пароля недействительна или истекла.'
                )
                return redirect('users:password_reset_request')
            
            form = PasswordResetForm()
            return render(request, self.template_name, {
                'form': form, 
                'token': token
            })
            
        except Exception as e:
            messages.error(request, 'Недействительная ссылка для сброса пароля.')
            return redirect('users:password_reset_request')
    
    def post(self, request, token):
        try:
            reset_token = get_object_or_404(PasswordResetToken, token=token)
            
            if not reset_token.is_valid:
                messages.error(request, 'Ссылка недействительна или истекла.')
                return redirect('users:password_reset_request')
            
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data['password']
                
                # Обновляем пароль
                user = reset_token.user
                user.set_password(password)
                user.save()
                
                # Помечаем токен как использованный
                reset_token.is_used = True
                reset_token.save()
                
                messages.success(
                    request, 
                    'Пароль успешно изменен! Войдите с новым паролем.'
                )
                return redirect('users:login')
            
            return render(request, self.template_name, {
                'form': form, 
                'token': token
            })
            
        except Exception as e:
            messages.error(request, 'Произошла ошибка при сбросе пароля.')
            return redirect('users:password_reset_request')


@method_decorator(login_required, name='dispatch')
class ProfileView(LoginRequiredMixin, View):
    """Профиль пользователя"""
    template_name = 'users/profile.html'
    
    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(instance=profile)
        return render(request, self.template_name, {
            'form': form,
            'profile': profile
        })
    
    def post(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile')
        
        return render(request, self.template_name, {
            'form': form,
            'profile': profile
        })


class ResendVerificationView(View):
    """Повторная отправка письма с подтверждением"""
    
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Необходима авторизация'}, status=401)
        
        if request.user.is_email_verified:
            return JsonResponse({'error': 'Email уже подтвержден'}, status=400)
        
        # Деактивируем старые токены
        EmailVerificationToken.objects.filter(
            user=request.user, 
            is_used=False
        ).update(is_used=True)
        
        # Создаем новый токен
        token = secrets.token_urlsafe(32)
        EmailVerificationToken.objects.create(
            user=request.user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Отправляем email
        verification_url = request.build_absolute_uri(
            reverse('users:verify_email', kwargs={'token': token})
        )
        
        try:
            send_mail(
                'Подтверждение email на ПП Expo',
                f'Ссылка для подтверждения: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            return JsonResponse({'success': 'Письмо отправлено'})
        except Exception as e:
            return JsonResponse({'error': 'Ошибка отправки'}, status=500)
