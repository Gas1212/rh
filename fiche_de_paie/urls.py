from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_paie, name='generate_paie'),
    path('calculer-auto/', views.calcul_auto_ajax, name='calcul_auto_ajax'),
    path('simulateur/', views.simulateur_paie, name='simulateur_paie'),
               
]
