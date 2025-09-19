from django.core.management.base import BaseCommand
from budgets.models import BudgetTemplate


class Command(BaseCommand):
    help = 'Create system default budget templates'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating system default templates...'))

        BudgetTemplate.create_system_defaults()

        template_count = BudgetTemplate.objects.filter(is_system_default=True).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {template_count} system default templates!'
            )
        )