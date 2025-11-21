import pandas as pd
import os
import uuid
from typing import List, Dict, Any

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

class DataService:
    def save_file(self, file, filename: str) -> str:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(TEMP_DIR, f"{file_id}_{filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(file.read())
            
        return file_id, file_path

    def load_df(self, file_id: str, filename: str) -> pd.DataFrame:
        # En producción, esto vendría de S3 o una BD. Aquí usamos disco local.
        path = os.path.join(TEMP_DIR, f"{file_id}_{filename}")
        if filename.endswith('.csv'):
            return pd.read_csv(path)
        return pd.read_excel(path)

    def get_summary(self, df: pd.DataFrame) -> str:
        # Crea un resumen de texto para pasárselo a la IA
        buffer = []
        buffer.append(f"Columnas: {', '.join(df.columns)}")
        buffer.append("Tipos de datos:")
        for col, dtype in df.dtypes.items():
            buffer.append(f"- {col}: {dtype}")
        
        # Estadísticas básicas de columnas numéricas
        desc = df.describe().to_string()
        buffer.append(f"\nEstadísticas:\n{desc}")
        
        # Muestra las primeras 3 filas para dar contexto de los valores
        buffer.append(f"\nEjemplo de datos:\n{df.head(3).to_string()}")
        
        return "\n".join(buffer)

    def process_chart_data(self, df: pd.DataFrame, params: dict) -> List[Dict[str, Any]]:
        """
        Procesa los datos crudos para devolver solo lo necesario para el gráfico.
        Evita enviar 10,000 filas al frontend.
        """
        x = params.get('x_axis')
        y = params.get('y_axis')
        
        if not x or not y or x not in df.columns or y not in df.columns:
            raise ValueError(f"Columnas invalidas: {x}, {y}")

        # Lógica simple de agregación
        # Si es un gráfico de dispersión (scatter), no agrupamos, pero limitamos puntos
        if params.get('chart_type') == 'scatter':
            return df[[x, y]].dropna().head(500).to_dict(orient='records')
        
        # Para barras/lineas/pastel, agrupamos (ej: Ventas por Región)
        # Asumimos suma por defecto, podrías mejorarlo para aceptar 'avg' o 'count'
        try:
            df_grouped = df.groupby(x)[y].sum().reset_index()
            # Ordenar por valor descendente para mejores visualizaciones
            df_grouped = df_grouped.sort_values(by=y, ascending=False).head(20)
            return df_grouped.to_dict(orient='records')
        except Exception as e:
            # Fallback si no se puede agrupar (ej: fechas no parseadas)
            return df[[x, y]].head(50).to_dict(orient='records')