import logging
from sqlalchemy import create_engine, text
from src.config import settings
from src.utils import normalize_description as normalize_text

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)

__all__ = ["get_conn", "get_by_codigo", "search_fuzzy", "get_by_exact_name"]

def get_conn():
    return engine.connect()

def get_by_codigo(codigo: str):
    with get_conn() as cn:
        query = text("""
            SELECT codigo, nombre, precio FROM medicamentos WHERE codigo = :codigo
            UNION
            SELECT codigo, nombre, precio FROM medicamentos WHERE troquel = :codigo
        """)
        result = cn.execute(query, {"codigo": codigo}).fetchone()
        return result

def search_fuzzy(q: str, k: int = 10):
    qn = normalize_text(q)
    if not qn: return []
    words = qn.split()
    if not words: return []
    
    with get_conn() as cn:
        where_clauses = " AND ".join(["nombre ILIKE :word{}".format(i) for i in range(len(words))])
        params = {f'word{i}': f"%{word}%" for i, word in enumerate(words)}
        params['k'] = k
        
        query = text(f"""
            SELECT codigo, nombre, precio FROM medicamentos 
            WHERE {where_clauses} 
            ORDER BY LENGTH(nombre) 
            LIMIT :k
        """)
        
        logger.debug(f"Ejecutando búsqueda fuzzy PRECISA: {query} con {params}")
        results = cn.execute(query, params).fetchall()
        
        if not results and len(words) > 1:
            logger.warning(f"Búsqueda precisa para '{qn}' sin resultados. Activando fallback.")
            fallback_params = {'word0': f"%{words[0]}%", 'k': k}
            fallback_query = text("""
                SELECT codigo, nombre, precio FROM medicamentos 
                WHERE nombre ILIKE :word0 
                ORDER BY LENGTH(nombre) 
                LIMIT :k
            """)
            results = cn.execute(fallback_query, fallback_params).fetchall()

        logger.debug(f"Búsqueda fuzzy para '{qn}' encontró {len(results)} candidatos.")
        return results

def get_by_exact_name(nombre: str):
    with get_conn() as cn:
        query = text("SELECT codigo, nombre, precio FROM medicamentos WHERE LOWER(nombre) = LOWER(:nombre)")
        return cn.execute(query, {"nombre": nombre}).fetchone()