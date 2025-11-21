import uuid
from datetime import datetime

def generate_unique_id() -> str:
    """Genera un ID único para archivos o sesiones."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Devuelve el timestamp actual en formato ISO."""
    return datetime.now().isoformat()

