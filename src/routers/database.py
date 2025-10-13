import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Query
from src.db import search_fuzzy

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/db", tags=["Búsqueda en Base de Datos"])

@router.get("/search_medicamentos", response_model=List[Dict[str, Any]])
async def search_medicamentos_endpoint(q: str = Query(..., min_length=3)):
    """
    Endpoint de búsqueda en vivo para que el front-end encuentre candidatos
    en la base de datos de medicamentos.
    """
    results = search_fuzzy(q, k=15)
    # Convertimos los resultados a un formato JSON amigable
    candidates = [{"codigo": r[0], "nombre": r[1], "precio": r[2]} for r in results]
    return candidates