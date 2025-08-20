# forms/management/commands/cleanup_notifications.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from forms.utils import cleanup_old_notifications

class Command(BaseCommand):
    help = 'Clean up old read notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete notifications older than this many days (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        self.stdout.write(f'Cleaning up notifications older than {days} days...')
        
        count = cleanup_old_notifications()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {count} old notifications')
        )

# forms/management/commands/send_digest_emails.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from forms.models import FormSubmission, Notification
from forms.utils import send_notification_email
import logging

logger = logging.getLogger('forms')

class Command(BaseCommand):
    help = 'Send weekly digest emails to users'

    def handle(self, *args, **options):
        self.stdout.write('Sending weekly digest emails...')
        
        # Get users who have submissions or notifications in the last week
        last_week = timezone.now() - timedelta(days=7)
        
        users_with_activity = User.objects.filter(
            Q(submissions__created_at__gte=last_week) |
            Q(notifications__created_at__gte=last_week)
        ).distinct()
        
        sent_count = 0
        
        for user in users_with_activity:
            if user.email:
                # Prepare digest data
                recent_submissions = FormSubmission.objects.filter(
                    user=user,
                    created_at__gte=last_week
                ).order_by('-created_at')
                
                recent_notifications = Notification.objects.filter(
                    user=user,
                    created_at__gte=last_week
                ).order_by('-created_at')
                
                if recent_submissions.exists() or recent_notifications.exists():
                    context = {
                        'user': user,
                        'recent_submissions': recent_submissions,
                        'recent_notifications': recent_notifications,
                        'week_start': last_week.strftime('%B %d, %Y'),
                        'week_end': timezone.now().strftime('%B %d, %Y'),
                    }
                    
                    success = send_notification_email(
                        user=user,
                        subject='ANNI Weekly Activity Digest',
                        template_name='forms/emails/weekly_digest.html',
                        context=context
                    )
                    
                    if success:
                        sent_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {sent_count} digest emails')
        )

# forms/management/commands/auto_assign_submissions.py

from django.core.management.base import BaseCommand
from forms.utils import auto_assign_reviewers

class Command(BaseCommand):
    help = 'Auto-assign pending submissions to available staff members'

    def handle(self, *args, **options):
        self.stdout.write('Auto-assigning pending submissions...')
        
        assigned_count = auto_assign_reviewers()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned {assigned_count} submissions to reviewers')
        )

# forms/management/commands/generate_report.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from forms.utils import generate_submission_report
import json

class Command(BaseCommand):
    help = 'Generate submission reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Generate report for the last N days (default: 30)'
        )
        
        parser.add_argument(
            '--status',
            type=str,
            help='Filter by submission status'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path for JSON report'
        )

    def handle(self, *args, **options):
        days = options['days']
        status = options.get('status')
        output_file = options.get('output')
        
        self.stdout.write(f'Generating submission report for the last {days} days...')
        
        date_from = timezone.now() - timedelta(days=days)
        
        report_data = generate_submission_report(
            date_from=date_from,
            status=status
        )
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            self.stdout.write(f'Report saved to {output_file}')
        else:
            self.stdout.write(json.dumps(report_data, indent=2, default=str))
        
        self.stdout.write(
            self.style.SUCCESS('Report generated successfully')
        )

# forms/management/commands/create_sample_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from forms.models import FormSubmission, UserProfile, Notification
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of sample users to create (default: 10)'
        )
        
        parser.add_argument(
            '--submissions',
            type=int,
            default=50,
            help='Number of sample submissions to create (default: 50)'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        submissions_count = options['submissions']
        
        self.stdout.write('Creating sample data...')
        
        # Create sample users
        users = []
        for i in range(users_count):
            username = fake.user_name()
            while User.objects.filter(username=username).exists():
                username = fake.user_name()
            
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password='testpass123'
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone_number=fake.phone_number()[:15],
                department=fake.company(),
                bio=fake.text(max_nb_chars=200)
            )
            
            users.append(user)
        
        # Create sample submissions
        statuses = ['pending', 'approved', 'rejected', 'in_progress']
        
        for i in range(submissions_count):
            user = random.choice(users)
            status = random.choice(statuses)
            
            submission = FormSubmission.objects.create(
                user=user,
                name=fake.catch_phrase(),
                details=fake.text(max_nb_chars=500),
                status=status
            )
            
            # Create notification for submission
            Notification.objects.create(
                user=user,
                title=f"Submission {submission.id} Status Update",
                message=f"Your submission '{submission.name}' is now {status}",
                is_read=random.choice([True, False])
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {users_count} users and {submissions_count} submissions'
            )
        )