from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect
from .models import Space, SpaceMember, SpaceSettings


class SpaceCreateForm(forms.ModelForm):
    """Form for creating a new space"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Space
        fields = ['name', 'description', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full pl-10 pr-4 py-3 bg-white border-2 border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:border-wallai-green focus:outline-none focus:ring-2 focus:ring-wallai-green/20 transition-all duration-200',
                'placeholder': 'Enter space name (e.g., "Family Budget", "Roommates")',
                'maxlength': 50,
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full pl-10 pr-4 py-3 bg-white border-2 border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:border-wallai-green focus:outline-none focus:ring-2 focus:ring-wallai-green/20 transition-all duration-200 resize-none',
                'placeholder': 'Optional: Describe what this space is for',
                'rows': 4,
                'maxlength': 200,
            }),
            'color': forms.RadioSelect(attrs={
                'class': 'space-y-2',
            }),
            'icon': forms.RadioSelect(attrs={
                'class': 'space-y-2',
            }),
        }
        help_texts = {
            'name': 'Choose a name that clearly identifies this shared space',
            'description': 'Help members understand the purpose of this space',
            'color': 'Pick a color theme for your space',
            'icon': 'Choose an icon that represents this space',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError('Space name must be at least 2 characters long.')
            if len(name) > 50:
                raise ValidationError('Space name cannot exceed 50 characters.')
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) > 200:
            raise ValidationError('Space description cannot exceed 200 characters.')
        return description

    def clean(self):
        cleaned_data = super().clean()
        # Assign created_by BEFORE model validation
        if self.user and self.instance:
            self.instance.created_by = self.user
        return cleaned_data

    def save(self, commit=True, user=None):
        """Save the space and automatically add creator as owner"""
        space = super().save(commit=False)

        if user:
            space.created_by = user

        if commit:
            space.save()

            # Add creator as owner
            if user:
                SpaceMember.objects.create(
                    space=space,
                    user=user,
                    role='owner',
                    is_active=True
                )

        return space


class JoinSpaceForm(forms.Form):
    """Form for joining a space using invite code"""

    invite_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-4 bg-white border-2 border-gray-200 rounded-xl text-gray-900 text-center text-2xl font-mono tracking-widest uppercase placeholder-gray-400 focus:border-wallai-green focus:outline-none focus:ring-2 focus:ring-wallai-green/20 transition-all duration-200',
            'placeholder': 'ABC123',
            'style': 'text-transform: uppercase;',
            'autocomplete': 'off',
        }),
        help_text='Enter the 6-character invite code shared by the space owner'
    )

    def clean_invite_code(self):
        code = self.cleaned_data.get('invite_code')
        if code:
            code = code.upper().strip()

            # Validate format
            if not code.isalnum():
                raise ValidationError('Invite code must contain only letters and numbers.')

            if len(code) != 6:
                raise ValidationError('Invite code must be exactly 6 characters long.')

            # Check if space exists
            try:
                space = Space.objects.get(invite_code=code, is_active=True)
            except Space.DoesNotExist:
                raise ValidationError('Invalid invite code. Please check and try again.')

            # Store space for later use
            self.space = space

        return code

    def join_space(self, user):
        """Join the user to the space"""
        if not hasattr(self, 'space'):
            raise ValidationError('Invalid form state')

        # Check if user can join
        can_join, message = self.space.can_user_join(user)
        if not can_join:
            raise ValidationError(message)

        # Add user to space
        member = self.space.add_member(user, role='member')
        return member, self.space


class SpaceUpdateForm(forms.ModelForm):
    """Form for updating space details (owner only)"""

    class Meta:
        model = Space
        fields = ['name', 'description', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:border-wallai-green focus:outline-none focus:ring-2 focus:ring-wallai-green/20 transition-all duration-200',
                'placeholder': 'Space name',
                'maxlength': 100,
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-white border-2 border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:border-wallai-green focus:outline-none focus:ring-2 focus:ring-wallai-green/20 transition-all duration-200 resize-none',
                'placeholder': 'Space description',
                'rows': 4,
                'maxlength': 500,
            }),
            'color': forms.RadioSelect(attrs={
                'class': 'space-y-2',
            }),
            'icon': forms.RadioSelect(attrs={
                'class': 'space-y-2',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError('Space name must be at least 2 characters long.')
        return name


class RegenerateInviteCodeForm(forms.Form):
    """Form for regenerating space invite code (owner only)"""

    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-wallai-green bg-white border-2 border-gray-200 rounded focus:ring-wallai-green focus:ring-2 transition-all duration-200',
        }),
        label='I understand that the old invite code will no longer work',
        help_text='Anyone with the current invite code will no longer be able to join'
    )

    def regenerate_code(self, space):
        """Generate new invite code for the space"""
        from .models import generate_invite_code

        # Generate new unique code
        new_code = generate_invite_code()
        while Space.objects.filter(invite_code=new_code).exclude(pk=space.pk).exists():
            new_code = generate_invite_code()

        space.invite_code = new_code.upper()
        space.save(update_fields=['invite_code', 'updated_at'])

        return space


class SpaceSettingsForm(forms.ModelForm):
    """Form for configuring space settings and approval rules"""

    class Meta:
        model = SpaceSettings
        fields = [
            'approval_mode',
            'approval_percentage_threshold',
            'approval_timeout_days',
            'notifications_in_app',
            'notifications_email',
            'shared_expenses_require_approval',
            'recurring_changes_require_approval',
            'deletion_requires_approval',
        ]
        widgets = {
            'approval_mode': forms.RadioSelect(attrs={
                'class': 'space-y-3',
            }),
            'approval_percentage_threshold': forms.NumberInput(attrs={
                'class': 'w-24 px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:border-wallai-green focus:outline-none transition-all duration-200',
                'min': '0',
                'max': '100',
                'step': '0.1',
            }),
            'approval_timeout_days': forms.NumberInput(attrs={
                'class': 'w-20 px-3 py-2 bg-white border-2 border-gray-200 rounded-lg text-gray-900 focus:border-wallai-green focus:outline-none transition-all duration-200',
                'min': '1',
                'max': '30',
            }),
            'notifications_in_app': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-wallai-green bg-white border-2 border-gray-300 rounded focus:ring-wallai-green focus:ring-2 transition-all duration-200',
            }),
            'notifications_email': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-wallai-green bg-white border-2 border-gray-300 rounded focus:ring-wallai-green focus:ring-2 transition-all duration-200',
            }),
            'shared_expenses_require_approval': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-wallai-green bg-white border-2 border-gray-300 rounded focus:ring-wallai-green focus:ring-2 transition-all duration-200',
            }),
            'recurring_changes_require_approval': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-wallai-green bg-white border-2 border-gray-300 rounded focus:ring-wallai-green focus:ring-2 transition-all duration-200',
            }),
            'deletion_requires_approval': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-wallai-green bg-white border-2 border-gray-300 rounded focus:ring-wallai-green focus:ring-2 transition-all duration-200',
            }),
        }
        labels = {
            'approval_mode': 'How should budget changes be approved?',
            'approval_percentage_threshold': 'Percentage threshold for approval',
            'approval_timeout_days': 'Days before auto-approval',
            'notifications_in_app': 'Enable in-app notifications',
            'notifications_email': 'Also send email notifications',
            'shared_expenses_require_approval': 'Shared expenses always require approval',
            'recurring_changes_require_approval': 'Changes to recurring items require approval',
            'deletion_requires_approval': 'Deleting budget items requires approval',
        }
        help_texts = {
            'approval_mode': 'Choose when budget changes need approval from other members',
            'approval_percentage_threshold': 'Changes above this percentage will require approval (when using percentage mode)',
            'approval_timeout_days': 'After this many days, pending changes will be automatically approved',
            'notifications_in_app': 'Members will see notifications within Wallai',
            'notifications_email': 'Members will also receive email notifications (requires in-app notifications)',
            'shared_expenses_require_approval': 'Any shared expense will always need approval regardless of amount',
            'recurring_changes_require_approval': 'Changes to recurring expenses will need approval',
            'deletion_requires_approval': 'Removing budget items will need approval',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamic help text for approval mode based on space
        approval_mode_field = self.fields['approval_mode']
        approval_mode_field.widget.attrs.update({'x-model': 'approvalMode'})

        # Add Alpine.js data for dynamic UI
        self.approval_mode_choices_with_descriptions = [
            ('none', 'No Approvals', 'Changes can be made freely by any member'),
            ('all', 'All Changes', 'Every budget change requires approval from other members'),
            ('percentage', 'Percentage Based', 'Only changes above a certain percentage require approval'),
            ('custom', 'Custom Rules', 'Use specific rules for different types of changes'),
        ]

    def clean_approval_percentage_threshold(self):
        threshold = self.cleaned_data.get('approval_percentage_threshold')
        if threshold is not None:
            if threshold < 0:
                raise ValidationError('Percentage threshold cannot be negative.')
            if threshold > 100:
                raise ValidationError('Percentage threshold cannot exceed 100%.')
        return threshold

    def clean_approval_timeout_days(self):
        timeout = self.cleaned_data.get('approval_timeout_days')
        if timeout is not None:
            if timeout < 1:
                raise ValidationError('Timeout must be at least 1 day.')
            if timeout > 30:
                raise ValidationError('Timeout cannot exceed 30 days.')
        return timeout

    def clean(self):
        cleaned_data = super().clean()

        # Email notifications require in-app notifications
        if cleaned_data.get('notifications_email') and not cleaned_data.get('notifications_in_app'):
            raise ValidationError({
                'notifications_email': 'Email notifications require in-app notifications to be enabled.'
            })

        return cleaned_data

    def save(self, commit=True):
        """Save the space settings"""
        instance = super().save(commit=commit)

        if commit:
            # Any additional logic after saving settings
            pass

        return instance