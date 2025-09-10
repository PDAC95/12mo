from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Main URL patterns
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Public pages (landing)
    path('', include('public.urls')),
    
    # Authentication (login, register, logout)
    path('', include('authentication.urls')),
    
    # Protected pages
    path('dashboard/', include('dashboard.urls')),
    
    # API endpoints (if needed later)
    # path('api/auth/', include('authentication.api_urls')),
]

# Static files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
