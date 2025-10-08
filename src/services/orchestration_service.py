import asyncio
import logging
from typing import List, Dict, Any
from thefuzz import fuzz
from src.db import get_by_exact_name, search_broadly_by_name, search_fuzzy
from src.services.ai_assistant import AIAssistant
from src.services.reporting_service import ReportingService

logger = logging.getLogger(__name__)

class OrchestrationService:
    def __init__(self):
        self.ai_agent = AIAssistant()
        self.reporting_service = ReportingService()

    async def process_items(self, items: List[Dict[str, Any]]) -> Dict[str, List]:
        logger.debug(f"--- FASE 2: INICIO --- Recibidos {len(items)} ítems para procesar.")
        conciliados_exactos = []
        pendientes_para_agente = []

        for item in items:
            nombre_factura = item["nombre_factura"]
            exact_match = get_by_exact_name(nombre_factura)

            if exact_match:
                logger.debug(f"Match exacto encontrado para: '{nombre_factura}'")
                conciliados_exactos.append({
                    "nombre_factura": nombre_factura, "precio_factura": item["precio_factura"],
                    "codigo_bd": exact_match[0], "nombre_bd": exact_match[1],
                    "precio_referencia": float(exact_match[2]) if exact_match[2] else None,
                    "confianza": 100
                })
            else:
                logger.debug(f"No hubo match exacto para: '{nombre_factura}'. Buscando candidatos...")
                
                fuzzy_candidates_rows = search_fuzzy(nombre_factura, k=50)
                
                candidatos_puntuados = []
                if fuzzy_candidates_rows:
                    for cand_row in fuzzy_candidates_rows:
                        cand_dict = {"codigo": cand_row[0], "nombre": cand_row[1], "precio": float(cand_row[2]) if cand_row[2] else None}
                        score = fuzz.token_set_ratio(nombre_factura, cand_dict["nombre"])
                        if score > 45:
                            candidatos_puntuados.append((score, cand_dict))
                
                candidatos_puntuados.sort(key=lambda x: x[0], reverse=True)

                # --- INICIO DE LA CORRECCIÓN ---
                # Si el mejor candidato tiene 100% de similitud, lo consideramos un match y no lo enviamos a la IA.
                if candidatos_puntuados and candidatos_puntuados[0][0] == 100:
                    logger.debug(f"Match de similitud 100% encontrado para: '{nombre_factura}'")
                    best_match = candidatos_puntuados[0][1]
                    conciliados_exactos.append({
                        "nombre_factura": nombre_factura, 
                        "precio_factura": item["precio_factura"],
                        "codigo_bd": best_match['codigo'], 
                        "nombre_bd": best_match['nombre'],
                        "precio_referencia": best_match['precio'],
                        "confianza": 100
                    })
                    continue  # Pasamos al siguiente ítem
                # --- FIN DE LA CORRECCIÓN ---

                top_10_candidatos_con_score = [
                    {**cand, "score": score} for score, cand in candidatos_puntuados[:10]
                ]
                
                mejor_intento = {"nombre_bd": candidatos_puntuados[0][1]['nombre'], "score": candidatos_puntuados[0][0]} if candidatos_puntuados else None

                pendientes_para_agente.append({
                    "nombre_factura": nombre_factura, 
                    "precio_factura": item["precio_factura"],
                    "candidatos_bd": top_10_candidatos_con_score,
                    "mejor_intento": mejor_intento
                })

        logger.debug(f"--- FASE 2: FIN --- {len(conciliados_exactos)} conciliados, {len(pendientes_para_agente)} pendientes.")
        return {"conciliados_exactos": conciliados_exactos, "pendientes_para_agente": pendientes_para_agente}

    async def run_conciliation_phase(self, pendientes: List[Dict[str, Any]]) -> Dict[str, List]:
        logger.debug(f"--- FASE 3: INICIO --- Enviando {len(pendientes)} ítems a Agno.")
        tasks = [self.ai_agent.conciliate_item(item) for item in pendientes]
        results = await asyncio.gather(*tasks)

        conciliados_por_ia = []
        fallidos_con_mejor_intento = []

        for result, original_item in zip(results, pendientes):
            logger.debug(f"Respuesta cruda de Agno para '{original_item['nombre_factura']}': {result}")
            codigo_conciliado = result.get("codigo_bd_conciliado")
            confianza = result.get("confianza", 0)

            if codigo_conciliado:
                candidato_elegido = next((c for c in original_item['candidatos_bd'] if c['codigo'] == codigo_conciliado), None)
                if candidato_elegido:
                    conciliados_por_ia.append({
                        "nombre_factura": original_item["nombre_factura"], 
                        "precio_factura": original_item["precio_factura"],
                        "codigo_bd": codigo_conciliado, 
                        "nombre_bd": candidato_elegido.get('nombre'), 
                        "precio_referencia": candidato_elegido.get('precio'),
                        "confianza": confianza
                    })
            else:
                logger.warning(f"Agno no pudo conciliar '{original_item['nombre_factura']}'.")
                fallidos_con_mejor_intento.append({
                    "nombre_factura": original_item["nombre_factura"],
                    "mejor_intento": original_item.get("mejor_intento")
                })
        
        logger.debug(f"--- FASE 3: FIN --- Agno concilió {len(conciliados_por_ia)} ítems.")
        return {"conciliados": conciliados_por_ia, "fallidos": fallidos_con_mejor_intento}

    def _annotate_with_surcharges(self, all_conciliated_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug(f"--- FASE 4: INICIO (Anotación) --- Calculando precios para {len(all_conciliated_items)} ítems.")
        annotated_items = []
        for item in all_conciliated_items:
            item_report = item.copy()
            precio_factura = item.get("precio_factura")
            precio_referencia = item.get("precio_referencia")
            item_report["monto_sobreprecio"] = 0.0
            item_report["porcentaje_sobreprecio"] = 0.0
            if precio_factura is not None and precio_referencia is not None and precio_referencia > 0:
                diferencia = precio_factura - precio_referencia
                item_report["monto_sobreprecio"] = round(diferencia, 2)
                item_report["porcentaje_sobreprecio"] = round((diferencia / precio_referencia) * 100, 2)
            annotated_items.append(item_report)
        logger.debug(f"--- FASE 4: FIN (Anotación) --- Anotación de precios completa.")
        return annotated_items

    async def generate_final_summary(
        self,
        total_unique_items: List[Dict[str, Any]],
        all_conciliated_items: List[Dict[str, Any]],
        unconciliated_items_with_details: List[Dict[str, Any]],
        surcharge_threshold: float
    ) -> str:
        logger.debug("--- FASE 5: INICIO --- Generando resumen ejecutivo.")
        
        annotated_conciliated_items = self._annotate_with_surcharges(all_conciliated_items)
        
        discrepancies = [
            item for item in annotated_conciliated_items 
            if item["porcentaje_sobreprecio"] > surcharge_threshold
        ]

        results_data = {
            "metricas": {
                "items_procesados": len(total_unique_items),
                "items_conciliados": len(all_conciliated_items),
                "items_con_sobreprecio": len(discrepancies)
            },
            "items_conciliados": annotated_conciliated_items,
            "items_no_conciliados": unconciliated_items_with_details
        }
        
        summary = await self.reporting_service.generate_summary(results_data)
        logger.debug("--- FASE 5: FIN --- Resumen ejecutivo generado.")
        return summary