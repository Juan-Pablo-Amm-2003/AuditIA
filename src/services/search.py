"""
Búsqueda multi-método para ~100% efectividad.
"""
from src.db import search_fuzzy, get_by_codigo, parse_medication_nombre
from src.utils import normalize_description, extract_specifications
import re

def search_medication(query: str, k: int = 5, threshold: float = 0.5) -> List[dict]:
    """
    Búsqueda multi-método usando las funciones existentes de DB.
    Prioriza búsqueda por código, luego fuzzy, luego componentes.
    """
    results = []
    original_query = query

    # 1. Primero intentar buscar por código exacto
    codigo_result = get_by_codigo(query.strip())
    if codigo_result:
        parsed = parse_medication_nombre(codigo_result[1])  # nombre es el segundo elemento
        results.append({
            "codigo": codigo_result[0],
            "nombre": codigo_result[1],
            "precio": float(codigo_result[2]) if codigo_result[2] else None,
            "score": 100.0,  # Match exacto
            "specifications": {
                "brand": parsed.get('brand', ''),
                "active": parsed.get('active', ''),
                "form": parsed.get('form', ''),
                "dose": parsed.get('dose', ''),
                "pack": parsed.get('pack', '')
            }
        })

    # 2. Si no hay match exacto, buscar fuzzy
    if not results:
        fuzzy_results = search_fuzzy(query, k=k*2)  # Buscar más para filtrar después
        for row in fuzzy_results:
            if len(results) >= k:
                break

            # Calcular score basado en la similitud
            score = _calculate_similarity_score(query, row[1])  # nombre es row[1]

            if score >= threshold:
                parsed = parse_medication_nombre(row[1])
                results.append({
                    "codigo": row[0],
                    "nombre": row[1],
                    "precio": float(row[2]) if row[2] else None,
                    "score": score,
                    "specifications": {
                        "brand": parsed.get('brand', ''),
                        "active": parsed.get('active', ''),
                        "form": parsed.get('form', ''),
                        "dose": parsed.get('dose', ''),
                        "pack": parsed.get('pack', '')
                    }
                })

    # 3. Fallback: buscar por componentes individuales
    if not results:
        components = _extract_search_components(query)
        for component in components:
            if len(results) >= k:
                break

            fuzzy_results = search_fuzzy(component, k=3)
            for row in fuzzy_results:
                if len(results) >= k:
                    break

                # Evitar duplicados
                if not any(r["codigo"] == row[0] for r in results):
                    parsed = parse_medication_nombre(row[1])
                    results.append({
                        "codigo": row[0],
                        "nombre": row[1],
                        "precio": float(row[2]) if row[2] else None,
                        "score": 60.0,  # Score menor para matches parciales
                        "specifications": {
                            "brand": parsed.get('brand', ''),
                            "active": parsed.get('active', ''),
                            "form": parsed.get('form', ''),
                            "dose": parsed.get('dose', ''),
                            "pack": parsed.get('pack', '')
                        }
                    })

    return results


def _calculate_similarity_score(query: str, db_name: str) -> float:
    """
    Calcula un score de similitud entre la consulta y el nombre en DB.
    """
    query_norm = normalize_description(query.lower())
    db_norm = normalize_description(db_name.lower())

    # Si contiene palabras clave importantes, aumentar score
    query_words = set(query_norm.split())
    db_words = set(db_norm.split())

    common_words = query_words.intersection(db_words)
    if common_words:
        # Bonus por palabras en común
        return min(95.0, 70.0 + len(common_words) * 10.0)

    # Si la consulta está contenida en el nombre DB
    if query_norm in db_norm:
        return 85.0

    # Si el nombre DB está contenido en la consulta
    if db_norm in query_norm:
        return 75.0

    return 50.0  # Score base


def _extract_search_components(query: str) -> List[str]:
    """
    Extrae componentes de búsqueda de la consulta.
    """
    components = []

    # Buscar dosis (números con unidades)
    dose_patterns = [
        r'(\d+\s*(?:mg|g|ml|mcg|ui|mg/ml))',
        r'(\d+(?:mg|g|ml|mcg|ui|mg/ml))'
    ]

    for pattern in dose_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        components.extend([match.strip() for match in matches])

    # Buscar formas comunes
    form_patterns = [
        r'\b(comprimidos|comprimido|comp|tabletas|tableta|tabs?|cápsulas|cápsula|caps?|ampollas|ampolla|amp|inyectable|crema|pomada|gotas|jarabe|suspensión|polvo)\b',
        r'\b(sobres|sobre|envases|envase|frascos|frasco|tubos|tubo)\b'
    ]

    for pattern in form_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        components.extend([match.strip() for match in matches])

    # Si no hay componentes específicos, dividir por conectores comunes
    if not components:
        parts = re.split(r'\s+(?:\+|y|con|de)\s+', query, flags=re.IGNORECASE)
        components.extend([part.strip() for part in parts if len(part.strip()) > 3])

    return list(set(components))  # Eliminar duplicados
