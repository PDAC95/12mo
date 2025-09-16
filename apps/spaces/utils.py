"""
Utilities for managing space context and navigation
"""
from django.shortcuts import get_object_or_404
from .models import Space, SpaceMember


class SpaceContextManager:
    """Manages the current space context for user sessions"""

    SESSION_KEY = 'current_space_id'
    DEFAULT_SPACE_NAME = 'Personal'

    @staticmethod
    def get_current_space_id(request):
        """Get the current space ID from session"""
        return request.session.get(SpaceContextManager.SESSION_KEY)

    @staticmethod
    def set_current_space(request, space_id):
        """Set the current space ID in session"""
        request.session[SpaceContextManager.SESSION_KEY] = space_id
        request.session.modified = True

    @staticmethod
    def get_current_space(request):
        """Get the current space object for the user"""
        space_id = SpaceContextManager.get_current_space_id(request)

        if space_id:
            try:
                # Verify user has access to this space
                space = Space.objects.get(
                    id=space_id,
                    spacemember__user=request.user,
                    spacemember__is_active=True,
                    is_active=True
                )
                return space
            except Space.DoesNotExist:
                # Space no longer exists or user lost access
                SpaceContextManager.clear_current_space(request)

        # No space set or invalid space - get default space
        return SpaceContextManager.get_default_space(request)

    @staticmethod
    def get_default_space(request):
        """Get the user's default space (pinned, Personal, or first available)"""
        # First, check for user's pinned/default space
        try:
            default_space = Space.objects.get(
                spacemember__user=request.user,
                spacemember__is_active=True,
                spacemember__is_default=True,
                is_active=True
            )
            # Set it as current space for future requests
            SpaceContextManager.set_current_space(request, default_space.id)
            return default_space
        except Space.DoesNotExist:
            pass

        # No pinned space, try to find a "Personal" space for this user
        personal_space = Space.objects.filter(
            name__iexact=SpaceContextManager.DEFAULT_SPACE_NAME,
            spacemember__user=request.user,
            spacemember__is_active=True,
            is_active=True
        ).first()

        if personal_space:
            # Set it as current space for future requests
            SpaceContextManager.set_current_space(request, personal_space.id)
            return personal_space

        # No "Personal" space found, get first available space
        first_space = Space.objects.filter(
            spacemember__user=request.user,
            spacemember__is_active=True,
            is_active=True
        ).first()

        if first_space:
            SpaceContextManager.set_current_space(request, first_space.id)
            return first_space

        # User has no spaces - this should be handled in views
        return None

    @staticmethod
    def clear_current_space(request):
        """Clear the current space from session"""
        if SpaceContextManager.SESSION_KEY in request.session:
            del request.session[SpaceContextManager.SESSION_KEY]
            request.session.modified = True

    @staticmethod
    def switch_space(request, space_id):
        """Switch to a different space (with permission check)"""
        try:
            # Verify user has access to this space
            space = Space.objects.get(
                id=space_id,
                spacemember__user=request.user,
                spacemember__is_active=True,
                is_active=True
            )
            SpaceContextManager.set_current_space(request, space_id)
            return space
        except Space.DoesNotExist:
            raise ValueError(f"Space {space_id} not found or access denied")

    @staticmethod
    def get_user_role_in_space(request, space):
        """Get user's role in the current space"""
        try:
            member = SpaceMember.objects.get(
                space=space,
                user=request.user,
                is_active=True
            )
            return member.role
        except SpaceMember.DoesNotExist:
            return None

    @staticmethod
    def set_default_space(request, space_id):
        """Set a space as the user's default space"""
        try:
            # Verify user has access to this space
            space = Space.objects.get(
                id=space_id,
                spacemember__user=request.user,
                spacemember__is_active=True,
                is_active=True
            )

            # Remove current default
            SpaceMember.objects.filter(
                user=request.user,
                is_active=True,
                is_default=True
            ).update(is_default=False)

            # Set new default
            member = SpaceMember.objects.get(
                space=space,
                user=request.user,
                is_active=True
            )
            member.is_default = True
            member.save()

            # Update session to use this space
            SpaceContextManager.set_current_space(request, space_id)
            return space

        except Space.DoesNotExist:
            raise ValueError(f"Space {space_id} not found or access denied")
        except SpaceMember.DoesNotExist:
            raise ValueError(f"User is not a member of space {space_id}")


def get_space_context(request):
    """
    Helper function to get complete space context for templates
    Returns dict with current space info and user permissions
    """
    current_space = SpaceContextManager.get_current_space(request)

    if not current_space:
        return {
            'current_space': None,
            'current_space_name': 'No Spaces',
            'user_role': None,
            'is_owner': False,
            'has_spaces': False
        }

    user_role = SpaceContextManager.get_user_role_in_space(request, current_space)

    # Check if this is the user's default space
    is_default_space = False
    try:
        member = SpaceMember.objects.get(
            space=current_space,
            user=request.user,
            is_active=True
        )
        is_default_space = member.is_default
    except SpaceMember.DoesNotExist:
        pass

    return {
        'current_space': current_space,
        'current_space_name': current_space.name,
        'user_role': user_role,
        'is_owner': user_role == 'owner',
        'has_spaces': True,
        'is_default_space': is_default_space
    }


def create_personal_space_if_needed(user):
    """
    Create a default "Personal" space for new users
    """
    # Check if user already has a "Personal" space
    personal_space = Space.objects.filter(
        name__iexact=SpaceContextManager.DEFAULT_SPACE_NAME,
        spacemember__user=user,
        spacemember__is_active=True,
        is_active=True
    ).first()

    if not personal_space:
        # Create default Personal space
        from .models import generate_invite_code

        personal_space = Space.objects.create(
            name=SpaceContextManager.DEFAULT_SPACE_NAME,
            description="Your personal financial space",
            created_by=user,
            invite_code=generate_invite_code()
        )

        # Add user as owner and set as default
        SpaceMember.objects.create(
            space=personal_space,
            user=user,
            role='owner',
            is_active=True,
            is_default=True
        )

    return personal_space