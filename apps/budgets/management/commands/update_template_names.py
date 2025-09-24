from django.core.management.base import BaseCommand
from budgets.models import BudgetTemplate


class Command(BaseCommand):
    help = 'Update template names to English'

    def handle(self, *args, **options):
        self.stdout.write('Updating template names to English...')

        # Spanish to English name mappings
        name_updates = {
            'Casa': 'House',
            'Oficina/Negocio': 'Office/Business',
            'Plan Evento': 'Event Planning',
            'Viaje de Negocios': 'Business Travel',
        }

        updated_count = 0
        for spanish_name, english_name in name_updates.items():
            template = BudgetTemplate.objects.filter(
                name=spanish_name,
                is_system_default=True
            ).first()

            if template:
                template.name = english_name
                template.save()
                updated_count += 1
                self.stdout.write(f'  Updated: {spanish_name} -> {english_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} template names to English'
            )
        )