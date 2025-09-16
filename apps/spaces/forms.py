from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect
from .models import Space, SpaceMember


class SpaceCreateForm(forms.ModelForm):
    """Form for creating a new space"""

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