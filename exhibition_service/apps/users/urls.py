from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Регистрация и вход
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Подтверждение email
    path('verify-email/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    
    # Сброс пароля
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/<str:token>/', views.PasswordResetView.as_view(), name='password_reset'),
    
    # Профиль
    path('profile/', views.ProfileView.as_view(), name='profile'),
]