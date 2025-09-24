from django.core.management.base import BaseCommand
from budgets.models import BudgetTemplate


class Command(BaseCommand):
    help = 'Fix category sections to English'

    def handle(self, *args, **options):
        self.stdout.write('Fixing category sections to English...')

        # Update 50/30/20 Rule
        template = BudgetTemplate.objects.get(name='50/30/20 Rule')
        if template:
            template.category_data = {
                'Housing & Rent': {'percentage': 32.9, 'amount': 1200, 'section': 'NEEDS'},
                'Food & Groceries': {'percentage': 11.0, 'amount': 400, 'section': 'NEEDS'},
                'Transportation': {'percentage': 6.2, 'amount': 225, 'section': 'NEEDS'},
                'Entertainment': {'percentage': 8.2, 'amount': 300, 'section': 'WANTS'},
                'Shopping': {'percentage': 11.0, 'amount': 400, 'section': 'WANTS'},
                'Other': {'percentage': 10.8, 'amount': 395, 'section': 'WANTS'},
                'Savings': {'percentage': 10.0, 'amount': 365, 'section': 'SAVINGS'},
                'Debt Payments': {'percentage': 10.0, 'amount': 365, 'section': 'SAVINGS'}
            }
            template.save()
            self.stdout.write('  Updated: 50/30/20 Rule categories')

        # Update Zero-based Budget
        template = BudgetTemplate.objects.get(name='Zero-based Budget')
        if template:
            template.category_data = {
                'Housing & Rent': {'percentage': 32.9, 'amount': 1200, 'section': 'EXPENSES'},
                'Savings': {'percentage': 13.7, 'amount': 500, 'section': 'EXPENSES'},
                'Food & Groceries': {'percentage': 11.0, 'amount': 400, 'section': 'EXPENSES'},
                'Transportation': {'percentage': 8.2, 'amount': 300, 'section': 'EXPENSES'},
                'Debt Payments': {'percentage': 8.2, 'amount': 300, 'section': 'EXPENSES'},
                'Shopping': {'percentage': 6.8, 'amount': 250, 'section': 'EXPENSES'},
                'Entertainment': {'percentage': 5.5, 'amount': 200, 'section': 'EXPENSES'},
                'Utilities': {'percentage': 5.5, 'amount': 200, 'section': 'EXPENSES'},
                'Healthcare': {'percentage': 4.1, 'amount': 150, 'section': 'EXPENSES'},
                'Other': {'percentage': 4.1, 'amount': 150, 'section': 'EXPENSES'}
            }
            template.save()
            self.stdout.write('  Updated: Zero-based Budget categories')

        # Update 60/20/20 Aggressive
        template = BudgetTemplate.objects.get(name='60/20/20 Aggressive')
        if template:
            template.category_data = {
                'Housing & Rent': {'percentage': 32.9, 'amount': 1200, 'section': 'NEEDS'},
                'Food & Groceries': {'percentage': 15.1, 'amount': 550, 'section': 'NEEDS'},
                'Transportation': {'percentage': 8.2, 'amount': 300, 'section': 'NEEDS'},
                'Utilities': {'percentage': 4.1, 'amount': 150, 'section': 'NEEDS'},
                'Savings': {'percentage': 13.7, 'amount': 500, 'section': 'SAVINGS'},
                'Debt Payments': {'percentage': 6.8, 'amount': 250, 'section': 'SAVINGS'},
                'Entertainment': {'percentage': 13.7, 'amount': 500, 'section': 'LIFESTYLE'},
                'Shopping': {'percentage': 5.5, 'amount': 200, 'section': 'LIFESTYLE'}
            }
            template.save()
            self.stdout.write('  Updated: 60/20/20 Aggressive categories')

        self.stdout.write(self.style.SUCCESS('Successfully fixed all category sections to English'))