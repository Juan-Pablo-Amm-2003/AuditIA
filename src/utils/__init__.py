import re
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)

# Diccionario de sinónimos y reemplazos más completo
REPLACEMENTS = {
    # Formas farmacéuticas
    r'\bCOMP\b': 'COMPRIMIDO',
    r'\bGTS\b': 'GOTAS',
    r'\bSOL\b': 'SOLUCION',
    r'\bINY\b': 'INYECTABLE',
    r'\bAMP\b': 'AMPOLLA',
    r'\bFCO\b': 'FRASCO',
    r'\bCAPS\b': 'CAPSULA',
    r'\bPDA\b': 'POMADA',
    # Unidades y otros
    r'\bAG\b': 'AGUA',
    r'\bDEST\b': 'DESTILADA',
    r'\bSOL[\.\s]FISIOL\b': 'SOLUCION FISIOLOGICA',
}

def normalize_description(desc: str) -> str:
    """
    Normaliza la descripción de un medicamento de forma más robusta.
    """
    if not isinstance(desc, str):
        return ""
    
    logger.debug(f"Normalizando descripción original: '{desc}'")
    
    normalized_desc = desc.upper().strip()
    
    for pattern, replacement in REPLACEMENTS.items():
        normalized_desc = re.sub(pattern, replacement, normalized_desc)
    
    normalized_desc = re.sub(r'(\d+)\s*(MG|G|ML|UI|MCG|GRS|GR)', r'\1 \2', normalized_desc)
    normalized_desc = re.sub(r'[^A-Z0-9\s]', ' ', normalized_desc)
    normalized_desc = re.sub(r'\s+', ' ', normalized_desc).strip()
    
    logger.debug(f"Descripción normalizada: '{normalized_desc}'")
    return normalized_desc

def clean_and_deduplicate(items: List[dict]) -> pd.DataFrame:
    """
    Agrupa ítems por descripción, sumando cantidades y totales.
    """
    if not items:
        return pd.DataFrame()
        
    df = pd.DataFrame(items)
    
    # Asegurarse de que las columnas numéricas sean del tipo correcto
    df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0)
    df['precio_total'] = pd.to_numeric(df['precio_total'], errors='coerce').fillna(0)

    df['normalized_desc'] = df['descripción'].apply(normalize_description)

    # Agrupar por descripción normalizada y agregar los valores
    agg_rules = {
        'cantidad': 'sum',
        'precio_total': 'sum',
        'descripción': 'first', # Mantener la primera descripción original
        'precio_unitario': 'first', # Mantener el primer precio unitario
        'fecha': 'first',
        'notas': 'first'
    }
    
    aggregated_df = df.groupby('normalized_desc').agg(agg_rules).reset_index()
    
    return aggregated_df