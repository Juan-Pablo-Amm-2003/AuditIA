import pyodbc
import logging
from src.utils import normalize_description as normalize_text

logger = logging.getLogger(__name__)

CS = ("DRIVER={ODBC Driver 18 for SQL Server};"
      "SERVER=localhost;"
      "DATABASE=alfabeta;"
      "Trusted_Connection=yes;"
      "Encrypt=no;TrustServerCertificate=yes;")

__all__ = ["get_conn", "get_by_codigo", "search_fuzzy", "get_by_exact_name"]

def get_conn():
    return pyodbc.connect(CS)

def get_by_codigo(codigo: str):
    with get_conn() as cn:
        cur = cn.cursor()
        r = cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos WHERE codigo = ?", codigo).fetchone()
        if r: return r
        return cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos WHERE troquel = ?", codigo).fetchone()

def search_fuzzy(q: str, k: int = 10):
    qn = normalize_text(q)
    if not qn: return []
    words = qn.split()
    if not words: return []
    
    with get_conn() as cn:
        cur = cn.cursor()
        where_clauses = " AND ".join(["nombre LIKE ?" for _ in words])
        params = [f"%{word}%" for word in words]
        query = f"SELECT TOP ({k}) codigo, nombre, precio FROM dbo.medicamentos WHERE {where_clauses} ORDER BY LEN(nombre)"
        
        logger.debug(f"Ejecutando búsqueda fuzzy PRECISA: {query} con {params}")
        cur.execute(query, *params)
        results = cur.fetchall()
        
        if not results and len(words) > 1:
            logger.warning(f"Búsqueda precisa para '{qn}' sin resultados. Activando fallback.")
            param = f"%{words[0]}%"
            fallback_query = f"SELECT TOP ({k}) codigo, nombre, precio FROM dbo.medicamentos WHERE nombre LIKE ? ORDER BY LEN(nombre)"
            cur.execute(fallback_query, param)
            results = cur.fetchall()

        logger.debug(f"Búsqueda fuzzy para '{qn}' encontró {len(results)} candidatos.")
        return results

def get_by_exact_name(nombre: str):
    with get_conn() as cn:
        cur = cn.cursor()
        return cur.execute("SELECT codigo, nombre, precio FROM dbo.medicamentos WHERE LOWER(nombre) = LOWER(?)", nombre).fetchone()