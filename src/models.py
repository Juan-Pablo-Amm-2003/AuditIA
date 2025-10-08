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
    total_honorarios: Optional[float] = None
    total_gastos: Optional[float] = None
    total_a_cargo_mutual: Optional[float] = None
    total_a_cargo_afiliado: Optional[float] = None
    monto_total: Optional[float] = None

class Factura(BaseModel):
    tipo_factura: str
    codigo_documento: str
    fecha_emision: str
    departamento: Optional[str] = None
    numero_control: Optional[str] = None
    items: List[Item]
    resumen: Resumen

class InfoPaciente(BaseModel):
    nombre: str
    numero_afiliado: str
    edad: int
    numero_interno_paciente: Optional[str] = None
    numero_habitacion: str

class Paciente(BaseModel):
    informacion_paciente: InfoPaciente
    facturas: List[Factura]

class InvoiceInput(BaseModel):
    nombre_hospital: str
    proveedor_seguro: str
    pacientes: List[Paciente]