from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.utils.translation import gettext as _

class LandingView(TemplateView):
    """Public landing page"""
    template_name = 'public/landing.html'
    
    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('Gestión Financiera Compartida'),
            'hero_title': _('Gestiona tus finanzas familiares sin complicaciones'),
            'hero_subtitle': _('MonAI te ayuda a compartir gastos, crear presupuestos y mantener el control financiero con tu familia y amigos.'),
            'cta_login': _('Iniciar Sesión'),
            'cta_register': _('Crear Cuenta'),
            'features': [
                {
                    'title': _('Espacios Compartidos'),
                    'description': _('Crea espacios para diferentes grupos: familia, roommates, pareja.'),
                    'icon': 'users'
                },
                {
                    'title': _('Gastos Divididos'), 
                    'description': _('Divide gastos automáticamente y mantén balances claros.'),
                    'icon': 'calculator'
                },
                {
                    'title': _('Presupuestos Inteligentes'),
                    'description': _('Planifica gastos mensuales y recibe alertas de límites.'),
                    'icon': 'chart-bar'
                }
            ]
        })
        return context
