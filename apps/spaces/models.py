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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
