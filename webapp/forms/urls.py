# forms/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Basic pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset URLs (Django built-in views)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='forms/password_reset.html'
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='forms/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='forms/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='forms/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # User pages
    path('form/', views.form_view, name='form'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Admin pages
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/submission/<int:submission_id>/', 
         views.admin_submission_detail, 
         name='admin_submission_detail'),
    
    # AJAX endpoints
    path('api/notification/<int:notification_id>/read/', 
         views.mark_notification_read, 
         name='mark_notification_read'),
    path('api/user-stats/', views.get_user_stats, name='user_stats'),
]