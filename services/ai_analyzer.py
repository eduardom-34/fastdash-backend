from __future__ import annotations
from typing import Any, Dict, Iterable, List
import re
from itertools import count


def _is_date_col(name: str) -> bool:
    
    # Heurística simple por nombre de columna (en español e inglés)
    n = name.strip().lower()
    return n in {"fecha", "fechahora", "datetime", "timestamp", "mes", "date", "day", "month"} or \
           bool(re.search(r"(fecha|date|_at)$", n))
           
           
def _score_categorical(n_unique: int, total_rows: int) -> float:
    
    # Puntua qué tan 'graficable' es una columna categórica.
    if total_rows <= 0:
        return 0.0
    if n_unique <= 1:
        return 0.0
    # ratio de categorías vs filas
    ratio = n_unique / max(1, total_rows)
    # campana centrada aprox en 10 categorías
    target = 10
    diff = abs(n_unique - target)
    return 1.0 / (1.0 + diff) - ratio * 0.2

def _pick_best_categorical(columns: Iterable[str], dtypes: Dict[str, Any], summary_text: str, sample_counts: Dict[str, int], total_rows: int) -> List[str]:
    
    # Ordena columnas candidatas categóricas por 'graficabilidad'
    cands = []
    for c in columns:
        # Excluye columnas numéricas conocidas por nombre
        if str(dtypes.get(c, "")).startswith(("int", "float", "Int", "Float")):
            continue
        n_unique = sample_counts.get(c, 0)
        score = _score_categorical(n_unique, total_rows)
        cands.append((score, c))
    cands.sort(reverse=True)
    return [c for _, c in cands]

def _pick_numeric_priority(columns: Iterable[str], dtypes: Dict[str, Any]) -> List[str]:
    
    Prioriza columnas numéricas comunes para KPIs (VentaTotal, Ventas, Importe, Monto, etc.),
    names = list(columns)
    numeric = [c for c in names if str(dtypes.get(c, "")).lower().startswith(("int", "float"))]
    # Heurísticas por nombre
    priority_keywords = ["ventatotal", "ventas", "importe", "monto", "total", "cantidadvendida", "cantidad", "precio", "precioUnitario".lower()]
    def key_fn(c: str) -> int:
        cn = c.lower()
        for i, k in enumerate(priority_keywords):
            if k in cn:
                return i  # menor es mejor
        return 100 + numeric.index(c) if c in numeric else 999
    numeric.sort(key=key_fn)
    return numeric

def _first_date(columns: Iterable[str]) -> str | None:
    for c in columns:
        if _is_date_col(c):
            return c
    return None

def get_suggestions(columns: Iterable[str], dtypes: Dict[str, Any], summary_text: str = "") -> List[Dict[str, Any]]:
    """
    Devuelve una lista de sugerencias de gráficos (3–5) basadas en heurísticas.
    - columns: nombres de columnas del DataFrame
    - dtypes:  dict {col: dtype_str}
    - summary_text: opcional, por si deseas ajustar reglas en el futuro
    """
    cols = list(columns)
    if not cols:
        return []

    # Estimación MUY ligera de cardinalidad por nombre (si tuvieras valores reales, pásalos aquí).
    # Por now, asumimos cardinalidad intermedia si no sabemos (10).
    sample_counts = {c: 10 for c in cols}

    # Candidatas
    date_col = _first_date(cols)
    numeric_cols = _pick_numeric_priority(cols, dtypes)  # ordenadas por prioridad de negocio
    categorical_ranked = _pick_best_categorical(cols, dtypes, summary_text, sample_counts, total_rows=1000)

    suggestions: List[Dict[str, Any]] = []
    sid = count(1)  # s1, s2, s3...

    # 1) Tendencia temporal si hay fecha + numérico
    if date_col and numeric_cols:
        y = numeric_cols[0]
        suggestions.append({
            "id": f"s{next(sid)}",
            "title": f"Tendencia de {y} por {date_col}",
            "chart_type": "line",
            "parameters": {"x_axis": date_col, "y_axis": y, "agg": "sum", "sort": "asc"},
            "insight": f"Evolución de {y} a lo largo del tiempo."
        })

    # 2) Barras por mejor categórica (x) vs numérico prioritario (y)
    if categorical_ranked and numeric_cols:
        x = categorical_ranked[0]
        y = numeric_cols[0]
        suggestions.append({
            "id": f"s{next(sid)}",
            "title": f"{y} por {x}",
            "chart_type": "bar",
            "parameters": {"x_axis": x, "y_axis": y, "agg": "sum", "sort": "desc", "top_n": 12},
            "insight": f"Comparación de {y} entre categorías de {x}."
        })

    # 3) Pie de proporciones por la mejor categórica (conteo)
    if categorical_ranked:
        x = categorical_ranked[0]
        suggestions.append({
            "id": f"s{next(sid)}",
            "title": f"Proporción por {x}",
            "chart_type": "pie",
            "parameters": {"x_axis": x, "agg": "count", "top_n": 10},
            "insight": f"Distribución de registros por {x}."
        })

    # 4) Barras por segunda categórica si existe
    if len(categorical_ranked) >= 2 and numeric_cols:
        x2 = categorical_ranked[1]
        y = numeric_cols[0]
        suggestions.append({
            "id": f"s{next(sid)}",
            "title": f"{y} por {x2}",
            "chart_type": "bar",
            "parameters": {"x_axis": x2, "y_axis": y, "agg": "sum", "sort": "desc", "top_n": 12},
            "insight": f"Comparativa de {y} según {x2}."
        })

    # 5) Dispersión si hay dos numéricas
    if len(numeric_cols) >= 2:
        y1, y2 = numeric_cols[0], numeric_cols[1]
        suggestions.append({
            "id": f"s{next(sid)}",
            "title": f"Relación {y1} vs {y2}",
            "chart_type": "scatter",
            "parameters": {"x_axis": y1, "y_axis": y2},
            "insight": f"Relación entre {y1} y {y2}; útil para ver correlaciones y outliers."
        })

    # Fallbacks si quedamos cortos
    if not suggestions and cols:
        x = cols[0]
        suggestions.append({
            "id": f"s{next(sid)}",
            "title": f"Conteo por {x}",
            "chart_type": "bar",
            "parameters": {"x_axis": x, "agg": "count", "top_n": 10},
            "insight": f"Vista general de frecuencias por {x}."
        })

    # Limitar a 5 máx.
    return suggestions[:5]