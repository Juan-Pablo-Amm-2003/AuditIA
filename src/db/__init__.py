import pyodbc
import logging
from src.utils import normalize_description as normalize_text

logger = logging.getLogger(__name__)

CS = ("DRIVER={ODBC Driver 18 for SQL Server};"
      "SERVER=localhost;"
      "DATABASE=alfabeta;"
      "Trusted_Connection=yes;"
      "Encrypt=no;TrustServerCertificate=yes;")

__all__ = ["get_conn", "search_broadly_by_name", "get_by_codigo", "search_fuzzy", "get_by_exact_name"]

def get_conn():
    return pyodbc.connect(CS)

def _norm(s: str) -> str:
    return normalize_text(s)

def search_broadly_by_name(q: str, k: int = 100):
    """Búsqueda amplia por nombre usando un solo LIKE para generar un pool de candidatos."""
    qn = _norm(q)
    # Usamos solo la primera palabra para la búsqueda amplia
    search_term = qn.split()[0] if qn.split() else ""
    if not search_term:
        return []
    
    with get_conn() as cn:
        cur = cn.cursor()
        query = f"SELECT TOP ({k}) codigo, nombre, precio FROM dbo.medicamentos WHERE nombre LIKE ?"
        param = f"%{search_term}%"
        logger.debug(f"Ejecutando búsqueda AMPLIA con query: '{query}' y param: '{param}'")
        cur.execute(query, param)
        return cur.fetchall()

def get_by_codigo(codigo: str):
    with get_conn() as cn:
        cur = cn.cursor()
        logger.debug(f"Buscando por código/troquel exacto: '{codigo}'")
        r = cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos WHERE codigo = ?", codigo).fetchone()
        if r:
            return r
        return cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos WHERE troquel = ?", codigo).fetchone()

def search_fuzzy(q: str, k: int = 10):
    """
    Búsqueda fuzzy de alta cobertura con fallback.
    """
    qn = _norm(q)
    if not qn:
        return []

    words = qn.split()
    if not words:
        return []
    
    with get_conn() as cn:
        cur = cn.cursor()
        
        where_clauses = " AND ".join(["nombre LIKE ?" for _ in words])
        params = [f"%{word}%" for word in words]
        query = f"SELECT TOP ({k}) codigo, nombre, precio FROM dbo.medicamentos WHERE {where_clauses} ORDER BY LEN(nombre)"
        
        logger.debug(f"Ejecutando búsqueda fuzzy PRECISA con query: '{query}' y params: {params}")
        cur.execute(query, *params)
        results = cur.fetchall()
        
        if not results and len(words) > 1:
            logger.warning(f"La búsqueda precisa para '{qn}' no encontró resultados. Activando fallback.")
            first_word_param = f"%{words[0]}%"
            fallback_query = f"SELECT TOP ({k}) codigo, nombre, precio FROM dbo.medicamentos WHERE nombre LIKE ? ORDER BY LEN(nombre)"
            
            logger.debug(f"Ejecutando búsqueda FALLBACK con query: '{fallback_query}' y param: '{first_word_param}'")
            cur.execute(fallback_query, first_word_param)
            results = cur.fetchall()

        logger.debug(f"Búsqueda fuzzy para '{qn}' encontró {len(results)} candidatos.")
        return results

def get_by_exact_name(nombre: str):
    with get_conn() as cn:
        cur = cn.cursor()
        logger.debug(f"Buscando por nombre exacto: '{nombre}'")
        result = cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos WHERE LOWER(nombre) = LOWER(?)", nombre).fetchone()
        logger.debug(f"Resultado de búsqueda exacta: {result}")
        return result