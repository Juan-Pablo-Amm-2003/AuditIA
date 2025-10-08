from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from src.services.ai_assistant import AIAssistant

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
ai_assistant_service = AIAssistant()

@router.post("/conciliate")
async def conciliate_item_endpoint(item_to_conciliate: Dict[str, Any]):
    """
    Endpoint de prueba para la Fase 3: Concilia un ítem usando el agente Agno.
    """
    try:
        return await ai_assistant_service.conciliate_item(item_to_conciliate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la conciliación: {e}")