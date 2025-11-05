# core/cache.py
import pandas as pd
from typing import Dict

# Este es nuestro caché en memoria. 
# La clave (key) será un file_id (str)
# El valor (value) será el DataFrame de pandas
DATA_CACHE: Dict[str, pd.DataFrame] = {}