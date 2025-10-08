import logging
import json
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from fastapi.responses import JSONResponse
from src.models import InvoiceInput
from src.services.cleaning import InvoiceProcessor
from src.services.orchestration_service import OrchestrationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["Auditoría de Facturas"])


async def _run_audit_logic(invoice_input: InvoiceInput, surcharge_threshold: float) -> dict:
    """
    Función auxiliar que contiene la lógica de auditoría principal.
    """
    try:
        logger.info(f"INICIO DE AUDITORÍA. Umbral: {surcharge_threshold}%")

        invoice_processor = InvoiceProcessor()
        unique_items_list, _ = invoice_processor.process_invoice(invoice_input.model_dump())
        
        unique_items_for_phase2 = [
            {"nombre_factura": i['descripción'], 
             "precio_factura": i['precio_unitario'],
             "cantidad_total": i['cantidad'], 
             "precio_total_agregado": i['precio_total']}
            for i in unique_items_list
        ]
        logger.info(f"Fase 1 completada: {len(unique_items_for_phase2)} ítems únicos agregados.")

        orchestrator = OrchestrationService()
        
        phase2_results = await orchestrator.process_items(unique_items_for_phase2)
        conciliados_exactos = phase2_results.get('conciliados_exactos', [])
        pendientes_para_agente = phase2_results.get('pendientes_para_agente', [])
        logger.info(f"Fase 2 completada: {len(conciliados_exactos)} exactos, {len(pendientes_para_agente)} pendientes.")

        phase3_results = {"conciliados": [], "fallidos": []}
        if pendientes_para_agente:
            phase3_results = await orchestrator.run_conciliation_phase(pendientes_para_agente)
        
        conciliados_por_ia = phase3_results.get('conciliados', [])
        fallidos_con_mejor_intento = phase3_results.get('fallidos', [])
        logger.info(f"Fase 3 completada: {len(conciliados_por_ia)} conciliados por IA.")

        all_conciliated_items = conciliados_exactos + conciliados_por_ia
        
        summary = await orchestrator.generate_final_summary(
            total_unique_items=unique_items_for_phase2,
            all_conciliated_items=all_conciliated_items,
            unconciliated_items_with_details=fallidos_con_mejor_intento,
            surcharge_threshold=surcharge_threshold
        )

        logger.info("FIN DE AUDITORÍA COMPLETA.")
        # Devolvemos un diccionario que FastAPI convertirá en JSON.
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Error en auditoría: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error inesperado.")


@router.post("/audit/full_process", tags=["Auditoría"])
async def run_full_audit_process(
    invoice_input: InvoiceInput = Body(...),
    surcharge_threshold: float = Query(5.0)
):
    """
    Ejecuta el proceso de auditoría completo a partir de un cuerpo JSON.
    """
    return await _run_audit_logic(invoice_input, surcharge_threshold)


@router.post("/audit/upload_invoice", tags=["Auditoría"])
async def upload_and_audit_invoice(
    surcharge_threshold: float = Query(5.0),
    file: UploadFile = File(...)
):
    """
    Ejecuta el proceso de auditoría completo a partir de un archivo JSON subido.
    """
    if file.content_type != 'application/json':
        raise HTTPException(status_code=400, detail="El archivo debe ser un JSON.")
    
    try:
        contents = await file.read()
        invoice_data = json.loads(contents)
        invoice_input = InvoiceInput(**invoice_data)
    except Exception as e:
        logger.error(f"Error al parsear el JSON: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"El JSON es inválido o no cumple la estructura: {e}")

    return await _run_audit_logic(invoice_input, surcharge_threshold)
