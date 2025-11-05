# models/schemas.py
from pydantic import BaseModel, Field
from typing import Dict, Any


ChartType = Literal["bar", "line", "pie", "scatter"]

class AnalyzeRequest(BaseModel):
    
    # Esto representa una sugerencia de gráfico generada por la IA.
    id: str = Field(..., description="ID únio de la sugerencia de grafico")
    title: str = Field(..., description="Título del gráfico")
    chart_type: ChartType = Field(..., description="Tipo de gráfico")
    parameters: Dict[str, Any] = Field(..., description="Parámetros del gráfico")
    insights: str = Field(..., description="Insights del gráfico")
    
class AnalyzeResponse(BaseModel):
    # Respuesta completa del endpoint /analyze
    file_id: str = Field(..., description="ID del archivo cargado")
    schema: Dict[str, any] = Field(..., description="Esquema del gráfico")
    suggestion: List[AnalyzeRequest] = Field(..., description="Sugerencias de gráficos")

# Solicitud para generar un gráfico

class ChartRequest(BaseModel):
    # Peticion que se envia al endpoint /chart-data
    file_id: str = Field(..., description="ID del archivo cargado")
    suggestion: AnalyzeSuggestion = Field(..., description="Sugerencia de gráfico")
    
class ChartSeriesPoint(BaseModel):
    # un punto o barra dentro del grafico
    label: str = Field(..., description="Etiqueta del punto o barra")
    value: float = Field(..., description="Valor del punto asociada a la etiqueta")
    
class ChartDataResponse(BaseModel):
    # Respuesta devuelta por /chart-data
    # Contine los datos procesado y listos para graficar
    serie: List[ChatSeriesPoint] = Field(..., description="Serie de puntos o barras para el gráfico")
    summary: Optional[Dict[str, float]] = Field(
        None,
        description="Resumen de los datos procesados"
        )
    
# Ejemplos para swagger
class ExampleData:
    analyze_example = {
        "file_id": "f123abc",
        "schema": {
            "columns": ["Categoria", "Ventas"],
            "dtypes": {"Categoria": "object", "Ventas": "float64"},
            "rows": 30
        },
        "suggestions": [
            {
                "id": "s1",
                "title": "Ventas por categoría",
                "chart_type": "bar",
                "parameters": {"x_axis": "Categoria", "y_axis": "Ventas", "agg": "sum"},
                "insight": "La categoría Electrónica lidera las ventas."
            }
        ]
    }

    chart_response_example = {
        "series": [
            {"label": "Electrónica", "value": 21000.0},
            {"label": "Ropa", "value": 9500.0},
            {"label": "Hogar", "value": 6800.0}
        ],
        "summary": {"total": 37300.0, "points": 3},
        "analysis": "Las ventas de Electrónica son el doble que las de Ropa."
    }