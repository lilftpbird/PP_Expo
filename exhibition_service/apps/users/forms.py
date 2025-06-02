# exhibition_service/apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )
    
    first_name = forms.CharField(
        label='Имя',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваше имя'
        })
    )
    
    last_name = forms.CharField(
        label='Фамилия',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваша фамилия'
        })
    )
    
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        })
    )
    
    company_name = forms.CharField(
        label='Компания',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название вашей компании'
        })
    )
    
    position = forms.CharField(
        label='Должность',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваша должность'
        })
    )
    
    role = forms.ChoiceField(
        label='Роль',
        choices=[
            ('visitor', 'Посетитель'),
            ('organizer', 'Организатор'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    gdpr_consent = forms.BooleanField(
        label='Согласие на обработку персональных данных',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )

    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'phone', 
            'company_name', 'position', 'role', 'password1', 
            'password2', 'gdpr_consent'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем поле username, так как используем email
        if 'username' in self.fields:
            del self.fields['username']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_gdpr_consent(self):
        consent = self.cleaned_data.get('gdpr_consent')
        if not consent:
            raise ValidationError(
                'Необходимо дать согласие на обработку персональных данных.'
            )
        return consent

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Используем email как username
        
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Форма входа пользователя"""
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )
    
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    
    remember_me = forms.BooleanField(
        label='Запомнить меня',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise ValidationError('Неверный email или пароль.')
                if not user.is_active:
                    raise ValidationError('Ваш аккаунт деактивирован.')
            except User.DoesNotExist:
                raise ValidationError('Неверный email или пароль.')

        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Форма запроса сброса пароля"""
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            # Не показываем пользователю, что email не существует (безопасность)
            pass
        return email


class PasswordResetForm(forms.Form):
    """Форма установки нового пароля"""
    
    password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль'
        })
    )
    
    password_confirm = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите новый пароль'
        })
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Пароли не совпадают.')

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    # Поля из модели User
    first_name = forms.CharField(
        label='Имя',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваше имя'
        })
    )
    
    last_name = forms.CharField(
        label='Фамилия',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваша фамилия'
        })
    )
    
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        })
    )
    
    company_name = forms.CharField(
        label='Компания',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название вашей компании'
        })
    )
    
    position = forms.CharField(
        label='Должность',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваша должность'
        })
    )

    class Meta:
        model = UserProfile
        fields = [
            'avatar', 'bio', 'website', 'organization_name', 
            'organization_description', 'organization_website', 
            'organization_logo', 'email_notifications', 'marketing_emails'
        ]
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'organization_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название организации'
            }),
            'organization_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание организации...'
            }),
            'organization_website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://organization.com'
            }),
            'organization_logo': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'marketing_emails': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Если есть связанный пользователь, заполняем поля из User
        if self.instance and hasattr(self.instance, 'user'):
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['phone'].initial = user.phone
            self.fields['company_name'].initial = user.company_name
            self.fields['position'].initial = user.position

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Обновляем данные пользователя
        if hasattr(profile, 'user'):
            user = profile.user
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.phone = self.cleaned_data.get('phone', '')
            user.company_name = self.cleaned_data.get('company_name', '')
            user.position = self.cleaned_data.get('position', '')
            
            if commit:
                user.save()
        
        if commit:
            profile.save()
        
        return profile