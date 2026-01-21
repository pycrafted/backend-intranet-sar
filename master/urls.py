"""
URL configuration for master project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .media_views import MediaView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/health/', include('health.urls')),
    path('api/actualites/', include('actualites.urls')),
    path('api/annuaire/', include('annuaire.urls')),
    path('api/accueil/', include('accueil.urls')),
    path('api/mai/', include('mai.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/organigramme/', include('organigramme.urls')),
    path('api/reseau-social/', include('reseau_social.urls')),
    path('api/forum/', include('forum.urls')),
    path('api/security/', include('security.urls')),
    path('api/metriques/', include('metriques.urls')),
    # URL pour servir les fichiers média avec CORS
    path('media/<path:path>', MediaView.as_view(), name='media'),
]

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
