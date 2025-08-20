# forms/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import FormSubmission, UserProfile, Notification

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

# Enhanced User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'submission_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def submission_count(self, obj):
        count = obj.submissions.count()
        url = reverse("admin:forms_formsubmission_changelist") + f"?user__id__exact={obj.id}"
        return format_html('<a href="{}">{} submissions</a>', url, count)
    submission_count.short_description = 'Submissions'

# Unregister the default User admin and register our enhanced version
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'status', 'created_at', 'file_link')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'name', 'details')
    readonly_fields = ('created_at', 'updated_at', 'user_link', 'file_link')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('user_link', 'name', 'details', 'file_link')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'User'
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download File</a>', obj.file.url)
        return 'No file'
    file_link.short_description = 'File'
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Create notification when status changes
            Notification.objects.create(
                user=obj.user,
                title="Submission Status Updated",
                message=f"Your submission '{obj.name}' status has been changed to '{obj.get_status_display()}'"
            )
        super().save_model(request, obj, form, change)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'phone_number', 'created_at')
    list_filter = ('department', 'created_at')
    search_fields = ('user__username', 'user__email', 'department', 'phone_number')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

# Customize admin site headers
admin.site.site_header = "ANNI Admin Panel"
admin.site.site_title = "ANNI Admin"
admin.site.index_title = "Welcome to ANNI Administration"