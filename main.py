# main.py
"""
Punto de entrada del backend FastDash.
- Inicializa la app FastAPI.
- Configura CORS (para comunicar con el frontend React).
- Monta los endpoints desde /api.
- Expone rutas raíz y documentación interactiva (/docs, /redoc).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar router principal
from api.endpoints import router as api_router


# -----------------------------------------------------------
# Crear aplicación
# -----------------------------------------------------------

app = FastAPI(
    title="FastDash Backend",
    description="API para análisis rápido de datos y generación de dashboards.",
    version="1.0.0",
    contact={
        "name": "FastDash Team",
        "url": "https://github.com/tu-repo",
        "email": "contacto@fastdash.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)


# -----------------------------------------------------------
# Configuración de CORS
# -----------------------------------------------------------

# ⚠️ Durante desarrollo puedes dejar allow_origins=["*"]
# En producción: especifica el dominio del frontend React (por seguridad)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ejemplo: ["http://localhost:5173", "https://fastdash.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------
# Rutas principales
# -----------------------------------------------------------

# Montar las rutas definidas en api/endpoints.py
app.include_router(api_router)


# -----------------------------------------------------------
# Rutas auxiliares
# -----------------------------------------------------------

@app.get("/")
def root():
    """
    Ruta raíz simple, devuelve información básica de servicio.
    """
    return {
        "service": "fastdash_backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "description": "Backend de análisis de datos para dashboards con IA (Nivel 1)."
    }
