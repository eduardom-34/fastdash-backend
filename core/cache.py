from __future__ import annotations
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from uuid import uuid4
from time import time
from threading import RLock

import pandas as pd

# Tiempo de vida (en segundos). sin expiracion usar None.
TTL_SECONDS: Optional[int] = 60 * 30  # 30 minutos


# Límite máximo de items en memoria. Si se supera, se purgan los más antiguos.
MAX_ITEMS: int = 100


@dataclass
class CacheItem:
    df: pd.DataFrame
    created_at: float  # epoch seconds


class DataCache:
    
    # Cache en memoria, seguro para hilos dentro de un solo proceso.
    def __init__(self) -> None:
        self._store: Dict[str, CacheItem] = {}
        self._lock = RLock()

    def _now(self) -> float:
        return time()

    def _is_expired(self, created_at: float) -> bool:
        if TTL_SECONDS is None:
            return False
        return (self._now() - created_at) > TTL_SECONDS

    def _purge_expired(self) -> None:
        """Elimina elementos expirados."""
        with self._lock:
            to_delete = [k for k, v in self._store.items() if self._is_expired(v.created_at)]
            for k in to_delete:
                self._store.pop(k, None)

    def _purge_if_over_limit(self) -> None:
        """Si se excede MAX_ITEMS, borra los más antiguos primero."""
        if MAX_ITEMS <= 0:
            return
        with self._lock:
            if len(self._store) <= MAX_ITEMS:
                return
            # Ordena por created_at ascendente (los más viejos primero)
            ordered = sorted(self._store.items(), key=lambda kv: kv[1].created_at)
            overflow = len(self._store) - MAX_ITEMS
            for k, _ in ordered[:overflow]:
                self._store.pop(k, None)

    # ------------- API pública -------------

    def save_df(self, df: pd.DataFrame) -> str:
        """Guarda un DataFrame y retorna un file_id único."""
        file_id = uuid4().hex
        with self._lock:
            self._store[file_id] = CacheItem(df=df, created_at=self._now())
            # Mantenimiento rápido
            self._purge_expired()
            self._purge_if_over_limit()
        return file_id

    def get_df(self, file_id: str) -> pd.DataFrame:
        """
        Recupera un DataFrame por file_id.
        Lanza KeyError si no existe o está expirado.
        """
        with self._lock:
            item = self._store.get(file_id)
            if item is None:
                raise KeyError("file_id no encontrado en cache.")

            if self._is_expired(item.created_at):
                # Limpia y reporta como no encontrado/expirado
                self._store.pop(file_id, None)
                raise KeyError("file_id expirado.")

            return item.df

    def delete_df(self, file_id: str) -> bool:
        """Elimina un DataFrame del cache. Devuelve True si existía."""
        with self._lock:
            return self._store.pop(file_id, None) is not None

    def stats(self) -> Tuple[int, int]:
        """
        Retorna (items_totales, items_no_expirados).
        Útil para depuración/monitorización.
        """
        with self._lock:
            total = len(self._store)
            alive = sum(0 if self._is_expired(v.created_at) else 1 for v in self._store.values())
            return total, alive

    def clear(self) -> None:
        """Vacía por completo la caché."""
        with self._lock:
            self._store.clear()


# Instancia global para usar desde los endpoints/servicios
_CACHE = DataCache()

# Funciones de módulo para una API simple (usadas por api/endpoints.py)
def save_df(df: pd.DataFrame) -> str:
    return _CACHE.save_df(df)

def get_df(file_id: str) -> pd.DataFrame:
    return _CACHE.get_df(file_id)

def delete_df(file_id: str) -> bool:
    return _CACHE.delete_df(file_id)

def cache_stats() -> Tuple[int, int]:
    return _CACHE.stats()

def clear_cache() -> None:
    _CACHE.clear()