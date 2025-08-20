# forms/utils.py - Enhanced helper functions

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import FormSubmission, Notification, UserProfile
import logging

logger = logging.getLogger('forms')

def send_notification_email(user, subject, template_name, context):
    """
    Send notification email to user
    """
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Notification email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return False

def create_notification(user, title, message, email_template=None):
    """
    Create a notification and optionally send email
    """
    try:
        # Create in-app notification
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message
        )
        
        # Send email notification if template provided
        if email_template:
            context = {
                'user': user,
                'notification': notification,
                'site_name': 'ANNI Bot Dashboard'
            }
            send_notification_email(
                user=user,
                subject=title,
                template_name=email_template,
                context=context
            )
        
        logger.info(f"Notification created for user {user.username}: {title}")
        return notification
        
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None

def get_user_statistics(user):
    """
    Get comprehensive statistics for a user
    """
    submissions = FormSubmission.objects.filter(user=user)
    
    stats = {
        'total_submissions': submissions.count(),
        'pending_submissions': submissions.filter(status='pending').count(),
        'approved_submissions': submissions.filter(status='approved').count(),
        'rejected_submissions': submissions.filter(status='rejected').count(),
        'in_progress_submissions': submissions.filter(status='in_progress').count(),
        'unread_notifications': Notification.objects.filter(
            user=user, 
            is_read=False
        ).count(),
        'recent_activity': submissions.order_by('-created_at')[:5],
        'avg_response_time': get_avg_response_time(user),
    }
    
    return stats

def get_avg_response_time(user):
    """
    Calculate average response time for user's submissions
    """
    try:
        processed_submissions = FormSubmission.objects.filter(
            user=user,
            status__in=['approved', 'rejected'],
            updated_at__isnull=False
        )
        
        if processed_submissions.exists():
            total_time = timedelta()
            count = 0
            
            for submission in processed_submissions:
                time_diff = submission.updated_at - submission.created_at
                total_time += time_diff
                count += 1
            
            avg_time = total_time / count
            return avg_time.days
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculating average response time: {str(e)}")
        return None

def get_admin_dashboard_stats():
    """
    Get statistics for admin dashboard
    """
    try:
        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(
                last_login__gte=last_week
            ).count(),
            'new_users_this_month': User.objects.filter(
                date_joined__gte=last_month
            ).count(),
            'total_submissions': FormSubmission.objects.count(),
            'pending_submissions': FormSubmission.objects.filter(
                status='pending'
            ).count(),
            'submissions_this_week': FormSubmission.objects.filter(
                created_at__gte=last_week
            ).count(),
            'status_breakdown': FormSubmission.objects.values('status').annotate(
                count=Count('status')
            ),
            'top_users': User.objects.annotate(
                submission_count=Count('submissions')
            ).order_by('-submission_count')[:5],
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard stats: {str(e)}")
        return {}

