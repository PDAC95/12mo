import string
import random
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError

User = get_user_model()


def generate_invite_code():
    """Generate a unique 6-character alphanumeric invite code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Space(models.Model):
    """Shared financial space between users"""

    # Color choices for space customization
    COLOR_CHOICES = [
        ('blue', '🔵 Blue'),
        ('green', '🟢 Green'),
        ('red', '🔴 Red'),
        ('purple', '🟣 Purple'),
        ('yellow', '🟡 Yellow'),
        ('orange', '🟠 Orange'),
        ('pink', '🩷 Pink'),
        ('teal', '🟢 Teal'),
        ('indigo', '🟣 Indigo'),
        ('gray', '⚫ Gray'),
    ]

    # Icon choices for space customization
    ICON_CHOICES = [
        ('home', '🏠 Home'),
        ('wallet', '💰 Wallet'),
        ('heart', '❤️ Heart'),
        ('star', '⭐ Star'),
        ('family', '👨‍👩‍👧‍👦 Family'),
        ('travel', '✈️ Travel'),
        ('work', '💼 Work'),
        ('shopping', '🛍️ Shopping'),
        ('food', '🍽️ Food'),
        ('car', '🚗 Car'),
        ('house', '🏡 House'),
        ('business', '🏢 Business'),
    ]

    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Space name (2-100 characters)"
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        help_text="Optional description of the space"
    )
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default='blue',
        help_text="Color theme for this space"
    )
    icon = models.CharField(
        max_length=20,
        choices=ICON_CHOICES,
        default='wallet',
        help_text="Icon for this space"
    )
    invite_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_invite_code,
        help_text="6-character invite code for joining"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_spaces',
        help_text="User who created this space"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this space is active"
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this space was archived (null if not archived)"
    )

    # Members relationship through SpaceMember
    members = models.ManyToManyField(
        User,
        through='SpaceMember',
        related_name='spaces',
        blank=True
    )

    class Meta:
        db_table = 'spaces'
        ordering = ['-created_at']
        verbose_name = 'Space'
        verbose_name_plural = 'Spaces'

    def __str__(self):
        return f"{self.name} ({self.invite_code})"

    def clean(self):
        """Custom validation"""
        if self.name and len(self.name.strip()) < 2:
            raise ValidationError({'name': 'Space name must be at least 2 characters long'})

        # Validate space name length
        if self.name and len(self.name.strip()) > 50:
            raise ValidationError({'name': 'Space name cannot be longer than 50 characters'})

        # Validate description length
        if self.description and len(self.description.strip()) > 200:
            raise ValidationError({'description': 'Space description cannot be longer than 200 characters'})

        # Prevent duplicate space names for the same user (when creating)
        if self.name and self.created_by:
            duplicate_check = Space.objects.filter(
                name__iexact=self.name.strip(),
                spacemember__user=self.created_by,
                spacemember__role='owner',
                spacemember__is_active=True,
                is_active=True
            ).exclude(pk=self.pk)

            if duplicate_check.exists():
                raise ValidationError({'name': 'You already have a space with this name. Please choose a different name.'})

    def save(self, *args, **kwargs):
        """Ensure invite code is unique and uppercase"""
        if not self.invite_code:
            self.invite_code = generate_invite_code()

        # Ensure invite code is unique
        while Space.objects.filter(invite_code=self.invite_code).exclude(pk=self.pk).exists():
            self.invite_code = generate_invite_code()

        self.invite_code = self.invite_code.upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def archive(self):
        """Archive the space instead of deleting it"""
        from django.utils import timezone
        self.archived_at = timezone.now()
        self.is_active = False
        self.save()

    def unarchive(self):
        """Unarchive the space"""
        self.archived_at = None
        self.is_active = True
        self.save()

    @property
    def is_archived(self):
        """Check if space is archived"""
        return self.archived_at is not None

    @property
    def member_count(self):
        """Get current number of members"""
        return self.spacemember_set.filter(is_active=True).count()

    @property
    def is_full(self):
        """Check if space has reached maximum capacity (10 members)"""
        return self.member_count >= 10

    @property
    def owner(self):
        """Get the space owner"""
        try:
            return self.spacemember_set.get(role='owner', is_active=True).user
        except SpaceMember.DoesNotExist:
            return self.created_by

    @property
    def color_class(self):
        """Get the Tailwind CSS class for the space color"""
        color_map = {
            'blue': 'bg-blue-500',
            'green': 'bg-green-500',
            'red': 'bg-red-500',
            'purple': 'bg-purple-500',
            'yellow': 'bg-yellow-500',
            'orange': 'bg-orange-500',
            'pink': 'bg-pink-500',
            'teal': 'bg-teal-500',
            'indigo': 'bg-indigo-500',
            'gray': 'bg-gray-500',
        }
        return color_map.get(self.color, 'bg-blue-500')

    @property
    def icon_class(self):
        """Get the icon class mapping for display"""
        icon_map = {
            'home': 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
            'wallet': 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
            'heart': 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
            'star': 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
            'family': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
            'travel': 'M12 19l9 2-9-18-9 18 9-2zm0 0v-8',
            'work': 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0H8m8 0v6m-8-6v6m0 0v4a2 2 0 002 2h4a2 2 0 002-2v-4M8 12h8',
            'shopping': 'M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 12H6L5 9z',
            'food': 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v4m6-4a2 2 0 100-4m0 4a2 2 0 100 4m0-4v4m6-4a2 2 0 100-4m0 4a2 2 0 100 4m0-4v4',
            'car': 'M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z M13 16v6 M6 10h2.5l3.5-4h4.5s1 0 1 1v4h2 M3 11h3',
            'house': 'M8 14v3a1 1 0 001 1h3m-4-4V9a1 1 0 011-1h4a1 1 0 011 1v5m-4 0h4a1 1 0 001-1v-5a1 1 0 00-1-1H9a1 1 0 00-1 1v5z',
            'business': 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
        }
        return icon_map.get(self.icon, icon_map['wallet'])

    def can_user_join(self, user):
        """Check if a user can join this space"""
        if not self.is_active:
            return False, "Space is not active"

        if self.is_full:
            return False, "Space is full (maximum 10 members)"

        if self.spacemember_set.filter(user=user, is_active=True).exists():
            return False, "User is already a member of this space"

        return True, "User can join"

    def add_member(self, user, role='member'):
        """Add a user as a member to this space"""
        can_join, message = self.can_user_join(user)
        if not can_join:
            raise ValidationError(message)

        # Create or reactivate membership
        member, created = SpaceMember.objects.get_or_create(
            space=self,
            user=user,
            defaults={'role': role, 'is_active': True}
        )

        if not created and not member.is_active:
            member.is_active = True
            member.role = role
            member.save()

        return member


class SpaceMember(models.Model):
    """Relationship between users and spaces with roles"""

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('member', 'Member'),
    ]

    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this membership is active"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the user's default space"
    )

    class Meta:
        db_table = 'space_members'
        unique_together = [['space', 'user']]
        ordering = ['role', 'joined_at']
        verbose_name = 'Space Member'
        verbose_name_plural = 'Space Members'

    def __str__(self):
        return f"{self.user.username} in {self.space.name} ({self.role})"

    def clean(self):
        """Custom validation"""
        # Ensure only one owner per space
        if self.role == 'owner' and self.is_active:
            existing_owner = SpaceMember.objects.filter(
                space=self.space,
                role='owner',
                is_active=True
            ).exclude(pk=self.pk)

            if existing_owner.exists():
                raise ValidationError('A space can only have one owner')

        # Ensure only one default space per user
        if self.is_default and self.is_active:
            existing_default = SpaceMember.objects.filter(
                user=self.user,
                is_default=True,
                is_active=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError('A user can only have one default space')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
