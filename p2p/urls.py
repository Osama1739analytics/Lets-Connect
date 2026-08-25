from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from home.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('home.urls')),
    
    # Google OAuth via social-auth
    path('auth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'home.views.page_not_found'
handler500 = 'home.views.server_error'
