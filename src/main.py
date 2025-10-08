from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import invoices, ai_assistant as ai_assistant_router

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Creación de la instancia de la aplicación
app = FastAPI(
    title="API de Auditoría de Medicamentos",
    description="Un sistema para auditar facturas de medicamentos usando IA.",
    version="2.0.0"
)

# Configuración de CORS
origins = [
    "http://localhost:3000",  # Origen de la aplicación de React
    "http://localhost:5173",  # Puerto común para Vite/React
    "http://localhost:8080",  # Otro puerto común
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

# Eventos de inicio y apagado
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Medicamentos API v2")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Medicamentos API v2")

# Inclusión de los routers de la aplicación
app.include_router(invoices.router)
app.include_router(ai_assistant_router.router)

# Endpoint raíz
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenido a la API de Auditoría de Medicamentos v2"}