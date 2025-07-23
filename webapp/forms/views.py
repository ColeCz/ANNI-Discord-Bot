# forms/views.py

from django.shortcuts import render

def home_view(request):
    return render(request, "forms/home.html")

def form_view(request):
    return render(request, "forms/form.html")

def about_view(request):
    return render(request, "forms/about.html")
