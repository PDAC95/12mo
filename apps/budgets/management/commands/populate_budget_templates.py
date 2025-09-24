from django.core.management.base import BaseCommand
from budgets.models import BudgetTemplate


class Command(BaseCommand):
    help = 'Populate system default budget templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing system templates before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing system templates...')
            )
            BudgetTemplate.objects.filter(is_system_default=True).delete()

        self.stdout.write('Creating system default budget templates...')

        # Use the model's create_system_defaults method
        BudgetTemplate.create_system_defaults()

        # Count templates created
        framework_count = BudgetTemplate.objects.filter(
            template_type='framework',
            is_system_default=True
        ).count()

        situation_count = BudgetTemplate.objects.filter(
            template_type='situation',
            is_system_default=True
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {framework_count} framework templates '
                f'and {situation_count} situation templates'
            )
        )

        # List created templates
        self.stdout.write('\nFramework Templates:')
        for template in BudgetTemplate.get_frameworks():
            if template.is_system_default:
                self.stdout.write(f'  - {template.name}')

        self.stdout.write('\nSituation Templates:')
        for template in BudgetTemplate.get_situations():
            if template.is_system_default:
                self.stdout.write(f'  - {template.name}')