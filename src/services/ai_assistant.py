import os
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIAssistant:
    PROMPT_TEMPLATE = """
# ROL Y OBJETIVO
Eres Agno, un asistente de IA experto en la conciliación de nombres de medicamentos. Tu única tarea es analizar un "nombre_original_factura" y elegir el "codigo_bd" del candidato más probable de la lista.

# CONTEXTO Y REGLAS
- El "nombre_original_factura" puede tener abreviaturas, errores o información parcial.
- La "lista_de_candidatos" ahora incluye un "score" (0-100) de similitud de texto. Usa este puntaje como una guía muy importante. Un score alto (>85) es una señal muy fuerte de que el candidato es correcto.
- Analiza el nombre, la dosis, la forma farmacéutica y el laboratorio para tomar tu decisión final.
- Si NINGÚN candidato es una coincidencia clara y confiable, devuelve `null` en el código.
- Tu respuesta DEBE SER ÚNICAMENTE un objeto JSON con el código elegido y el score del candidato que elegiste.

# EJEMPLOS

## Ejemplo 1: Coincidencia Clara
### Entrada:
{{
  "nombre_original_factura": "DELTISONA B-8 MG .- COMP.",
  "lista_de_candidatos": [
    {{"codigo_bd": "7795345001275", "nombre_bd": "BAGO DELTISONA B 8 MG 20 COMPRIMIDOS", "score": 95}},
    {{"codigo_bd": "7795345001237", "nombre_bd": "BAGO DELTISONA 40 MG 20 COMPRIMIDOS", "score": 70}}
  ]
}}
### Salida Esperada:
{{
  "codigo_bd_conciliado": "7795345001275",
  "confianza": 95
}}

## Ejemplo 2: Sin Coincidencia Confiable
### Entrada:
{{
  "nombre_original_factura": "ANALGESICO FUERTE",
  "lista_de_candidatos": [
    {{"codigo_bd": "7790010004514", "nombre_bd": "AGUA DESTILADA X 500 ML", "score": 30}},
    {{"codigo_bd": "7790010004545", "nombre_bd": "ALCOHOL ETILICO 500 ML", "score": 25}}
  ]
}}
### Salida Esperada:
{{
  "codigo_bd_conciliado": null,
  "confianza": 0
}}

# TAREA ACTUAL
Realiza la conciliación para la siguiente entrada:
### Entrada:
{{
  "nombre_original_factura": "{nombre_factura}",
  "lista_de_candidatos": {candidatos_json_str}
}}
### Salida Esperada:
"""

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("API key de OpenAI no encontrada.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"

    async def conciliate_item(self, item_to_conciliate: Dict[str, Any]) -> Dict[str, Any]:
        nombre_factura = item_to_conciliate.get('nombre_factura')
        candidatos_bd = item_to_conciliate.get('candidatos_bd', [])

        if not nombre_factura:
            logger.error("No se encontró 'nombre_factura' en el ítem a conciliar.")
            return {"codigo_bd_conciliado": None, "confianza": 0}
        
        if not candidatos_bd:
            logger.warning(f"No se recibieron candidatos para '{nombre_factura}', no se puede conciliar.")
            return {"nombre_original_factura": nombre_factura, "codigo_bd_conciliado": None, "confianza": 0}

        candidatos_json_str = json.dumps(candidatos_bd, ensure_ascii=False, indent=2)
        final_prompt = self.PROMPT_TEMPLATE.format(
            nombre_factura=nombre_factura,
            candidatos_json_str=candidatos_json_str
        )
        
        logger.debug(f"Enviando a OpenAI para '{nombre_factura}'.")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": final_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            ai_response_str = response.choices[0].message.content
            if not ai_response_str:
                raise ValueError("La respuesta de la API de OpenAI estaba vacía.")
            
            logger.debug(f"Respuesta de OpenAI para '{nombre_factura}': {ai_response_str}")
            
            response_data = json.loads(ai_response_str)
            response_data["nombre_original_factura"] = nombre_factura
            return response_data

        except Exception as e:
            logger.error(f"La conciliación con IA falló para '{nombre_factura}': {e}")
            return {"nombre_original_factura": nombre_factura, "codigo_bd_conciliado": None, "confianza": 0}