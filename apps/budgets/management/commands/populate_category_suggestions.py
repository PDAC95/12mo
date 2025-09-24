from django.core.management.base import BaseCommand
from budgets.models import CategorySuggestion


class Command(BaseCommand):
    help = 'Populate category suggestions for autocomplete functionality'

    def handle(self, *args, **options):
        self.stdout.write('Populating category suggestions...')

        # Define category suggestions organized by type
        suggestions = {
            'housing': [
                ('Rent', True), ('Mortgage', True), ('Property Tax', False),
                ('Home Insurance', False), ('HOA Fees', False),
                ('Home Maintenance', False), ('Repairs', False),
                ('Utilities', True), ('Electricity', False), ('Gas', False),
                ('Water', False), ('Internet', True), ('Phone', True),
                ('Cable TV', False), ('Streaming Services', False),
            ],
            'food': [
                ('Groceries', True), ('Dining Out', True), ('Coffee', True),
                ('Lunch', False), ('Breakfast', False), ('Fast Food', False),
                ('Restaurants', True), ('Food Delivery', False),
                ('Alcohol', False), ('Snacks', False),
            ],
            'transportation': [
                ('Car Payment', True), ('Gas', True), ('Car Insurance', True),
                ('Car Maintenance', False), ('Public Transit', False),
                ('Uber/Lyft', False), ('Taxi', False), ('Parking', False),
                ('Tolls', False), ('Car Registration', False), ('Oil Change', False),
                ('Tires', False), ('Repairs', False),
            ],
            'healthcare': [
                ('Health Insurance', True), ('Doctor Visits', False),
                ('Dentist', False), ('Prescription', False), ('Pharmacy', False),
                ('Eye Care', False), ('Therapy', False), ('Gym', True),
                ('Fitness', False), ('Medical Bills', False),
            ],
            'entertainment': [
                ('Movies', True), ('Concerts', False), ('Sports Events', False),
                ('Hobbies', True), ('Books', False), ('Games', False),
                ('Music', False), ('Art Supplies', False), ('Theater', False),
                ('Festivals', False), ('Nightlife', False),
            ],
            'shopping': [
                ('Clothing', True), ('Shoes', False), ('Personal Care', True),
                ('Haircut', False), ('Beauty', False), ('Electronics', False),
                ('Home Goods', False), ('Gifts', True), ('Amazon', False),
                ('Online Shopping', False),
            ],
            'education': [
                ('Tuition', False), ('Books', False), ('School Supplies', False),
                ('Courses', False), ('Training', False), ('Certifications', False),
                ('Online Learning', False), ('Workshops', False),
            ],
            'savings': [
                ('Emergency Fund', True), ('Retirement', True), ('Investment', True),
                ('Vacation Fund', False), ('Down Payment', False),
                ('College Fund', False), ('Savings Account', True),
                ('401k', False), ('IRA', False),
            ],
            'debt': [
                ('Credit Card', True), ('Student Loan', True), ('Personal Loan', False),
                ('Car Loan', False), ('Medical Debt', False), ('Other Debt', False),
            ],
            'subscriptions': [
                ('Netflix', True), ('Spotify', True), ('Amazon Prime', False),
                ('Hulu', False), ('Disney+', False), ('YouTube Premium', False),
                ('Software', False), ('Apps', False), ('Cloud Storage', False),
                ('News', False), ('Magazines', False),
            ],
            'pets': [
                ('Pet Food', False), ('Vet Bills', False), ('Pet Insurance', False),
                ('Pet Supplies', False), ('Grooming', False), ('Pet Care', False),
                ('Dog Walker', False),
            ],
            'family': [
                ('Childcare', False), ('School Fees', False), ('Kids Activities', False),
                ('Babysitter', False), ('Child Support', False), ('Kids Clothing', False),
                ('Toys', False), ('Family Outings', False),
            ],
            'travel': [
                ('Vacation', True), ('Hotel', False), ('Flight', False),
                ('Car Rental', False), ('Travel Insurance', False),
                ('Passport', False), ('Visa', False), ('Tours', False),
            ],
            'business': [
                ('Office Supplies', False), ('Business Meals', False),
                ('Professional Development', False), ('Networking', False),
                ('Business Insurance', False), ('Taxes', False),
                ('Accounting', False), ('Legal Fees', False),
            ],
            'other': [
                ('Donations', False), ('Charity', False), ('Gifts', False),
                ('Miscellaneous', True), ('Emergency', False), ('Unexpected', False),
            ],
        }

        created_count = 0
        updated_count = 0

        for category_type, items in suggestions.items():
            for name, is_popular in items:
                suggestion, created = CategorySuggestion.objects.get_or_create(
                    name=name,
                    defaults={
                        'category_type': category_type,
                        'is_popular': is_popular,
                        'usage_count': 10 if is_popular else 1,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'  Created: {name}')
                else:
                    # Update existing if needed
                    if suggestion.category_type != category_type or suggestion.is_popular != is_popular:
                        suggestion.category_type = category_type
                        suggestion.is_popular = is_popular
                        if is_popular and suggestion.usage_count < 10:
                            suggestion.usage_count = 10
                        suggestion.save()
                        updated_count += 1
                        self.stdout.write(f'  Updated: {name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated category suggestions: '
                f'{created_count} created, {updated_count} updated'
            )
        )