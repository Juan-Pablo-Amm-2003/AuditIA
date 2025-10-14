from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import invoices, ai_assistant as ai_assistant_router, feedback as feedback_router, database as database_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API de Auditoría de Medicamentos",
    description="Un sistema para auditar facturas de medicamentos usando IA.",
    version="2.0.0"
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "https://audit-ia-alpha.vercel.app",
    "https://audit-j67e9cawp-juan-pablo-amm-2003s-projects.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Medicamentos API v2")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Medicamentos API v2")

app.include_router(invoices.router)
app.include_router(ai_assistant_router.router)
app.include_router(feedback_router.router)
app.include_router(database_router.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenido a la API de Auditoría de Medicamentos v2"}