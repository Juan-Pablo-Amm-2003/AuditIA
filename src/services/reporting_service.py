import os
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class ReportingService:
    # --- PROMPT COMPLETAMENTE RENOVADO ---
    PROMPT_ANALISTA_TEMPLATE = """
# ROL Y OBJETIVO
Eres un analista de auditoría médica experto. Tu tarea es recibir un objeto JSON con los resultados de una auditoría y redactar un resumen ejecutivo claro y accionable.

# REGLAS DE REDACCIÓN
- **Estructura del Reporte:** Sigue estrictamente estas tres secciones:
  1.  **Resumen General:** Presenta las métricas clave.
  2.  **Detalle de Ítems Conciliados:** Lista CADA ítem conciliado. Indica su "Hallazgo" (Precio Correcto o Sobreprecio) y la "Confianza del Match".
  3.  **Ítems No Conciliados:** Lista los ítems que requieren revisión manual, mostrando el "Mejor Intento" que hizo el sistema y su puntaje de similitud para justificar el fallo.
- **Tono:** Formal, objetivo y claro.

# EJEMPLOS

## Ejemplo 1: Auditoría CON Discrepancias
### Entrada JSON:
{{
  "metricas": {{"items_procesados": 12, "items_conciliados": 2, "items_con_sobreprecio": 1}},
  "items_conciliados": [
    {{
      "nombre_factura": "FADAMICINA 500 MG - COMP.", "precio_factura": 1500.75, "codigo_bd": "7795345001275", 
      "nombre_bd": "FADAMICINA 500 MG 16 COMPRIMIDOS", "precio_referencia": 1000.00,
      "monto_sobreprecio": 500.75, "porcentaje_sobreprecio": 50.07, "confianza": 95
    }},
    {{
      "nombre_factura": "AGUA DESTILADA X 10 ML.", "precio_factura": 3714.21, "codigo_bd": "56847", 
      "nombre_bd": "AGUA DESTILADA ESTERILIZADA RIGECIN 100 A. X 10ML", "precio_referencia": 6618.66,
      "monto_sobreprecio": -2904.45, "porcentaje_sobreprecio": -43.88, "confianza": 100
    }}
  ],
  "items_no_conciliados": [
      {{"nombre_factura": "BAREX UNIPEG - SOBRES", "mejor_intento": {{"nombre_bd": "BAREX 70 G 1 FRASCO", "score": 65}}}}
  ]
}}
### Salida Esperada:
**Resumen de Auditoría de Factura**

Se ha completado el proceso de auditoría.
- Ítems únicos procesados: 12
- Ítems conciliados con la base de datos: 2
- Ítems con sobreprecio detectado: 1

---
**Detalle de Ítems Conciliados**

1.  **FADAMICINA 500 MG - COMP.** (Código: 7795345001275)
    - Precio Facturado: $1500.75 / Precio de Referencia: $1000.00
    - **Hallazgo: Sobreprecio de $500.75 (50.07%)**
    - Confianza del Match: 95%

2.  **AGUA DESTILADA X 10 ML.** (Código: 56847)
    - Precio Facturado: $3714.21 / Precio de Referencia: $6618.66
    - Hallazgo: Precio correcto.
    - Confianza del Match: 100%

---
**Ítems No Conciliados (Requieren Revisión Manual)**
- **BAREX UNIPEG - SOBRES**
  - _Mejor intento en BD: "BAREX 70 G 1 FRASCO" (Similitud: 65%)_

## Ejemplo 2: Auditoría SIN Discrepancias
### Entrada JSON:
{{
  "metricas": {{"items_procesados": 12, "items_conciliados": 1, "items_con_sobreprecio": 0}},
  "items_conciliados": [
     {{
      "nombre_factura": "AGUA DESTILADA X 10 ML.", "precio_factura": 3714.21, "codigo_bd": "56847", 
      "nombre_bd": "AGUA DESTILADA ESTERILIZADA RIGECIN 100 A. X 10ML", "precio_referencia": 6618.66,
      "monto_sobreprecio": -2904.45, "porcentaje_sobreprecio": -43.88, "confianza": 100
    }}
  ],
  "items_no_conciliados": [
      {{"nombre_factura": "BACTROBAN 2% CREMA", "mejor_intento": {{"nombre_bd": "BACTROBAN POMADA", "score": 75}}}}
  ]
}}
### Salida Esperada:
**Resumen de Auditoría de Factura**

Se ha completado el proceso de auditoría.
- Ítems únicos procesados: 12
- Ítems conciliados con la base de datos: 1
- **Hallazgo Principal: No se detectaron medicamentos con sobreprecio.**

---
**Detalle de Ítems Conciliados**

1.  **AGUA DESTILADA X 10 ML.** (Código: 56847)
    - Precio Facturado: $3714.21 / Precio de Referencia: $6618.66
    - Hallazgo: Precio correcto.
    - Confianza del Match: 100%

---
**Ítems No Conciliados (Requieren Revisión Manual)**
- **BACTROBAN 2% CREMA**
  - _Mejor intento en BD: "BACTROBAN POMADA" (Similitud: 75%)_

# TAREA ACTUAL
Analiza el siguiente JSON de resultados y genera el reporte de auditoría correspondiente:
{json_de_resultados}
"""

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("API key de OpenAI no encontrada.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"

    async def generate_summary(self, results_data: Dict[str, Any]) -> str:
        json_de_resultados = json.dumps(results_data, ensure_ascii=False, indent=2)
        final_prompt = self.PROMPT_ANALISTA_TEMPLATE.format(
            json_de_resultados=json_de_resultados
        )
        logger.debug("Enviando datos al agente Analista para generar resumen.")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.1
            )
            summary = response.choices[0].message.content.strip()
            logger.debug(f"Resumen generado por el Analista: {summary}")
            return summary
        except Exception as e:
            logger.error(f"La generación de resumen con IA falló: {e}")
            return "Error: No se pudo generar el resumen de la auditoría."