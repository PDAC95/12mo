from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils.translation import gettext as _
from django.http import JsonResponse

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view for authenticated users"""
    template_name = 'dashboard/home.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Dashboard'),
            'welcome_message': _('Bienvenido a MonAI'),
            'user': self.request.user,
        })
        return context

@login_required
def dashboard(request):
    """Legacy dashboard view - kept for compatibility"""
    context = {
        'page_title': _('Dashboard'),
        'balance_title': _('Balance'),
        'expenses_title': _('Expenses'),
        'budget_title': _('Monthly Budget'),
    }
    return render(request, 'dashboard/index.html', context)

def set_language(request):
    """Language switching endpoint"""
    from django.conf import settings
    from django.http import HttpResponseRedirect
    from django.utils import translation
    
    language = request.GET.get('language')
    if language and language in dict(settings.LANGUAGES):
        translation.activate(language)
        response = HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
        return response
    
    return JsonResponse({'error': 'Invalid language'}, status=400)
