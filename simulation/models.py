"""
models.py — Modelo de base de datos para la simulación de incendios forestales.
"""

import uuid
import json
import numpy as np

from django.db import models
from simulation.engine import create_grid, grid_to_list, list_to_grid


class Simulation(models.Model):
    """
    Representa una simulación de incendios forestales activa en el servidor.

    Almacena el estado completo de la cuadrícula, los parámetros del modelo
    y las estadísticas acumuladas a lo largo de su vida.

    Campos:
        id          (UUID):    Identificador único generado automáticamente.
        size        (int):     Lado de la cuadrícula NxN (entre 20 y 200).
        p           (float):   Probabilidad de que una celda vacía se convierta en árbol.
        f           (float):   Probabilidad de ignición por rayo.
        steps       (int):     Número de pasos ejecutados desde la creación.
        grid_data   (JSON):    Estado actual de la cuadrícula serializado.
        fire_histogram (JSON): Histograma acumulado {tamaño_incendio: frecuencia}.
        created_at  (datetime): Fecha y hora de creación.
        updated_at  (datetime): Fecha y hora de última modificación.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    size = models.IntegerField()
    p = models.FloatField()
    f = models.FloatField()
    steps = models.IntegerField(default=0)
    grid_data = models.JSONField(default=list)
    fire_histogram = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Simulation {self.id} ({self.size}x{self.size}) — paso {self.steps}"

    def get_grid(self) -> np.ndarray:
        """Devuelve la cuadrícula como array numpy."""
        return list_to_grid(self.grid_data)

    def set_grid(self, grid: np.ndarray) -> None:
        """Guarda la cuadrícula numpy en el campo JSON."""
        self.grid_data = grid_to_list(grid)

    def tree_density(self) -> float:
        """Calcula la densidad de árboles sobre el total de celdas."""
        grid = self.get_grid()
        total = grid.size
        if total == 0:
            return 0.0
        return float(np.sum(grid == 1)) / total

    @classmethod
    def create_new(cls, size: int, p: float, f: float) -> 'Simulation':
        """
        Crea y persiste una nueva simulación con cuadrícula vacía.

        Parámetros:
            size (int):   Lado de la cuadrícula.
            p    (float): Probabilidad de crecimiento.
            f    (float): Probabilidad de rayo.

        Retorna:
            Instancia de Simulation guardada en base de datos.
        """
        sim = cls(size=size, p=p, f=f)
        grid = create_grid(size)
        sim.set_grid(grid)
        sim.save()
        return sim