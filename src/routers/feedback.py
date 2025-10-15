import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from src.db import upsert_manual_correction
from src.services.main_service import orchestrator # Importamos la instancia singleton
from src.utils import normalize_description # Importamos la función de normalización

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback y Aprendizaje"])

class ManualReview(BaseModel):
    nombre_factura: str
    codigo_bd_correcto: str

@router.post("/manual_review")
async def submit_manual_review(review: ManualReview = Body(...)):
    """
    Recibe una corrección manual y la guarda en la base de datos.
    """
    try:
        # Normalizamos el nombre de la factura para usarlo como clave consistente
        normalized_name = normalize_description(review.nombre_factura)
        
        logger.info(f"Guardando nuevo mapeo en la BD: '{normalized_name}' -> '{review.codigo_bd_correcto}'")
        upsert_manual_correction(normalized_name, review.codigo_bd_correcto)
        
        # Actualizamos el diccionario en memoria con la clave normalizada
        orchestrator.mappings[normalized_name] = {"codigo": review.codigo_bd_correcto, "metodo": "Manual"}
        
        return {"status": "success", "message": "Mapeo guardado correctamente en la base de datos."}
    except Exception as e:
        logger.error(f"Error al guardar la revisión manual en la BD: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo guardar la revisión manual en la base de datos.")