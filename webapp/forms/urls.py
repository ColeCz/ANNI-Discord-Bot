# forms/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('form/', views.form_view, name='form'),
    path('about/', views.about_view, name='about'),
]
