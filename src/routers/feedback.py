import logging
import json
import asyncio
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback y Aprendizaje"])

# --- Definimos la ubicación de nuestro "diccionario" y un Lock para evitar conflictos ---
SYNONYMS_FILE = Path("data/synonyms.json")
file_lock = asyncio.Lock()

class ManualReview(BaseModel):
    nombre_factura: str
    codigo_bd_correcto: str

@router.post("/manual_review")
async def submit_manual_review(review: ManualReview = Body(...)):
    """
    Recibe una corrección manual y la guarda en el diccionario de sinónimos.
    """
    async with file_lock:
        try:
            # Asegurarse de que el directorio 'data' exista
            SYNONYMS_FILE.parent.mkdir(exist_ok=True)

            # Cargar el diccionario de sinónimos actual
            if SYNONYMS_FILE.is_file():
                with open(SYNONYMS_FILE, 'r', encoding='utf-8') as f:
                    synonyms = json.load(f)
            else:
                synonyms = {}

            # Añadir o actualizar el nuevo mapeo
            logger.info(f"Guardando nuevo mapeo: '{review.nombre_factura}' -> '{review.codigo_bd_correcto}'")
            synonyms[review.nombre_factura] = review.codigo_bd_correcto

            # Guardar el archivo actualizado
            with open(SYNONYMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(synonyms, f, ensure_ascii=False, indent=4)

            return {"status": "success", "message": "Mapeo guardado correctamente."}

        except Exception as e:
            logger.error(f"Error al guardar la revisión manual: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="No se pudo guardar la revisión manual.")