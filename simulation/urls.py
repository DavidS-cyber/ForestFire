"""
urls.py — Rutas de la API de simulación de incendios forestales.

Las rutas están definidas en la especificación del proyecto y no pueden modificarse.
"""

from django.urls import path
from simulation.views import (
    SimulationListView,
    SimulationDetailView,
    SimulationStepView,
    WeatherView,
)

urlpatterns = [
    path('simulations/', SimulationListView.as_view(), name='simulation-list'),
    path('simulations/<uuid:pk>/', SimulationDetailView.as_view(), name='simulation-detail'),
    path('simulations/<uuid:pk>/step/', SimulationStepView.as_view(), name='simulation-step'),
    path('weather/', WeatherView.as_view(), name='weather'),
]