def cleanup_old_notifications():
    """
    Clean up old read notifications (older than 30 days)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        old_notifications = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        )
        
        count = old_notifications.count()
        old_notifications.delete()
        
        logger.info(f"Cleaned up {count} old notifications")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {str(e)}")
        return 0

def validate_file_upload(file):
    """
    Validate uploaded file size and type
    """
    # Max file size: 10MB
    max_size = 10 * 1024 * 1024
    
    # Allowed file extensions
    allowed_extensions = [
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.xls', '.xlsx', '.csv', '.zip', '.rar'
    ]
    
    if file.size > max_size:
        return False, "File size exceeds 10MB limit."
    
    file_extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
    if f'.{file_extension}' not in allowed_extensions:
        return False, f"File type '.{file_extension}' is not allowed."
    
    return True, "File is valid."

def generate_submission_report(date_from=None, date_to=None, status=None):
    """
    Generate submission report for given parameters
    """
    try:
        submissions = FormSubmission.objects.all()
        
        if date_from:
            submissions = submissions.filter(created_at__gte=date_from)
        if date_to:
            submissions = submissions.filter(created_at__lte=date_to)
        if status:
            submissions = submissions.filter(status=status)
        
        report_data = {
            'total_submissions': submissions.count(),
            'submissions_by_status': submissions.values('status').annotate(
                count=Count('status')
            ),
            'submissions_by_user': submissions.values(
                'user__username'
            ).annotate(count=Count('user')).order_by('-count')[:10],
            'submissions_by_date': submissions.extra(
                {'day': 'date(created_at)'}
            ).values('day').annotate(count=Count('id')).order_by('day'),
            'avg_processing_time': get_avg_processing_time(submissions),
        }
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating submission report: {str(e)}")
        return {}

def get_avg_processing_time(submissions):
    """
    Calculate average processing time for submissions
    """
    try:
        processed_submissions = submissions.filter(
            status__in=['approved', 'rejected'],
            updated_at__isnull=False
        )
        
        if processed_submissions.exists():
            total_time = timedelta()
            count = 0
            
            for submission in processed_submissions:
                time_diff = submission.updated_at - submission.created_at
                total_time += time_diff
                count += 1
            
            avg_time = total_time / count
            return round(avg_time.total_seconds() / 3600, 2)  # Return hours
        
        return 0
        
    except Exception as e:
        logger.error(f"Error calculating processing time: {str(e)}")
        return 0

def auto_assign_reviewers():
    """
    Auto-assign pending submissions to available staff members
    """
    try:
        pending_submissions = FormSubmission.objects.filter(
            status='pending',
            reviewed_by__isnull=True
        )
        
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        
        if not staff_users.exists():
            return 0
        
        assigned_count = 0
        for submission in pending_submissions:
            # Simple round-robin assignment
            reviewer = staff_users[assigned_count % staff_users.count()]
            submission.reviewed_by = reviewer
            submission.save()
            
            # Notify reviewer
            create_notification(
                user=reviewer,
                title="New Submission Assigned",
                message=f"You have been assigned submission #{submission.id}: {submission.name}"
            )
            
            assigned_count += 1
        
        logger.info(f"Auto-assigned {assigned_count} submissions to reviewers")
        return assigned_count
        
    except Exception as e:
        logger.error(f"Error auto-assigning reviewers: {str(e)}")
        return 0

def get_user_activity_feed(user, limit=10):
    """
    Get recent activity feed for user
    """
    try:
        activities = []
        
        # Recent submissions
        recent_submissions = FormSubmission.objects.filter(
            user=user
        ).order_by('-created_at')[:limit//2]
        
        for submission in recent_submissions:
            activities.append({
                'type': 'submission',
                'timestamp': submission.created_at,
                'title': f'Submitted: {submission.name}',
                'description': f'Status: {submission.get_status_display()}',
                'icon': 'fas fa-file-plus',
                'color': 'primary'
            })
        
        # Recent notifications
        recent_notifications = Notification.objects.filter(
            user=user
        ).order_by('-created_at')[:limit//2]
        
        for notification in recent_notifications:
            activities.append({
                'type': 'notification',
                'timestamp': notification.created_at,
                'title': notification.title,
                'description': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                'icon': 'fas fa-bell',
                'color': 'info'
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:limit]
        
    except Exception as e:
        logger.error(f"Error getting user activity feed: {str(e)}")
        return []

def bulk_update_submission_status(submission_ids, new_status, admin_user, notes=""):
    """
    Bulk update submission statuses
    """
    try:
        submissions = FormSubmission.objects.filter(id__in=submission_ids)
        updated_count = 0
        
        for submission in submissions:
            old_status = submission.status
            submission.status = new_status
            submission.reviewed_by = admin_user
            if notes:
                submission.admin_notes = notes
            submission.save()
            
            # Create notification for user
            create_notification(
                user=submission.user,
                title="Submission Status Updated",
                message=f"Your submission '{submission.name}' status has been changed from '{old_status}' to '{new_status}'"
            )
            
            updated_count += 1
        
        logger.info(f"Bulk updated {updated_count} submissions to status: {new_status}")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error bulk updating submissions: {str(e)}")
        return 0