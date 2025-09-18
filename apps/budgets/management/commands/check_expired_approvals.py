from django.core.management.base import BaseCommand
from django.utils import timezone
from budgets.services import BudgetChangeService
from notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Check for expired approval requests and auto-approve them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Also clean up old notifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cleanup = options['cleanup']

        self.stdout.write(
            self.style.SUCCESS(f'Starting expired approval check at {timezone.now()}')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        # Check for expired requests
        if dry_run:
            from budgets.approval_models import BudgetChangeRequest
            expired_requests = BudgetChangeRequest.objects.filter(
                status='pending',
                expires_at__lte=timezone.now()
            )

            self.stdout.write(
                f'Found {expired_requests.count()} expired requests that would be auto-approved:'
            )

            for request in expired_requests:
                self.stdout.write(
                    f'  - {request.budget_item.category.name} in {request.budget_item.space.name} '
                    f'(requested by {request.requested_by.username}, '
                    f'expired: {request.expires_at})'
                )

        else:
            # Actually auto-approve expired requests
            auto_approved_count = BudgetChangeService.check_expired_requests()

            self.stdout.write(
                self.style.SUCCESS(f'Auto-approved {auto_approved_count} expired requests')
            )

        # Clean up notifications if requested
        if cleanup:
            if dry_run:
                self.stdout.write('Would clean up expired and old notifications')
            else:
                cleanup_stats = NotificationService.cleanup_notifications()

                self.stdout.write(
                    f'Cleaned up {cleanup_stats["expired_removed"]} expired notifications'
                )
                self.stdout.write(
                    f'Cleaned up {cleanup_stats["old_read_removed"]} old read notifications'
                )

        self.stdout.write(
            self.style.SUCCESS('Expired approval check completed')
        )