# 🔥 Forest Fire Simulator — Drossel-Schwabl

Simulación de incendios forestales como servicio web.  
Proyecto individual — Desarrollo Web en Entorno Servidor, UD4.

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Instalación

```bash
uv sync
python manage.py migrate
python manage.py runserver
```

Abre http://127.0.0.1:8000 en tu navegador.

## Tests

```bash
pytest
```

## Estructura

```
forest-fire/
├── core/           # Configuración Django
├── simulation/
│   ├── engine.py   # Lógica pura del modelo (sin Django)
│   ├── weather.py  # Integración Open-Meteo
│   ├── models.py   # Modelo Simulation
│   ├── serializers.py
│   ├── views.py    # Endpoints API REST
│   ├── urls.py
│   └── templates/index.html
└── tests/
```

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/simulations/` | Crear simulación |
| GET | `/api/simulations/{id}/` | Estado actual |
| POST | `/api/simulations/{id}/step/` | Avanzar pasos |
| PATCH | `/api/simulations/{id}/` | Modificar p/f |
| DELETE | `/api/simulations/{id}/` | Eliminar |
| GET | `/api/weather/?city=...` | Parámetros por clima |