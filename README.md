# FastDash Backend

Backend construido con FastAPI y Python para el procesamiento de datos con Pandas e integración con IA.

## Instalación

1. Crear entorno virtual: `python -m venv venv`
2. Activar entorno: `source venv/bin/activate` (Linux/Mac) o `venv\Scripts\activate` (Windows)
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar `.env` con tu `OPENAI_API_KEY`.

## Ejecución

```bash
uvicorn app.main:app --reload
```

