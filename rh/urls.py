from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django_mongoengine import mongo_admin
from fiche_de_paie import views as paie_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('mongo-admin/', mongo_admin.site.urls),
    
    # Simulateur accessible directement via /simulateur/
    path('simulateur/', paie_views.simulateur_paie, name='simulateur_paie'),
    
    # Apps existantes
    path('paie/', include('fiche_de_paie.urls')),
    path('converter/', include('file_converter.urls')),
    
    # Apps principales
    path('jobs/', include('jobs.urls')),
    path('accounts/', include('accounts.urls')),
    
    # Home - EN DERNIER
    path('', include('accounts.urls')),
]

# Servir les fichiers media et static en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)