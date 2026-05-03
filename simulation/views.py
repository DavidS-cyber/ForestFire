"""
views.py — Endpoints de la API REST para la simulación de incendios forestales.

Todos los endpoints devuelven JSON.
Las rutas y métodos HTTP son fijos según la especificación del proyecto.
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from simulation.models import Simulation
from simulation.serializers import (
    SimulationCreateSerializer,
    SimulationPatchSerializer,
    SimulationStateSerializer,
    StepSerializer,
)
from simulation.engine import step, update_fire_histogram
from simulation import weather as weather_module


class SimulationListView(APIView):
    """
    GET  /api/simulations/ — Lista todas las simulaciones existentes.
    POST /api/simulations/ — Crea una nueva simulación.
    """

    def get(self, request):
        """
        Lista todas las simulaciones almacenadas.

        Parámetros: ninguno.

        Respuesta 200:
            Lista de objetos SimulationState (sin el campo grid para aligerar la respuesta).
        """
        sims = Simulation.objects.all()
        data = []
        for sim in sims:
            data.append({
                "id": str(sim.id),
                "size": sim.size,
                "p": sim.p,
                "f": sim.f,
                "steps": sim.steps,
                "tree_density": round(sim.tree_density(), 4),
                "created_at": sim.created_at.isoformat(),
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Crea una nueva simulación con cuadrícula vacía.

        Body (JSON):
            size (int):   Lado de la cuadrícula NxN. Obligatorio. Rango [20, 200].
            p    (float): Probabilidad de crecimiento de árbol. Obligatorio. Rango [0, 1].
            f    (float): Probabilidad de ignición por rayo. Obligatorio. Rango [0, 1].

        Respuesta 201:
            Estado completo de la simulación recién creada (SimulationState).

        Respuesta 400:
            Errores de validación.
        """
        serializer = SimulationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sim = Simulation.create_new(
            size=serializer.validated_data['size'],
            p=serializer.validated_data['p'],
            f=serializer.validated_data['f'],
        )
        return Response(
            SimulationStateSerializer(sim).data,
            status=status.HTTP_201_CREATED,
        )


class SimulationDetailView(APIView):
    """
    GET    /api/simulations/{id}/ — Estado actual completo.
    PATCH  /api/simulations/{id}/ — Modifica p y/o f en caliente.
    DELETE /api/simulations/{id}/ — Elimina la simulación.
    """

    def get(self, request, pk):
        """
        Devuelve el estado completo de la simulación indicada.

        Parámetros de ruta:
            id (UUID): Identificador de la simulación.

        Respuesta 200:
            id             (str):   UUID.
            size           (int):   Lado de la cuadrícula.
            p              (float): Probabilidad de crecimiento.
            f              (float): Probabilidad de rayo.
            steps          (int):   Pasos ejecutados.
            grid           (list):  Cuadrícula serializada.
            tree_density   (float): Fracción de celdas con árbol.
            fire_histogram (dict):  Histograma acumulado {tamaño: frecuencia}.
            created_at     (str):   ISO 8601.
            updated_at     (str):   ISO 8601.

        Respuesta 404:
            La simulación no existe.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        return Response(SimulationStateSerializer(sim).data)

    def patch(self, request, pk):
        """
        Modifica los parámetros p y/o f de la simulación en caliente,
        sin reiniciar el estado de la cuadrícula.

        Parámetros de ruta:
            id (UUID): Identificador de la simulación.

        Body (JSON, todos opcionales):
            p (float): Nueva probabilidad de crecimiento. Rango [0, 1].
            f (float): Nueva probabilidad de rayo. Rango [0, 1].

        Respuesta 200:
            Estado actualizado de la simulación.

        Respuesta 400:
            Errores de validación.

        Respuesta 404:
            La simulación no existe.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        serializer = SimulationPatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if 'p' in data:
            sim.p = data['p']
        if 'f' in data:
            sim.f = data['f']
        sim.save()

        return Response(SimulationStateSerializer(sim).data)

    def delete(self, request, pk):
        """
        Elimina permanentemente la simulación y todos sus datos.

        Parámetros de ruta:
            id (UUID): Identificador de la simulación.

        Respuesta 204:
            Sin cuerpo. Eliminación exitosa.

        Respuesta 404:
            La simulación no existe.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        sim.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SimulationStepView(APIView):
    """
    POST /api/simulations/{id}/step/ — Avanza la simulación N pasos.

    Se usa POST (no GET) porque la operación modifica el estado del servidor,
    no es idempotente y no es segura: cada llamada produce un efecto secundario
    persistente (avanzar la simulación y actualizar la base de datos).
    """

    def post(self, request, pk):
        """
        Avanza la simulación un número determinado de pasos y actualiza las
        estadísticas acumuladas.

        Parámetros de ruta:
            id (UUID): Identificador de la simulación.

        Body (JSON):
            steps (int): Número de pasos a ejecutar. Por defecto 1. Rango [1, 1000].

        Respuesta 200:
            Estado completo actualizado de la simulación tras ejecutar los pasos.
            Incluye grid, tree_density y fire_histogram actualizados.

        Respuesta 400:
            Errores de validación.

        Respuesta 404:
            La simulación no existe.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        serializer = StepSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        n_steps = serializer.validated_data['steps']
        grid = sim.get_grid()
        histogram = sim.fire_histogram or {}

        for _ in range(n_steps):
            grid, fire_size = step(grid, sim.p, sim.f)
            histogram = update_fire_histogram(histogram, fire_size)

        sim.set_grid(grid)
        sim.fire_histogram = histogram
        sim.steps += n_steps
        sim.save()

        return Response(SimulationStateSerializer(sim).data)


class WeatherView(APIView):
    """
    GET /api/weather/?city={ciudad} — Devuelve p y f sugeridos según el clima actual.

    La consulta a Open-Meteo se realiza en el servidor, nunca desde el cliente JS.
    """

    def get(self, request):
        """
        Consulta la API de Open-Meteo para la ciudad indicada y devuelve los
        parámetros p y f sugeridos según las condiciones meteorológicas actuales.

        Lógica de ajuste:
            - Viento > 30 km/h  → reduce p.
            - Humedad > 70%     → aumenta p y f.
            - Temperatura > 35°C → aumenta f.

        Parámetros de query:
            city (str): Nombre de la ciudad. Obligatorio.

        Respuesta 200:
            p       (float): Probabilidad de crecimiento sugerida.
            f       (float): Probabilidad de rayo sugerida.
            city    (str):   Ciudad consultada.
            weather (dict):  Datos meteorológicos crudos (temperatura, humedad, viento).

        Respuesta 400:
            Falta el parámetro city o la ciudad no se encontró.

        Respuesta 503:
            Error de comunicación con Open-Meteo.
        """
        city = request.query_params.get('city', '').strip()
        if not city:
            return Response(
                {"error": "El parámetro 'city' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = weather_module.suggest_parameters(city)
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error consultando Open-Meteo: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )