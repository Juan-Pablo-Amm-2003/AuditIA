import asyncio
import logging
import json
from typing import List, Dict, Any
from pathlib import Path
from thefuzz import fuzz
from src.db import get_by_exact_name, search_fuzzy, get_by_codigo
from src.services.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)
SYNONYMS_FILE = Path("data/synonyms.json")

class OrchestrationService:
    """Orquesta el flujo completo de auditoría de ítems de factura."""
    def __init__(self):
        self.ai_agent = AIAssistant()
        self.synonyms = self._load_synonyms()

    def _load_synonyms(self) -> Dict[str, str]:
        """Carga el diccionario de sinónimos desde un archivo JSON."""
        if SYNONYMS_FILE.is_file():
            try:
                with open(SYNONYMS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError): return {}
        return {}

    async def process_items(self, items: List[Dict[str, Any]]) -> Dict[str, List]:
        """FASE 2: Procesa ítems para encontrar matches directos o preparar para la IA."""
        conciliados_exactos, pendientes_para_agente = [], []

        for item in items:
            nombre_factura = item["nombre_factura"]
            
            match_info = None
            
            # 1. Match por Sinónimo
            if nombre_factura in self.synonyms:
                codigo = self.synonyms[nombre_factura]
                logger.info(f"Match por Sinónimo para '{nombre_factura}' -> '{codigo}'")
                match = get_by_codigo(codigo)
                if match:
                    # MEJORA #1: Asignación de Score 100.0 y Método
                    match_info = {
                        "codigo_bd": match[0], 
                        "nombre_bd": match[1], 
                        "precio_referencia": float(match[2]) if match[2] else 0.0, 
                        "confianza": 100,
                        "score_coincidencia": 100.0,
                        "metodo_conciliacion": "Sinónimo" # <-- AÑADIDO
                    }
            
            # 2. Match Exacto (solo si no se encontró por sinónimo)
            if not match_info:
                exact_match = get_by_exact_name(nombre_factura)
                if exact_match:
                    # MEJORA #1: Asignación de Score 100.0 y Método
                    match_info = {
                        "codigo_bd": exact_match[0], 
                        "nombre_bd": exact_match[1], 
                        "precio_referencia": float(exact_match[2]) if exact_match[2] else 0.0, 
                        "confianza": 100,
                        "score_coincidencia": 100.0, # <-- AÑADIDO
                        "metodo_conciliacion": "Exacto" # <-- AÑADIDO
                    }

            if match_info:
                conciliados_exactos.append({**item, **match_info})
            else:
                # Lógica para ítems pendientes para la IA/Fuzzing
                fuzzy_rows = search_fuzzy(nombre_factura, k=50)
                candidatos_puntuados = []
                if fuzzy_rows:
                    for code, name, price in fuzzy_rows:
                        cand_dict = {"codigo": code, "nombre": name, "precio": float(price) if price is not None else 0.0}
                        score = fuzz.token_set_ratio(nombre_factura, cand_dict["nombre"])
                        if score > 45: candidatos_puntuados.append((score, cand_dict))
                
                candidatos_puntuados.sort(key=lambda x: x[0], reverse=True)
                
                top_10 = [{**cand, "score": score} for score, cand in candidatos_puntuados[:10]]
                mejor_intento = {"nombre_bd": candidatos_puntuados[0][1]['nombre'], "score": candidatos_puntuados[0][0]} if candidatos_puntuados else None
                
                pendientes_para_agente.append({**item, "candidatos_bd": top_10, "mejor_intento": mejor_intento})

        return {"conciliados_exactos": conciliados_exactos, "pendientes_para_agente": pendientes_para_agente}

    async def run_conciliation_phase(self, pendientes: List[Dict[str, Any]]) -> Dict[str, List]:
        """FASE 3: Ejecuta la conciliación con IA en paralelo."""
        tasks = [self.ai_agent.conciliate_item(item) for item in pendientes]
        results = await asyncio.gather(*tasks)
        conciliados_por_ia, fallidos = [], []

        for result, item in zip(results, pendientes):
            codigo = result.get("codigo_bd_conciliado")
            if codigo:
                candidato = next((c for c in item['candidatos_bd'] if c['codigo'] == codigo), None)
                if candidato:
                    # MEJORA #2: Obtener el score del candidato y Método IA
                    score = candidato.get('score', 0.0) 
                    
                    conciliados_por_ia.append({
                        **item, 
                        "codigo_bd": codigo, 
                        "nombre_bd": candidato.get('nombre'), 
                        "precio_referencia": candidato.get('precio', 0.0), 
                        "confianza": result.get("confianza", 0),
                        "score_coincidencia": score, # <-- CORRECCIÓN
                        "metodo_conciliacion": "IA/Fuzzy" # <-- AÑADIDO
                    })
            else:
                fallidos.append({**item, "mejor_intento": item.get("mejor_intento")})
        
        logger.info(f"Fase 3 completada: {len(conciliados_por_ia)} conciliados por IA.")
        return {"conciliados": conciliados_por_ia, "fallidos": fallidos}

    def _annotate_with_surcharges(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """FASE 4: Calcula y anota la información de sobreprecio."""
        annotated = []
        for item in items:
            report = item.copy()
            total_facturado, ref_unitario, cantidad = item.get("precio_total_agregado"), item.get("precio_referencia"), item.get("cantidad_total")
            report["monto_sobreprecio"], report["porcentaje_sobreprecio"] = 0.0, 0.0
            if all(v is not None for v in [total_facturado, ref_unitario, cantidad]) and ref_unitario > 0 and cantidad > 0:
                ref_total = ref_unitario * cantidad
                diferencia = total_facturado - ref_total
                report["monto_sobreprecio"] = round(diferencia, 2)
                report["porcentaje_sobreprecio"] = round((diferencia / ref_total) * 100, 2)
            annotated.append(report)
        return annotated

    def generate_final_summary(self, total_items: List[Dict[str, Any]], all_conciliated: List[Dict[str, Any]], fallidos: List[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
        """FASE 5: Construye el objeto de datos final para la respuesta de la API."""
        annotated = self._annotate_with_surcharges(all_conciliated)
        
        # Renombramos 'precio_unitario' a 'precio_factura' para el front-end
        for item in annotated:
            if 'precio_unitario' in item:
                item['precio_factura'] = item.pop('precio_unitario')
                
        sobreprecio = [item for item in annotated if item["porcentaje_sobreprecio"] > threshold]
        
        return {
            "metricas": {
                "ahorro_potencial": sum(d.get("monto_sobreprecio", 0) for d in sobreprecio),
                "monto_total_facturado": sum(i.get("precio_total_agregado", 0) for i in total_items),
                "items_procesados": len(total_items),
                "items_conciliados": len(all_conciliated),
                "items_con_sobreprecio": len(sobreprecio),
                "items_no_conciliados": len(fallidos)
            },
            "items_conciliados": annotated,
            "items_con_sobreprecio": sobreprecio,
            "items_no_conciliados": fallidos
        }