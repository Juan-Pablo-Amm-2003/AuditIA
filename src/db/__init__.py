import logging
from sqlalchemy import create_engine, text
from src.config import settings
from src.utils import normalize_description as normalize_text

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)

__all__ = [
    "get_conn", "get_by_codigo", "search_fuzzy", "get_by_exact_name",
    "load_all_synonyms_from_db", "upsert_manual_correction"
]

def get_conn():
    return engine.connect()

def get_by_codigo(codigo: str):
    """Obtiene un medicamento por su código."""
    with get_conn() as cn:
        query = text("""
            SELECT codigo, nombre, precio FROM medicamentos WHERE codigo = :codigo
            UNION
            SELECT codigo, nombre, precio FROM medicamentos WHERE troquel = :codigo
        """)
        result = cn.execute(query, {"codigo": codigo}).fetchone()
        return result

def load_all_synonyms_from_db():
    """Carga todos los sinónimos y correcciones desde la BD a un diccionario."""
    # Usamos la sintaxis de PostgreSQL para la consulta
    query = text("SELECT nombre_factura, codigo_medicamento, metodo FROM sinonimos_factura")
    mappings = {}
    with get_conn() as conn:
        result = conn.execute(query)
        for row in result:
            # El resultado de la consulta es (nombre_factura, codigo_medicamento, metodo)
            mappings[row[0]] = {"codigo": row[1], "metodo": row[2]}
    logger.info(f"Cargados {len(mappings)} mapeos desde la base de datos.")
    return mappings

def upsert_manual_correction(nombre_factura: str, codigo_medicamento: str):
    """Inserta o actualiza una corrección manual (UPSERT) en PostgreSQL."""
    query = text("""
        INSERT INTO sinonimos_factura (nombre_factura, codigo_medicamento, metodo)
        VALUES (:nombre_factura, :codigo_medicamento, 'Manual')
        ON CONFLICT (nombre_factura)
        DO UPDATE SET
            codigo_medicamento = EXCLUDED.codigo_medicamento,
            metodo = 'Manual';
    """)
    with get_conn() as conn:
        conn.execute(query, {"nombre_factura": nombre_factura, "codigo_medicamento": codigo_medicamento})
        conn.commit() # ¡Importante! Confirmar la transacción

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