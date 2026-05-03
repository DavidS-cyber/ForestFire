"""
tests/test_engine.py — Tests unitarios del motor de simulación.
Se ejecutan con: pytest
"""

import numpy as np
import pytest
from simulation.engine import (
    create_grid,
    step,
    grid_to_list,
    list_to_grid,
    tree_density,
    update_fire_histogram,
)


def test_create_grid_shape():
    """La cuadrícula creada debe tener la forma correcta y estar vacía."""
    grid = create_grid(50)
    assert grid.shape == (50, 50)
    assert grid.dtype == np.uint8
    assert np.all(grid == 0)


def test_step_fire_becomes_empty():
    """Una celda en llamas debe convertirse en vacía en el siguiente paso."""
    grid = create_grid(5)
    grid[2, 2] = 2  # celda en llamas
    new_grid, _ = step(grid, p=0.0, f=0.0)
    assert new_grid[2, 2] == 0


def test_step_tree_catches_fire_from_neighbor():
    """Un árbol vecino de una celda en llamas debe incendiarse."""
    grid = create_grid(5)
    grid[2, 2] = 1  # árbol
    grid[2, 3] = 2  # vecino en llamas
    new_grid, _ = step(grid, p=0.0, f=0.0)
    assert new_grid[2, 2] == 2


def test_step_no_growth_with_p_zero():
    """Con p=0 y f=0 no deben aparecer árboles nuevos en celdas vacías."""
    grid = create_grid(10)
    new_grid, _ = step(grid, p=0.0, f=0.0)
    assert np.all(new_grid == 0)


def test_grid_serialization_roundtrip():
    """La conversión grid → lista → grid debe ser reversible."""
    grid = create_grid(10)
    grid[0, 0] = 1
    grid[1, 1] = 2
    recovered = list_to_grid(grid_to_list(grid))
    assert np.array_equal(grid, recovered)


def test_tree_density_empty():
    """La densidad de una cuadrícula vacía debe ser 0."""
    grid = create_grid(10)
    assert tree_density(grid) == 0.0


def test_tree_density_full():
    """La densidad de una cuadrícula llena de árboles debe ser 1."""
    grid = np.ones((10, 10), dtype=np.uint8)
    assert tree_density(grid) == 1.0


def test_update_fire_histogram():
    """El histograma debe acumular correctamente las frecuencias."""
    h = {}
    h = update_fire_histogram(h, 5)
    h = update_fire_histogram(h, 5)
    h = update_fire_histogram(h, 3)
    assert h['5'] == 2
    assert h['3'] == 1


def test_update_fire_histogram_zero_ignored():
    """Un incendio de tamaño 0 no debe añadirse al histograma."""
    h = {}
    h = update_fire_histogram(h, 0)
    assert len(h) == 0