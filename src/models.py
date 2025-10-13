from pydantic import BaseModel
from typing import List, Optional

class Item(BaseModel):
    fecha: str
    descripción: str
    cantidad: int
    precio_unitario: float
    precio_total: float
    notas: Optional[str] = None

class Resumen(BaseModel):
    monto_total: Optional[float] = None

class Factura(BaseModel):
    items: List[Item]
    resumen: Resumen

class InfoPaciente(BaseModel):
    nombre: str
    numero_afiliado: str

class Paciente(BaseModel):
    informacion_paciente: InfoPaciente
    facturas: List[Factura]

class InvoiceInput(BaseModel):
    pacientes: List[Paciente]