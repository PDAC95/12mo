from django.core.management.base import BaseCommand
from budgets.models import BudgetTemplate


class Command(BaseCommand):
    help = 'Update template descriptions to English'

    def handle(self, *args, **options):
        self.stdout.write('Updating template descriptions to English...')

        # Template description updates
        description_updates = {
            '50/30/20 Rule': 'Allocate 50% to basic needs, 30% to personal wants, and 20% to savings. If you can\'t save 20%, start with less but maintain the priority order.',

            'Zero-based Budget': 'Every dollar has a specific purpose. Income minus all assigned expenses should equal zero.',

            '60/20/20 Aggressive': 'Aggressive savings approach: 60% necessary expenses, 20% aggressive savings, 20% lifestyle.',

            'House': 'Family budget for household expenses shared among family members.',

            'Roommates': 'Budget for shared expenses between roommates or housemates.',

            'Business Travel': 'Budget for planning work travel or conference expenses.',

            'Event Planning': 'Budget for organizing parties, weddings, meetings, or special events.',

            'Office/Business': 'Budget for operational expenses of an office or small business.',
        }

        # Also update category data to English
        category_updates = {
            'House': {
                'Housing & Rent': {'percentage': 35.0, 'amount': 1400, 'section': 'FIXED'},
                'Utilities': {'percentage': 6.0, 'amount': 240, 'section': 'FIXED'},
                'Food & Groceries': {'percentage': 15.0, 'amount': 600, 'section': 'VARIABLE'},
                'Transportation': {'percentage': 10.0, 'amount': 400, 'section': 'VARIABLE'},
                'Healthcare': {'percentage': 8.0, 'amount': 320, 'section': 'VARIABLE'},
                'Entertainment': {'percentage': 6.0, 'amount': 240, 'section': 'VARIABLE'},
                'Shopping': {'percentage': 5.0, 'amount': 200, 'section': 'VARIABLE'},
                'Savings': {'percentage': 15.0, 'amount': 600, 'section': 'SAVINGS'}
            },
            'Roommates': {
                'Housing & Rent': {'percentage': 40.0, 'amount': 800, 'section': 'SHARED'},
                'Utilities': {'percentage': 10.0, 'amount': 200, 'section': 'SHARED'},
                'Food & Groceries': {'percentage': 20.0, 'amount': 400, 'section': 'SHARED'},
                'Entertainment': {'percentage': 15.0, 'amount': 300, 'section': 'SHARED'},
                'Shopping': {'percentage': 10.0, 'amount': 200, 'section': 'PERSONAL'},
                'Other': {'percentage': 5.0, 'amount': 100, 'section': 'PERSONAL'}
            },
            'Business Travel': {
                'Transportation': {'percentage': 35.0, 'amount': 700, 'section': 'TRAVEL'},
                'Housing & Rent': {'percentage': 25.0, 'amount': 500, 'section': 'TRAVEL'},
                'Food & Groceries': {'percentage': 20.0, 'amount': 400, 'section': 'TRAVEL'},
                'Entertainment': {'percentage': 10.0, 'amount': 200, 'section': 'TRAVEL'},
                'Other': {'percentage': 10.0, 'amount': 200, 'section': 'MISCELLANEOUS'}
            },
            'Event Planning': {
                'Food & Groceries': {'percentage': 30.0, 'amount': 600, 'section': 'EVENT'},
                'Entertainment': {'percentage': 25.0, 'amount': 500, 'section': 'EVENT'},
                'Shopping': {'percentage': 20.0, 'amount': 400, 'section': 'EVENT'},
                'Other': {'percentage': 15.0, 'amount': 300, 'section': 'MISCELLANEOUS'},
                'Transportation': {'percentage': 10.0, 'amount': 200, 'section': 'MISCELLANEOUS'}
            },
            'Office/Business': {
                'Housing & Rent': {'percentage': 25.0, 'amount': 500, 'section': 'OPERATIONAL'},
                'Utilities': {'percentage': 15.0, 'amount': 300, 'section': 'OPERATIONAL'},
                'Shopping': {'percentage': 20.0, 'amount': 400, 'section': 'OPERATIONAL'},
                'Transportation': {'percentage': 10.0, 'amount': 200, 'section': 'OPERATIONAL'},
                'Entertainment': {'percentage': 10.0, 'amount': 200, 'section': 'MARKETING'},
                'Other': {'percentage': 20.0, 'amount': 400, 'section': 'MISCELLANEOUS'}
            }
        }

        # Also update sections_data for frameworks to English
        sections_updates = {
            '50/30/20 Rule': {
                'NEEDS': {'percentage': 50, 'color': 'green', 'emoji': '🟢'},
                'WANTS': {'percentage': 30, 'color': 'yellow', 'emoji': '🟡'},
                'SAVINGS': {'percentage': 20, 'color': 'blue', 'emoji': '🔵'}
            },
            'Zero-based Budget': {
                'INCOME': {'percentage': 100, 'color': 'green', 'emoji': '💰'},
                'EXPENSES': {'percentage': 100, 'color': 'red', 'emoji': '💸'}
            },
            '60/20/20 Aggressive': {
                'NEEDS': {'percentage': 60, 'color': 'green', 'emoji': '🟢'},
                'SAVINGS': {'percentage': 20, 'color': 'blue', 'emoji': '🔵'},
                'LIFESTYLE': {'percentage': 20, 'color': 'yellow', 'emoji': '🟡'}
            }
        }

        updated_count = 0
        for template_name, new_description in description_updates.items():
            template = BudgetTemplate.objects.filter(
                name=template_name,
                is_system_default=True
            ).first()

            if template:
                template.description = new_description

                # Update category data if available
                if template_name in category_updates:
                    template.category_data = category_updates[template_name]

                # Update sections data if available
                if template_name in sections_updates:
                    template.sections_data = sections_updates[template_name]

                template.save()
                updated_count += 1
                self.stdout.write(f'  Updated: {template_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} template descriptions and data to English'
            )
        )