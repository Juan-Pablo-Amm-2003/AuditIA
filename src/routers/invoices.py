import logging
import json
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.models import InvoiceInput
from src.services.cleaning import InvoiceProcessor
from src.services.orchestration_service import OrchestrationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["Auditoría de Facturas"])

# --- LÓGICA CENTRAL REUTILIZABLE ---
async def _run_audit_logic(invoice_data: dict, surcharge_threshold: float) -> dict:
    try:
        InvoiceInput.model_validate(invoice_data)
        processor = InvoiceProcessor()
        unique_items, _ = processor.process_invoice(invoice_data)
        
        items_for_phase2 = [
            {"nombre_factura": i['descripción'], "precio_unitario": i['precio_unitario'], 
             "cantidad_total": i['cantidad'], "precio_total_agregado": i['precio_total']}
            for i in unique_items
        ]
        logger.info(f"Fase 1 completada: {len(items_for_phase2)} ítems únicos agregados.")
        
        orchestrator = OrchestrationService()
        phase2 = await orchestrator.process_items(items_for_phase2)
        conciliados_exactos = phase2.get('conciliados_exactos', [])
        pendientes = phase2.get('pendientes_para_agente', [])
        
        phase3 = {"conciliados": [], "fallidos": []}
        if pendientes:
            phase3 = await orchestrator.run_conciliation_phase(pendientes)
        
        all_conciliated = conciliados_exactos + phase3.get('conciliados', [])
        fallidos = phase3.get('fallidos', [])
        
        return orchestrator.generate_final_summary(
            total_items=items_for_phase2,
            all_conciliated=all_conciliated,
            fallidos=fallidos,
            threshold=surcharge_threshold
        )
    except Exception as e:
        logger.error(f"Error en la lógica de auditoría: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error inesperado.")

# --- ENDPOINT PARA SUBIR ARCHIVOS ---
@router.post("/audit/upload_invoice", response_class=JSONResponse)
async def upload_and_audit_invoice(
    surcharge_threshold: float = Query(5.0),
    file: UploadFile = File(...)
):
    logger.info("="*50)
    logger.info(f"INICIO DE AUDITORÍA (vía archivo). Umbral: {surcharge_threshold}%")
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="El archivo no es un JSON válido.")
    summary = await _run_audit_logic(data, surcharge_threshold)
    logger.info("FIN DE AUDITORÍA.")
    logger.info("="*50)
    return summary

# --- ENDPOINT PARA CUERPO JSON (RESTAURADO) ---
@router.post("/audit/full_process", response_class=JSONResponse)
async def run_full_audit_process(
    invoice_input: InvoiceInput = Body(...),
    surcharge_threshold: float = Query(5.0)
):
    logger.info("="*50)
    logger.info(f"INICIO DE AUDITORÍA (vía body). Umbral: {surcharge_threshold}%")
    summary = await _run_audit_logic(invoice_input.model_dump(), surcharge_threshold)
    logger.info("FIN DE AUDITORÍA.")
    logger.info("="*50)
    return summary