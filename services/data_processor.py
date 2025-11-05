from __future__ import annotations
from typing import Any, Dict, List, Optional
import io
import pandas as pd

from models.schemas import ChartSeriesPoint

# Esto lo que hará es: Leer el archivo, Extraccion de schema y agregación parametrizada 
# para enerar series listas para graficar


def _safe_convert_dtypes(df: pd..DataFrame) -> pd.DataFrame:
    # Convertir tipos al dtype mas apropiado
    
    try:
        return df.convert_dtypes()
    except Exception as e:
        # Si hay un error, se devuelve el DataFrame original
        return df
    
def _try_parse_datatimes(df: pd.DataFrame) -> pd.DataFrame:
    # Intentar parsear columnas que parecen fechas
    date_like = [c for c in df.columns if str(c).lower() in {"fecha", "date", "fechahora", "datetime", "timestamp", "mes"}]
    for col in date_like:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="ignore", infer_datetime_format=True)
            except Exception:
                pass
    return df

def _read_excel(buffer: io.BytesIO) -> pd.DataFrame:
    # Lee el excel o csv, requiere openpyxl instalado, por defecto toma la primera hoja
    buffer.seek(0)
    return pd.read_excel(buffer)

# Esta es la api publica para procesar un archivo y generar series listas para graficar

def read_file_df(file_byte: io.BytesIO, filename: str) -> pd.DataFrame:
    # lee un archivo CSV o XLSX y devuelve un DataFrame
    name = (filename or "").lower()
    if name.endswith(".csv"):
        df = _read_csv(file_byte)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = _read_csv(file_byte)
    else:
        try:
            df = _read_csv(file_byte)
        except expression:
            df = _read_excel(file_byte)
            
            # normalizaciones basicas
            df = _safe_convert_dtypes(df)
            df = _try_parse_datatimes(df)
            return df

def extract_schema(df: pd.DataFrame) -> Dict[str, Any]:
    # Devuelve un diccionario con metadatos del dataframe
    columns = [str(c) for c in df.columns]
    dtypes = {str(k): str(v) for k, v in df.dtypes.items()}
    rows = int(len(df))
    
    # vista previs pequeña para la UI
    preview_rows = 15 if rows >= 15 else rows
    preview = df.head(preview_rows).fillna("").astype(str).to_dict(orient="records")
    
    # Clasificacion simple de columnas
    numeric_cols = [c for c in df.columns if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])]
    categorical_cols = [c for c in df.columns if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_numeric_dtype(df[c])]
    
    # Resuen estadistico
    try:
        summary_text = df.describe(include="all", datetime_is_numeric=True).fillna("").to_string()
    except Exception:
        summary_text = ""
    
    return {
        "columns": columns,
        "dtypes": dtypes,
        "rows": rows,
        "preview": preview,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "summary_text": summary_text,
    }
    
sef summarize_for_chart(df: pd.DataFrame, parameters: Dict[str, any]) -> List[ChartSeriesPoint]:
    # se usa pandas para producir datos listos para graficar
    
    x = parameters.get("x_axis")
    y = parameters.get("y_axis")
    agg = (parameters.get("agg") or "sum").lower()
    filters = parameters.get("filters")
    top_n = parameters.get("top_n")
    sort_dir = (parameters.get("sort") or "desc").lower()
    
    work = df.copy()
    
    # Filtros simples
    if isinstance(filters, dict):
        for col, val in filters.items():
            if col not in work.columns:
                continue
            if isinstance(val, list):
                work = work[work[col].isin(val)]
            else:
                work = work[work[col] == val]
    if x is None or x not in work.columns:
        # Si no hay x válido, devolvemos un fallback con primeras filas indexadas
        head = work.head(10)
        return [ChartSeriesPoint(label=str(i), value=float(i)) for i in range(len(head))]

    # --- Caso: X e Y presentes → agregación sobre Y agrupada por X
    if y and y in work.columns and pd.api.types.is_numeric_dtype(work[y]):
        # Elegir función de agregación
        if agg == "mean":
            grouped = work.groupby(x, dropna=False)[y].mean().reset_index()
        elif agg == "count":
            # cuenta el número de registros por categoría de X (independiente de Y)
            grouped = work.groupby(x, dropna=False)[y].count().reset_index()
        else:
            # sum por defecto
            grouped = work.groupby(x, dropna=False)[y].sum().reset_index()

        # Ordenar por valor (si procede)
        value_col = y if agg in {"sum", "mean"} else y  # para count también cae en y
        if sort_dir in {"asc", "desc"}:
            grouped = grouped.sort_values(by=value_col, ascending=(sort_dir == "asc"))

        # Limitar top_n (si se pide)
        if isinstance(top_n, int) and top_n > 0:
            grouped = grouped.head(top_n)

        # Mapear a series
        return [
            ChartSeriesPoint(label=str(row[x]), value=float(row[value_col]))
            for _, row in grouped.iterrows()
        ]

    # --- Solo X presente (sin Y o Y no numérico) → conteo por categoría
    counts = work[x].value_counts(dropna=False).reset_index()
    counts.columns = [x, "count"]

    if sort_dir in {"asc", "desc"}:
        counts = counts.sort_values(by="count", ascending=(sort_dir == "asc"))

    if isinstance(top_n, int) and top_n > 0:
        counts = counts.head(top_n)

    return [
        ChartSeriesPoint(label=str(row[x]), value=float(row["count"]))
        for _, row in counts.iterrows()
    ]




