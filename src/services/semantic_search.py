import logging
import numpy as np
import faiss
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from src.db import get_conn, parse_medication_nombre
from src.models import MedicationSpec

logger = logging.getLogger(__name__)

# --- Singleton Pattern para el Servicio de Búsqueda Semántica ---
_semantic_search_instance = None

class SemanticSearchService:
    """Servicio dedicado para búsquedas semánticas usando embeddings."""

    def __init__(self, model_name: str = 'paraphrase-MiniLM-L3-v2'):
        """La inicialización ahora es rápida, no construye el índice."""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.medication_data = []

    def _build_index(self):
        """Construye el índice FAISS con los embeddings de los medicamentos."""
        logger.info("Construyendo índice de búsqueda semántica... (esto puede tardar la primera vez)")
        try:
            with get_conn() as cn:
                cur = cn.cursor()
                cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos")
                self.medication_data = cur.fetchall()

            if not self.medication_data:
                logger.warning("No se encontraron medicamentos para el índice.")
                return

            med_names = [med[1] for med in self.medication_data]
            med_embeddings = self.model.encode(med_names)

            dimension = med_embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(np.array(med_embeddings))
            logger.info(f"Índice construido con {len(self.medication_data)} medicamentos.")
        except Exception as e:
            logger.error(f"Fallo al construir el índice de búsqueda semántica: {e}")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Realiza una búsqueda semántica."""
        if not self.index:
            logger.warning("El índice de búsqueda semántica no está disponible.")
            return []
        # (El resto del método search se mantiene igual)
        try:
            query_embedding = self.model.encode([query])
            scores, indices = self.index.search(query_embedding, min(k, len(self.medication_data)))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and score > 0.5:
                    med = self.medication_data[idx]
                    parsed = parse_medication_nombre(med[1])
                    results.append({
                        "codigo": med[0], "nombre": med[1], "precio": float(med[2]) if med[2] else None,
                        "score": float(score) * 100,
                        "specifications": MedicationSpec(**parsed),
                        "search_method": "semantic"
                    })
            return results
        except Exception as e:
            logger.error(f"Error en la búsqueda semántica: {e}")
            return []

def get_semantic_search_service():
    """Función para obtener la instancia única del servicio (Singleton)."""
    global _semantic_search_instance
    if _semantic_search_instance is None:
        _semantic_search_instance = SemanticSearchService()
        _semantic_search_instance._build_index()
    return _semantic_search_instance