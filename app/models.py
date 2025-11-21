from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any

# Definimos los tipos permitidos de gráficos
ChartType = Literal['bar', 'line', 'pie', 'scatter']

class ChartParameters(BaseModel):
    x_axis: str
    y_axis: str
    aggregation: Optional[Literal['sum', 'avg', 'count', 'none']] = 'sum'

# Lo que la IA nos va a devolver (Estructura estricta)
class AIAnalysisSuggestion(BaseModel):
    title: str
    chart_type: ChartType
    parameters: ChartParameters
    insight: str

# Respuesta del endpoint de Upload
class UploadResponse(BaseModel):
    file_id: str
    filename: str
    summary: str
    suggestions: List[AIAnalysisSuggestion]