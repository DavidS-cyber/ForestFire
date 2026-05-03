"""
serializers.py — Serializers de Django REST Framework para la simulación.
"""

from rest_framework import serializers
from simulation.models import Simulation


class SimulationCreateSerializer(serializers.Serializer):
    """
    Serializer para la creación de una nueva simulación.

    Campos:
        size (int):   Lado de la cuadrícula. Debe estar entre 20 y 200.
        p    (float): Probabilidad de crecimiento de árbol. Rango [0.0, 1.0].
        f    (float): Probabilidad de ignición por rayo. Rango [0.0, 1.0].
    """

    size = serializers.IntegerField(min_value=20, max_value=200)
    p = serializers.FloatField(min_value=0.0, max_value=1.0)
    f = serializers.FloatField(min_value=0.0, max_value=1.0)


class SimulationPatchSerializer(serializers.Serializer):
    """
    Serializer para la modificación parcial de parámetros en caliente.

    Campos (todos opcionales):
        p (float): Nueva probabilidad de crecimiento. Rango [0.0, 1.0].
        f (float): Nueva probabilidad de rayo. Rango [0.0, 1.0].
    """

    p = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    f = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)


class StepSerializer(serializers.Serializer):
    """
    Serializer para solicitar el avance de N pasos.

    Campos:
        steps (int): Número de pasos a ejecutar. Por defecto 1. Mínimo 1, máximo 1000.
    """

    steps = serializers.IntegerField(min_value=1, max_value=1000, default=1)


class SimulationStateSerializer(serializers.ModelSerializer):
    """
    Serializer completo del estado de una simulación.

    Incluye el UUID, la cuadrícula serializada, los parámetros actuales,
    el número de pasos ejecutados, la densidad de árboles y el histograma
    acumulado de tamaños de incendio.

    Campos de respuesta:
        id              (str):   UUID de la simulación.
        size            (int):   Lado de la cuadrícula.
        p               (float): Probabilidad de crecimiento actual.
        f               (float): Probabilidad de rayo actual.
        steps           (int):   Pasos ejecutados.
        grid            (list):  Cuadrícula serializada como lista de listas.
        tree_density    (float): Fracción de celdas ocupadas por árboles.
        fire_histogram  (dict):  Histograma {tamaño: frecuencia}.
        created_at      (str):   ISO 8601 de creación.
        updated_at      (str):   ISO 8601 de última modificación.
    """

    tree_density = serializers.SerializerMethodField()
    grid = serializers.SerializerMethodField()

    class Meta:
        model = Simulation
        fields = [
            'id', 'size', 'p', 'f', 'steps',
            'grid', 'tree_density', 'fire_histogram',
            'created_at', 'updated_at',
        ]

    def get_tree_density(self, obj):
        return round(obj.tree_density(), 4)

    def get_grid(self, obj):
        return obj.grid_data