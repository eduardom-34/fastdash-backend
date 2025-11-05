# models/schemas.py
from pydantic import BaseModel
from typing import Dict, Any

class ChartRequest(BaseModel):
    file_id: str
    chart_type: str
    parameters: Dict[str, Any]