from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import Budget, BudgetCategory, BudgetTemplate
from spaces.models import Space, SpaceMember

User = get_user_model()


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating custom budget categories"""

    class Meta:
        model = BudgetCategory
        fields = ['name', 'description', 'icon', 'category_type', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'wallai-input',
                'placeholder': 'Category name (e.g., Entertainment)',
                'maxlength': '50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'wallai-input',
                'placeholder': 'Optional description of this category',
                'rows': 3,
                'maxlength': '200'
            }),
            'icon': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'category_type': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'color': forms.TextInput(attrs={
                'class': 'wallai-input',
                'placeholder': 'blue'
            })
        }

    def __init__(self, *args, **kwargs):
        self.space = kwargs.pop('space', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Validate category name uniqueness within space"""
        name = self.cleaned_data.get('name')
        if name and self.space:
            # Check for duplicate names in the same space
            existing = BudgetCategory.objects.filter(
                space=self.space,
                name__iexact=name.strip(),
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('A category with this name already exists in this space.')

        return name.strip() if name else name

    def save(self, commit=True):
        """Save category with space and user information"""
        category = super().save(commit=False)
        if self.space:
            category.space = self.space
        if self.user:
            category.created_by = self.user

        if commit:
            category.save()
        return category


class BudgetForm(forms.ModelForm):
    """Form for creating and editing budgets"""

    class Meta:
        model = Budget
        fields = ['category', 'amount', 'assigned_to', 'notes']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'wallai-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'wallai-input',
                'placeholder': 'Optional notes about this budget...',
                'rows': 3,
                'maxlength': '500'
            })
        }

    def __init__(self, *args, **kwargs):
        self.space = kwargs.pop('space', None)
        self.user = kwargs.pop('user', None)
        self.month_period = kwargs.pop('month_period', None)
        super().__init__(*args, **kwargs)

        # Filter categories for the space
        if self.space:
            # Include system defaults and custom categories for this space
            from django.db import models
            categories = BudgetCategory.objects.filter(
                models.Q(is_system_default=True) | models.Q(space=self.space),
                is_active=True
            ).order_by('is_system_default', 'name')

            self.fields['category'].queryset = categories

            # Filter assigned_to to space members
            space_members = User.objects.filter(
                spacemember__space=self.space,
                spacemember__is_active=True
            ).distinct()

            self.fields['assigned_to'].queryset = space_members
            self.fields['assigned_to'].empty_label = "Not assigned"

    def clean_amount(self):
        """Validate budget amount"""
        amount = self.cleaned_data.get('amount')
        if amount is not None:
            if amount <= 0:
                raise ValidationError('Budget amount must be greater than 0.')
            if amount > 999999.99:
                raise ValidationError('Budget amount cannot exceed $999,999.99.')
        return amount

    def clean(self):
        """Validate budget constraints"""
        cleaned_data = super().clean()
        category = cleaned_data.get('category')

        # Check for duplicate budget in same space/month/category
        if category and self.space and self.month_period:
            existing = Budget.objects.filter(
                space=self.space,
                category=category,
                month_period=self.month_period,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('A budget for this category already exists for this month.')

        return cleaned_data

    def save(self, commit=True):
        """Save budget with space, user, and month information"""
        budget = super().save(commit=False)
        if self.space:
            budget.space = self.space
        if self.user:
            budget.created_by = self.user
        if self.month_period:
            budget.month_period = self.month_period

        if commit:
            budget.save()
        return budget


class MonthlyBudgetForm(forms.Form):
    """Form for creating a complete monthly budget"""

    month_period = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'class': 'wallai-input',
            'placeholder': '2025-09',
            'pattern': r'\d{4}-\d{2}'
        }),
        help_text="Month in YYYY-MM format"
    )

    copy_from_previous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-wallai-green focus:ring-wallai-green'
        }),
        help_text="Copy amounts from previous month"
    )

    def __init__(self, *args, **kwargs):
        self.space = kwargs.pop('space', None)
        super().__init__(*args, **kwargs)

        # Set default month to current month
        current_month = timezone.now().strftime('%Y-%m')
        self.fields['month_period'].initial = current_month

    def clean_month_period(self):
        """Validate month format and future/past restrictions"""
        month_period = self.cleaned_data.get('month_period')
        if month_period:
            try:
                from datetime import datetime
                datetime.strptime(month_period, '%Y-%m')
            except ValueError:
                raise ValidationError('Month must be in YYYY-MM format.')

            # Check if budget already exists for this month
            if self.space:
                existing_budgets = Budget.objects.filter(
                    space=self.space,
                    month_period=month_period,
                    is_active=True
                )
                if existing_budgets.exists():
                    raise ValidationError(f'Budgets already exist for {month_period}. You can edit individual budgets instead.')

        return month_period


