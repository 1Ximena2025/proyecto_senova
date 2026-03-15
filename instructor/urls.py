from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.panel_instructor, name='panel_instructor'),
    path('reportes_panel/', views.reportes_panel, name='reportes_panel'),
]
