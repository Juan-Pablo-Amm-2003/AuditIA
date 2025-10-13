import re
import pandas as pd
from typing import List
import logging

logger = logging.getLogger(__name__)

REPLACEMENTS = {
    r'\bCOMP\b': 'COMPRIMIDO', r'\bGTS\b': 'GOTAS', r'\bSOL\b': 'SOLUCION',
    r'\bINY\b': 'INYECTABLE', r'\bAMP\b': 'AMPOLLA', r'\bFCO\b': 'FRASCO',
    r'\bCAPS\b': 'CAPSULA', r'\bPDA\b': 'POMADA', r'\bAG\b': 'AGUA',
    r'\bDEST\b': 'DESTILADA', r'\bSOL[\.\s]FISIOL\b': 'SOLUCION FISIOLOGICA',
}

def normalize_description(desc: str) -> str:
    if not isinstance(desc, str): return ""
    normalized_desc = desc.upper().strip()
    for pattern, replacement in REPLACEMENTS.items():
        normalized_desc = re.sub(pattern, replacement, normalized_desc)
    normalized_desc = re.sub(r'(\d+)\s*(MG|G|ML|UI|MCG|GRS|GR)', r'\1 \2', normalized_desc)
    normalized_desc = re.sub(r'[^A-Z0-9\s]', ' ', normalized_desc)
    normalized_desc = re.sub(r'\s+', ' ', normalized_desc).strip()
    return normalized_desc

def clean_and_deduplicate(items: List[dict]) -> pd.DataFrame:
    if not items: return pd.DataFrame()
    df = pd.DataFrame(items)
    for col in ['cantidad', 'precio_total', 'precio_unitario']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['normalized_desc'] = df['descripción'].apply(normalize_description)
    agg_rules = {
        'cantidad': 'sum', 'precio_total': 'sum', 'descripción': 'first',
        'precio_unitario': 'first', 'fecha': 'first', 'notas': 'first'
    }
    return df.groupby('normalized_desc').agg(agg_rules).reset_index()