class BudgetBulkEditForm(forms.Form):
    """Form for bulk editing multiple budgets"""

    def __init__(self, *args, **kwargs):
        self.budgets = kwargs.pop('budgets', [])
        super().__init__(*args, **kwargs)

        # Create dynamic fields for each budget
        for budget in self.budgets:
            field_name = f'amount_{budget.id}'
            self.fields[field_name] = forms.DecimalField(
                max_digits=10,
                decimal_places=2,
                min_value=Decimal('0.01'),
                initial=budget.amount,
                widget=forms.NumberInput(attrs={
                    'class': 'wallai-input',
                    'step': '0.01',
                    'min': '0.01'
                }),
                label=budget.category.name
            )

            # Assigned to field
            assigned_field_name = f'assigned_to_{budget.id}'
            self.fields[assigned_field_name] = forms.ModelChoiceField(
                queryset=User.objects.filter(
                    spacemember__space=budget.space,
                    spacemember__is_active=True
                ).distinct(),
                required=False,
                initial=budget.assigned_to,
                widget=forms.Select(attrs={
                    'class': 'wallai-input'
                }),
                empty_label="Not assigned"
            )

    def save(self):
        """Save all budget changes"""
        updated_budgets = []

        for budget in self.budgets:
            amount_field = f'amount_{budget.id}'
            assigned_field = f'assigned_to_{budget.id}'

            if amount_field in self.cleaned_data:
                budget.amount = self.cleaned_data[amount_field]

            if assigned_field in self.cleaned_data:
                budget.assigned_to = self.cleaned_data[assigned_field]

            budget.save()
            updated_budgets.append(budget)

        return updated_budgets


class BudgetCopyForm(forms.Form):
    """Form for copying budgets from one month to another"""

    source_month = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'class': 'wallai-input',
            'placeholder': '2025-08'
        }),
        help_text="Source month in YYYY-MM format"
    )

    target_month = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'class': 'wallai-input',
            'placeholder': '2025-09'
        }),
        help_text="Target month in YYYY-MM format"
    )

    multiply_by = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('10.00'),
        initial=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'class': 'wallai-input',
            'step': '0.01',
            'min': '0.01',
            'max': '10.00'
        }),
        help_text="Multiply amounts by this factor (1.00 = same amounts)"
    )

    def __init__(self, *args, **kwargs):
        self.space = kwargs.pop('space', None)
        super().__init__(*args, **kwargs)

    def clean_source_month(self):
        """Validate source month has budgets"""
        source_month = self.cleaned_data.get('source_month')
        if source_month and self.space:
            try:
                from datetime import datetime
                datetime.strptime(source_month, '%Y-%m')
            except ValueError:
                raise ValidationError('Month must be in YYYY-MM format.')

            # Check if source month has budgets
            source_budgets = Budget.objects.filter(
                space=self.space,
                month_period=source_month,
                is_active=True
            )
            if not source_budgets.exists():
                raise ValidationError(f'No budgets found for {source_month}.')

        return source_month

    def clean_target_month(self):
        """Validate target month format"""
        target_month = self.cleaned_data.get('target_month')
        if target_month:
            try:
                from datetime import datetime
                datetime.strptime(target_month, '%Y-%m')
            except ValueError:
                raise ValidationError('Month must be in YYYY-MM format.')

        return target_month

    def clean(self):
        """Validate that source and target months are different"""
        cleaned_data = super().clean()
        source_month = cleaned_data.get('source_month')
        target_month = cleaned_data.get('target_month')

        if source_month and target_month and source_month == target_month:
            raise ValidationError('Source and target months must be different.')

        return cleaned_data


