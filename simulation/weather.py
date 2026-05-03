"""
weather.py — Consulta la API de Open-Meteo y sugiere parámetros p y f
basándose en las condiciones meteorológicas actuales.

Se llama exclusivamente desde el servidor Django (nunca desde el cliente JS).
"""

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Valores base del modelo
BASE_P = 0.05
BASE_F = 0.001


def get_coordinates(city: str) -> tuple[float, float]:
    """
    Obtiene las coordenadas geográficas de una ciudad usando la API de geocodificación
    de Open-Meteo.

    Parámetros:
        city (str): Nombre de la ciudad a buscar.

    Retorna:
        tuple[float, float]: (latitud, longitud)

    Lanza:
        ValueError si la ciudad no se encuentra.
        requests.RequestException si hay un error de red.
    """
    response = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "es", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Ciudad '{city}' no encontrada.")

    return results[0]["latitude"], results[0]["longitude"]


def get_weather(lat: float, lon: float) -> dict:
    """
    Consulta las condiciones meteorológicas actuales en las coordenadas dadas.

    Parámetros:
        lat (float): Latitud.
        lon (float): Longitud.

    Retorna:
        dict con las variables meteorológicas actuales:
            - temperature_2m (°C)
            - relativehumidity_2m (%)
            - windspeed_10m (km/h)

    Lanza:
        requests.RequestException si hay un error de red.
    """
    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    current = data.get("current", {})

    return {
        "temperature": current.get("temperature_2m", 20.0),
        "humidity": current.get("relative_humidity_2m", 50.0),
        "wind_speed": current.get("wind_speed_10m", 10.0),
    }


def suggest_parameters(city: str) -> dict:
    """
    Devuelve los parámetros p y f sugeridos para la simulación según las condiciones
    meteorológicas actuales de la ciudad indicada.

    Lógica de ajuste:
        - Viento > 30 km/h  → reduce p (los árboles caen o no crecen bien).
        - Humedad > 70%     → aumenta p (mejor crecimiento) y f (más tormentas).
        - Temperatura > 35°C → aumenta f (más probabilidad de ignición).

    Parámetros:
        city (str): Nombre de la ciudad.

    Retorna:
        dict con las claves:
            - p         (float): Probabilidad de crecimiento sugerida.
            - f         (float): Probabilidad de rayo sugerida.
            - city      (str):   Ciudad usada.
            - weather   (dict):  Datos meteorológicos crudos.

    Lanza:
        ValueError si la ciudad no se encuentra.
        requests.RequestException si hay un error de red.
    """
    lat, lon = get_coordinates(city)
    weather = get_weather(lat, lon)

    p = BASE_P
    f = BASE_F

    wind = weather["wind_speed"]
    humidity = weather["humidity"]
    temperature = weather["temperature"]

    # Ajuste por viento fuerte
    if wind > 30:
        p = max(0.001, p * 0.5)

    # Ajuste por humedad alta
    if humidity > 70:
        p = min(0.2, p * 1.5)
        f = min(0.01, f * 2.0)

    # Ajuste por temperatura alta
    if temperature > 35:
        f = min(0.01, f * 3.0)

    return {
        "p": round(p, 6),
        "f": round(f, 6),
        "city": city,
        "weather": weather,
    }