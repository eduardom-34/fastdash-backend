# api/endpoints.py
"""
Capa de exposición HTTP (Nivel 1).
- /analyze: subir archivo, extraer schema y obtener sugerencias (IA/heurística).
- /chart-data: generar series agregadas listas para graficar.
- /schema/{file_id}: consultar solo el schema del DF en cache.
- /suggestions/{file_id}/refresh: recalcular sugerencias para un DF ya subido.
- /session/{file_id}: borrar DF de memoria.
"""

from __future__ import annotations
from typing import Dict, Any
import io

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Esquemas (contratos)
from models.schemas import (
    AnalyzeResponse,
    AnalyzeSuggestion,
    ChartRequest,
    ChartDataResponse,
)

# Cache (almacenamiento temporal)
from core.cache import save_df, get_df, delete_df

# Servicios (lógica de negocio)
from services.data_processor import read_file_to_df, extract_schema, summarize_for_chart
from services.ai_analyzer import get_suggestions

router = APIRouter(prefix="/api", tags=["fastdash"])


@router.get("/health")
def health() -> Dict[str, str]:
    """Ping de salud para monitoreo y readiness checks."""
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    """
    Flujo:
    1) Recibe archivo (CSV/XLSX)
    2) Convierte a DataFrame (pandas)
    3) Extrae schema (columnas, tipos, preview, resumen)
    4) Genera sugerencias de gráficos (heurísticas)
    5) Guarda DF en cache y devuelve file_id + schema + sugerencias
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Archivo vacío o no recibido.")

    # Leer a DF
    try:
        df = read_file_to_df(io.BytesIO(raw), filename=file.filename)
    except Exception as ex:
        raise HTTPException(status_code=422, detail=f"Error leyendo archivo: {ex}")

    # Schema para UI e IA
    schema = extract_schema(df)

    # Sugerencias (IA/heurística)
    try:
        suggestions_raw = get_suggestions(
            columns=df.columns,
            dtypes=df.dtypes.to_dict(),
            summary_text=schema.get("summary_text", "")
        )
        suggestions = [AnalyzeSuggestion(**s) for s in suggestions_raw]
        if not suggestions:
            # Fallback amigable
            first_col = schema["columns"][0] if schema.get("columns") else "Columna"
            suggestions = [
                AnalyzeSuggestion(
                    id="s_fallback",
                    title=f"Conteo por {first_col}",
                    chart_type="bar",
                    parameters={"x_axis": first_col, "agg": "count", "top_n": 10},
                    insight=f"Distribución de registros por {first_col}."
                )
            ]
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"No fue posible generar sugerencias: {ex}")

    # Guardar en cache
    file_id = save_df(df)

    return AnalyzeResponse(
        file_id=file_id,
        schema=schema,
        suggestions=suggestions
    )


@router.post("/chart-data", response_model=ChartDataResponse)
async def chart_data(req: ChartRequest):
    """
    Flujo:
    1) Recupera DF desde cache con file_id
    2) Agrega/agrupa con pandas según 'parameters' de la sugerencia elegida
    3) Devuelve series listas para graficar y un pequeño summary
    """
    # Validar file_id
    try:
        df = get_df(req.file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="file_id inválido o expirado.")

    # Generar series
    try:
        series = summarize_for_chart(df, req.suggestion.parameters)
    except Exception as ex:
        raise HTTPException(status_code=422, detail=f"Error al procesar datos: {ex}")

    total = float(sum(p.value for p in series)) if series else 0.0
    return ChartDataResponse(
        series=series,
        summary={"total": total, "points": len(series)}
        # Nivel 1: sin 'analysis'
    )


@router.get("/schema/{file_id}")
def get_schema(file_id: str):
    """
    Devuelve únicamente el schema del DataFrame en cache.
    Útil para rehidratar la UI al recargar.
    """
    try:
        df = get_df(file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="file_id inválido o expirado.")
    return extract_schema(df)


@router.post("/suggestions/{file_id}/refresh")
def refresh_suggestions(file_id: str):
    """
    Recalcula sugerencias para un DF ya subido (sin reenviar archivo).
    """
    try:
        df = get_df(file_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="file_id inválido o expirado.")

    schema = extract_schema(df)
    suggestions = get_suggestions(
        columns=df.columns,
        dtypes=df.dtypes.to_dict(),
        summary_text=schema.get("summary_text", "")
    )
    return {"file_id": file_id, "suggestions": suggestions}


@router.delete("/session/{file_id}")
def delete_session(file_id: str):
    """
    Elimina de memoria el DF asociado a 'file_id' para liberar RAM.
    """
    existed = delete_df(file_id)
    return JSONResponse({"deleted": existed, "file_id": file_id})
