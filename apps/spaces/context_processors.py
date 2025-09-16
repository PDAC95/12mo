"""
Context processors for spaces app
"""
from .utils import get_space_context


def space_context(request):
    """
    Add space context to all templates
    """
    if request.user.is_authenticated:
        return {
            'space_context': get_space_context(request)
        }

    return {
        'space_context': {
            'current_space': None,
            'current_space_name': 'Not logged in',
            'user_role': None,
            'is_owner': False,
            'has_spaces': False
        }
    }