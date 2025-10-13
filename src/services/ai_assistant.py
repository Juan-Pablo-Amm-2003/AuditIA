import os
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIAssistant:
    # --- 1. PROMPT ACTUALIZADO PARA ENTENDER CANTIDADES ---
    PROMPT_TEMPLATE = """
# ROL Y OBJETIVO
Eres Agno, un asistente de IA experto en conciliar medicamentos. Tu tarea es analizar un "nombre_original_factura" y la "cantidad_consumida", y elegir el candidato más lógico de la lista.

# CONTEXTO Y REGLAS
- La "lista_de_candidatos" incluye un "score" de similitud de texto. Úsalo como una guía muy importante.
- **REGLA CLAVE:** Compara la "cantidad_consumida" con la información de empaque en los nombres de los candidatos (ej. "x 7", "x 20"). Elige el candidato cuyo empaque sea el más lógicamente compatible. Por ejemplo, si se consumieron 8 unidades, no puede ser una caja de 7; debe ser una de 20.
- Si NINGÚN candidato es una coincidencia clara y confiable, devuelve `null` en el código.
- Tu respuesta DEBE SER ÚNICAMENTE un objeto JSON con el código elegido y el score del candidato que elegiste.

# EJEMPLOS

## Ejemplo 1: Coincidencia por Cantidad (Caso BAREX)
### Entrada:
{{
  "nombre_original_factura": "BAREX UNIPEG - SOBRES",
  "cantidad_consumida": 10,
  "lista_de_candidatos": [
    {{"codigo": "111", "nombre": "BAREX UNIPEG sobres x 7", "score": 100}},
    {{"codigo": "222", "nombre": "BAREX UNIPEG sobres x 15", "score": 98}}
  ]
}}
### Salida Esperada:
{{
  "codigo_bd_conciliado": "222",
  "confianza": 98
}}

## Ejemplo 2: Sin Coincidencia Confiable
### Entrada:
{{
  "nombre_original_factura": "ANALGESICO FUERTE",
  "cantidad_consumida": 1,
  "lista_de_candidatos": [
    {{"codigo": "779", "nombre": "AGUA DESTILADA X 500 ML", "score": 30}}
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
  "cantidad_consumida": {cantidad_consumida},
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

    # --- 2. FUNCIÓN ACTUALIZADA PARA MANEJAR LA CANTIDAD ---
    async def conciliate_item(self, item_to_conciliate: Dict[str, Any]) -> Dict[str, Any]:
        nombre_factura = item_to_conciliate.get('nombre_factura')
        candidatos_bd = item_to_conciliate.get('candidatos_bd', [])
        # Se añade la cantidad total consumida
        cantidad_consumida = item_to_conciliate.get('cantidad_total', 1)

        if not nombre_factura:
            logger.error("No se encontró 'nombre_factura' en el ítem a conciliar.")
            return {"codigo_bd_conciliado": None, "confianza": 0}
        
        if not candidatos_bd:
            logger.warning(f"No se recibieron candidatos para '{nombre_factura}', no se puede conciliar.")
            return {"nombre_original_factura": nombre_factura, "codigo_bd_conciliado": None, "confianza": 0}

        candidatos_json_str = json.dumps(candidatos_bd, ensure_ascii=False, indent=2)
        final_prompt = self.PROMPT_TEMPLATE.format(
            nombre_factura=nombre_factura,
            cantidad_consumida=cantidad_consumida, # Se pasa la cantidad al prompt
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