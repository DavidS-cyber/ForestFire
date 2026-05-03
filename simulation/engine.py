"""
engine.py — Lógica pura del modelo Drossel-Schwabl.
Sin dependencias de Django. Totalmente testeable de forma aislada.

Estados de celda:
  0 — Vacía
  1 — Árbol
  2 — En llamas
"""

import numpy as np


def create_grid(size: int) -> np.ndarray:
    """
    Crea una cuadrícula inicial NxN con todos los valores a 0 (vacío).

    Parámetros:
        size (int): Lado de la cuadrícula. Debe estar entre 20 y 200.

    Retorna:
        np.ndarray de shape (size, size) con dtype uint8.
    """
    return np.zeros((size, size), dtype=np.uint8)


def step(grid: np.ndarray, p: float, f: float) -> tuple[np.ndarray, int]:
    """
    Avanza la simulación un paso aplicando las reglas de Drossel-Schwabl
    de forma simultánea a todas las celdas.

    Reglas:
        1. Vacía (0) → Árbol (1) con probabilidad p.
        2. Árbol (1) con al menos un vecino en llamas (2) → En llamas (2).
        3. Árbol (1) sin vecinos en llamas → En llamas (2) con probabilidad f (rayo).
        4. En llamas (2) → Vacía (0).

    Parámetros:
        grid (np.ndarray): Cuadrícula actual de shape (N, N).
        p    (float):      Probabilidad de que una celda vacía se convierta en árbol.
        f    (float):      Probabilidad de ignición por rayo.

    Retorna:
        tuple[np.ndarray, int]:
            - Nueva cuadrícula tras aplicar las reglas.
            - Tamaño total del incendio ocurrido en este paso (nº de celdas quemadas).
    """
    size = grid.shape[0]
    new_grid = grid.copy()

    # Máscara de celdas en llamas en el paso actual
    on_fire = (grid == 2)

    # Determinar qué árboles tienen vecinos en llamas (conectividad 4-vecindad)
    neighbor_fire = np.zeros((size, size), dtype=bool)
    neighbor_fire[:-1, :] |= on_fire[1:, :]   # sur
    neighbor_fire[1:, :]  |= on_fire[:-1, :]  # norte
    neighbor_fire[:, :-1] |= on_fire[:, 1:]   # este
    neighbor_fire[:, 1:]  |= on_fire[:, :-1]  # oeste

    # Regla 4: En llamas → Vacía
    new_grid[on_fire] = 0

    # Regla 1: Vacía → Árbol con probabilidad p
    empty = (grid == 0)
    grow = np.random.random((size, size)) < p
    new_grid[empty & grow] = 1

    # Regla 2: Árbol con vecino en llamas → En llamas
    trees = (grid == 1)
    new_grid[trees & neighbor_fire] = 2

    # Regla 3: Árbol sin vecino en llamas → Rayo con probabilidad f
    lightning = np.random.random((size, size)) < f
    new_grid[trees & ~neighbor_fire & lightning] = 2

    # Calcular el tamaño del incendio de este paso
    fire_size = int(np.sum(new_grid == 2))

    return new_grid, fire_size


def grid_to_list(grid: np.ndarray) -> list[list[int]]:
    """
    Convierte la cuadrícula numpy a lista de listas de Python para serialización JSON.

    Parámetros:
        grid (np.ndarray): Cuadrícula de shape (N, N).

    Retorna:
        list[list[int]]: Representación anidada de la cuadrícula.
    """
    return grid.tolist()


def list_to_grid(data: list[list[int]]) -> np.ndarray:
    """
    Convierte una lista de listas (procedente de JSON) a un array numpy.

    Parámetros:
        data (list[list[int]]): Cuadrícula serializada.

    Retorna:
        np.ndarray de dtype uint8.
    """
    return np.array(data, dtype=np.uint8)


def tree_density(grid: np.ndarray) -> float:
    """
    Calcula la densidad de árboles sobre el total de celdas.

    Parámetros:
        grid (np.ndarray): Cuadrícula actual.

    Retorna:
        float en [0.0, 1.0].
    """
    total = grid.size
    if total == 0:
        return 0.0
    return float(np.sum(grid == 1)) / total


def update_fire_histogram(histogram: dict, fire_size: int) -> dict:
    """
    Actualiza el histograma acumulado de tamaños de incendio.

    Parámetros:
        histogram (dict): Histograma actual {tamaño: frecuencia}.
        fire_size (int):  Tamaño del incendio del paso actual.

    Retorna:
        dict actualizado.
    """
    if fire_size > 0:
        key = str(fire_size)
        histogram[key] = histogram.get(key, 0) + 1
    return histogram