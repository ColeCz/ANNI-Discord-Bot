# forms/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import FormSubmission, UserProfile, Notification
from .forms import (
    CustomUserCreationForm, 
    FormSubmissionForm, 
    UserProfileForm,
    AdminStatusUpdateForm
)

# Home and basic views
def home_view(request):
    """Enhanced home view with user context"""
    context = {}
    if request.user.is_authenticated:
        recent_submissions = FormSubmission.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        unread_notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        context.update({
            'recent_submissions': recent_submissions,
            'unread_notifications': unread_notifications,
        })
    return render(request, "forms/home.html", context)

# Authentication views
def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            # Create welcome notification
            Notification.objects.create(
                user=user,
                title="Welcome to ANNI!",
                message="Your account has been successfully created. You can now submit forms and track their status."
            )
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'forms/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'forms/login.html')

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# Form submission views
@login_required
def form_view(request):
    """Enhanced form submission view"""
    if request.method == 'POST':
        form = FormSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.save()
            messages.success(request, 'Your submission has been received and is pending review.')
            return redirect('user_dashboard')
    else:
        form = FormSubmissionForm()
    return render(request, "forms/form.html", {'form': form})

@login_required
def user_dashboard(request):
    """User dashboard with submissions and notifications"""
    submissions = FormSubmission.objects.filter(user=request.user)
    notifications = Notification.objects.filter(user=request.user)[:10]
    
    # Pagination for submissions
    paginator = Paginator(submissions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'submissions': page_obj,
        'notifications': notifications,
        'total_submissions': submissions.count(),
        'pending_submissions': submissions.filter(status='pending').count(),
        'approved_submissions': submissions.filter(status='approved').count(),
    }
    return render(request, 'forms/dashboard.html', context)

@login_required
def profile_view(request):
    """User profile view and editing"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'forms/profile.html', {'form': form, 'profile': profile})

# Admin views
def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff

@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """Admin dashboard with submission management"""
    submissions = FormSubmission.objects.all()
    users = User.objects.all()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        submissions = submissions.filter(
            Q(user__username__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(details__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(submissions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'submissions': page_obj,
        'total_users': users.count(),
        'total_submissions': FormSubmission.objects.count(),
        'pending_submissions': FormSubmission.objects.filter(status='pending').count(),
        'status_choices': FormSubmission.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'forms/admin_dashboard.html', context)

@user_passes_test(is_staff_user)
def admin_submission_detail(request, submission_id):
    """Admin view for individual submission management"""
    submission = get_object_or_404(FormSubmission, id=submission_id)
    
    if request.method == 'POST':
        form = AdminStatusUpdateForm(request.POST, instance=submission)
        if form.is_valid():
            updated_submission = form.save(commit=False)
            updated_submission.reviewed_by = request.user
            updated_submission.save()
            
            # Create notification for user
            Notification.objects.create(
                user=submission.user,
                title=f"Submission Status Updated",
                message=f"Your submission '{submission.name}' status has been changed to '{updated_submission.get_status_display()}'"
            )
            
            messages.success(request, 'Submission updated successfully!')
            return redirect('admin_dashboard')
    else:
        form = AdminStatusUpdateForm(instance=submission)
    
    return render(request, 'forms/admin_submission_detail.html', {
        'submission': submission,
        'form': form
    })

# API-like views for AJAX requests
@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def get_user_stats(request):
    """Get user statistics for dashboard"""
    stats = {
        'total_submissions': FormSubmission.objects.filter(user=request.user).count(),
        'pending': FormSubmission.objects.filter(user=request.user, status='pending').count(),
        'approved': FormSubmission.objects.filter(user=request.user, status='approved').count(),
        'rejected': FormSubmission.objects.filter(user=request.user, status='rejected').count(),
    }
    return JsonResponse(stats)

def about_view(request):
    """About page view"""
    return render(request, "forms/about.html")