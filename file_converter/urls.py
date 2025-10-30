# file_converter/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.convert_to_pdf, name='file_converter'),
]