class SmartBudgetCreationForm(forms.ModelForm):
    """Enhanced budget creation form with template selection and timing options"""

    # Template selection
    use_template = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-wallai-green focus:ring-wallai-green',
            'x-model': 'useTemplate'
        }),
        label="Use a template to speed up creation"
    )

    template = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'wallai-input',
            'x-show': 'useTemplate',
            '@change': 'loadTemplate($event.target.value)'
        }),
        empty_label="Select a template..."
    )

    class Meta:
        model = Budget
        fields = [
            'category', 'amount', 'timing_type', 'due_date', 'range_start',
            'range_end', 'range_description', 'reminder_days_before',
            'preferred_time_of_day', 'is_recurring', 'recurrence_pattern',
            'assigned_to', 'notes'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'wallai-input',
                'x-model': 'selectedCategory'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'wallai-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'x-model': 'amount'
            }),
            'timing_type': forms.Select(attrs={
                'class': 'wallai-input',
                'x-model': 'timingType',
                '@change': 'updateTimingFields()'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'wallai-input',
                'type': 'date',
                'x-show': 'timingType === "fixed_date"',
                'x-model': 'dueDate'
            }),
            'range_start': forms.DateInput(attrs={
                'class': 'wallai-input',
                'type': 'date',
                'x-show': 'timingType === "date_range"',
                'x-model': 'rangeStart'
            }),
            'range_end': forms.DateInput(attrs={
                'class': 'wallai-input',
                'type': 'date',
                'x-show': 'timingType === "date_range"',
                'x-model': 'rangeEnd'
            }),
            'range_description': forms.TextInput(attrs={
                'class': 'wallai-input',
                'placeholder': 'e.g., First week of month, Weekends only',
                'x-show': 'timingType === "date_range"',
                'x-model': 'rangeDescription'
            }),
            'reminder_days_before': forms.NumberInput(attrs={
                'class': 'wallai-input',
                'min': '0',
                'max': '30',
                'x-model': 'reminderDays'
            }),
            'preferred_time_of_day': forms.Select(attrs={
                'class': 'wallai-input',
                'x-model': 'preferredTime'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-wallai-green focus:ring-wallai-green',
                'x-model': 'isRecurring',
                '@change': 'updateRecurrenceFields()'
            }),
            'recurrence_pattern': forms.Select(attrs={
                'class': 'wallai-input',
                'x-show': 'isRecurring',
                'x-model': 'recurrencePattern'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'wallai-input',
                'x-model': 'assignedTo'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'wallai-input',
                'placeholder': 'Optional notes about this budget...',
                'rows': 3,
                'maxlength': '500',
                'x-model': 'notes'
            })
        }

    def __init__(self, *args, **kwargs):
        self.space = kwargs.pop('space', None)
        self.user = kwargs.pop('user', None)
        self.month_period = kwargs.pop('month_period', None)
        super().__init__(*args, **kwargs)

        # Filter categories for the space
        if self.space:
            from django.db import models
            from .models import BudgetTemplate

            # Include system defaults and custom categories for this space
            categories = BudgetCategory.objects.filter(
                models.Q(is_system_default=True) | models.Q(space=self.space),
                is_active=True
            ).order_by('is_system_default', 'name')
            self.fields['category'].queryset = categories

            # Get available templates
            templates = BudgetTemplate.objects.filter(
                models.Q(is_system_default=True) | models.Q(space=self.space),
                is_active=True
            ).order_by('template_type', 'name')
            self.fields['template'].queryset = templates

            # Filter assigned_to to space members
            space_members = User.objects.filter(
                spacemember__space=self.space,
                spacemember__is_active=True
            ).distinct()
            self.fields['assigned_to'].queryset = space_members
            self.fields['assigned_to'].empty_label = "Not assigned"

    def clean(self):
        """Enhanced validation for timing fields"""
        cleaned_data = super().clean()
        timing_type = cleaned_data.get('timing_type')

        # Timing-specific validation
        if timing_type == 'fixed_date':
            if not cleaned_data.get('due_date'):
                raise ValidationError({'due_date': 'Due date is required for fixed date expenses'})
        elif timing_type == 'date_range':
            range_start = cleaned_data.get('range_start')
            range_end = cleaned_data.get('range_end')
            if not range_start or not range_end:
                raise ValidationError({'range_start': 'Both start and end dates are required for date range expenses'})
            if range_start >= range_end:
                raise ValidationError({'range_start': 'Start date must be before end date'})

        # Check for duplicate budget in same space/month/category
        category = cleaned_data.get('category')
        if category and self.space and self.month_period:
            existing = Budget.objects.filter(
                space=self.space,
                category=category,
                month_period=self.month_period,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise ValidationError('A budget for this category already exists for this month.')

        return cleaned_data

    def save(self, commit=True):
        """Save budget with space, user, and month information"""
        budget = super().save(commit=False)
        if self.space:
            budget.space = self.space
        if self.user:
            budget.created_by = self.user
        if self.month_period:
            budget.month_period = self.month_period

        if commit:
            budget.save()

        # If a template was used, increment its usage count
        template_id = self.data.get('template')
        if template_id and self.cleaned_data.get('use_template'):
            try:
                from .models import BudgetTemplate
                template = BudgetTemplate.objects.get(id=template_id)
                template.increment_usage()
            except BudgetTemplate.DoesNotExist:
                pass

        return budget


class BudgetTemplateForm(forms.ModelForm):
    """Form for creating and editing budget templates"""

    class Meta:
        model = BudgetTemplate
        fields = [
            'name', 'description', 'template_type', 'default_category',
            'suggested_amount', 'default_timing_type', 'default_reminder_days',
            'default_time_of_day', 'default_is_recurring', 'default_recurrence_pattern'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'wallai-input',
                'placeholder': 'Template name (e.g., Monthly Rent)',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'wallai-input',
                'placeholder': 'Description of when to use this template',
                'rows': 3,
                'maxlength': '300'
            }),
            'template_type': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'default_category': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'suggested_amount': forms.NumberInput(attrs={
                'class': 'wallai-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'default_timing_type': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'default_reminder_days': forms.NumberInput(attrs={
                'class': 'wallai-input',
                'min': '0',
                'max': '30'
            }),
            'default_time_of_day': forms.Select(attrs={
                'class': 'wallai-input'
            }),
            'default_is_recurring': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-wallai-green focus:ring-wallai-green'
            }),
            'default_recurrence_pattern': forms.Select(attrs={
                'class': 'wallai-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.space = kwargs.pop('space', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter categories for the space
        if self.space:
            from django.db import models
            categories = BudgetCategory.objects.filter(
                models.Q(is_system_default=True) | models.Q(space=self.space),
                is_active=True
            ).order_by('is_system_default', 'name')
            self.fields['default_category'].queryset = categories

    def save(self, commit=True):
        """Save template with space and user information"""
        template = super().save(commit=False)
        if self.space:
            template.space = self.space
        if self.user:
            template.created_by = self.user
        template.template_type = 'custom'  # Mark as custom template

        if commit:
            template.save()
        return template