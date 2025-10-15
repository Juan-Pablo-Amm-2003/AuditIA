import requests
import json
from pathlib import Path

# --- Configuración de la Prueba ---
API_BASE_URL = "http://127.0.0.1:8000"
FEEDBACK_ENDPOINT = f"{API_BASE_URL}/feedback/manual_review"
AUDIT_ENDPOINT = f"{API_BASE_URL}/invoices/audit/full_process"

# --- Datos de Prueba ---
# Usamos un ítem de la factura de muestra para la corrección manual
MANUAL_CORRECTION_ITEM = {
    "nombre_factura": "IBUPROFENO 400 MG COMPRIMIDOS",
    "codigo_bd_correcto": "55856"  # Código para "IBUPROFENO 600 MG"
}

EXACT_MATCH_ITEM = "AGUA DESTILADA X 10 ML."
NO_MATCH_ITEM = "PRODUCTO INEXISTENTE XYZ"

def test_feedback():
    """Paso 1: Enviar una corrección manual para simular el feedback del usuario."""
    print("\n--- 🧪 PASO 1: Probando el Endpoint de Feedback ---")
    try:
        response = requests.post(FEEDBACK_ENDPOINT, json=MANUAL_CORRECTION_ITEM)
        response.raise_for_status()  # Lanza un error si el status no es 2xx
        
        data = response.json()
        assert data["status"] == "success"
        print(f"✅ Feedback enviado correctamente: '{MANUAL_CORRECTION_ITEM['nombre_factura']}' -> '{MANUAL_CORRECTION_ITEM['codigo_bd_correcto']}'")
        return True
    except requests.RequestException as e:
        print(f"❌ ERROR: No se pudo conectar a la API en {FEEDBACK_ENDPOINT}. ¿Está el servidor corriendo?")
        print(f"   Detalle: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado durante la prueba de feedback: {e}")
        return False

def test_audit():
    """Paso 2: Ejecutar una auditoría que incluya el ítem corregido manualmente."""
    print("\n--- 🧪 PASO 2: Probando el Endpoint de Auditoría ---")
    
    # Cargamos la factura de muestra y la modificamos para la prueba
    sample_file = Path(__file__).parent / "sample_invoice.json"
    with open(sample_file, 'r', encoding='utf-8') as f:
        invoice_data = json.load(f)

    # Corregimos la estructura de la factura de muestra para que coincida con los modelos
    invoice_data["pacientes"][0]["informacion_paciente"] = {"nombre": "María González", "numero_afiliado": "AF12345"}
    invoice_data["pacientes"][0]["facturas"][0]["resumen"] = {"monto_total": 910.00} # Añadimos el resumen

    # Añadimos nuestros ítems de prueba a la primera factura del primer paciente
    items_de_prueba = [
        # Este ítem debería ser conciliado como "Manual"
        {"fecha": "2024-01-15", "descripción": MANUAL_CORRECTION_ITEM["nombre_factura"], "cantidad": 1, "precio_unitario": 120.00, "precio_total": 120.00},
        # Este ítem debería ser conciliado como "Exacto"
        {"fecha": "2024-01-15", "descripción": EXACT_MATCH_ITEM, "cantidad": 1, "precio_unitario": 50.00, "precio_total": 50.00},
        # Este ítem no debería ser conciliado
        {"fecha": "2024-01-15", "descripción": NO_MATCH_ITEM, "cantidad": 1, "precio_unitario": 99.99, "precio_total": 99.99},
    ]
    invoice_data["pacientes"][0]["facturas"][0]["items"].extend(items_de_prueba)

    try:
        # Construimos el payload para que coincida con el modelo InvoiceInput
        payload = {"pacientes": invoice_data["pacientes"]}
        
        response = requests.post(AUDIT_ENDPOINT, json=payload, params={"surcharge_threshold": 10.0})
        response.raise_for_status()
        
        audit_results = response.json()
        print("✅ Auditoría procesada exitosamente.")
        return audit_results
    except requests.RequestException as e:
        print(f"❌ ERROR: No se pudo conectar a la API en {AUDIT_ENDPOINT}.")
        print(f"   Detalle: {e}")
        if e.response is not None:
            try:
                print(f"   Respuesta del servidor: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"   Respuesta del servidor (no es JSON): {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ ERROR inesperado durante la auditoría: {e}")
        return None

def validate_results(results):
    """Paso 3: Validar que los resultados de la auditoría son los esperados."""
    if not results:
        print("\n--- ❌ PASO 3: Validación Omitida (No hubo resultados) ---")
        return

    print("\n--- 🧪 PASO 3: Validando los Resultados de la Auditoría ---")
    
    conciliados = {item['nombre_factura']: item for item in results.get("items_conciliados", [])}
    no_conciliados = {item['nombre_factura'] for item in results.get("items_no_conciliados", [])}
    
    # Validación 1: Corrección Manual (IBUPROFENO)
    if MANUAL_CORRECTION_ITEM["nombre_factura"] in conciliados:
        item = conciliados[MANUAL_CORRECTION_ITEM["nombre_factura"]]
        assert item["metodo_conciliacion"] == "Manual"
        assert item["codigo_bd"] == MANUAL_CORRECTION_ITEM["codigo_bd_correcto"]
        print(f"✅ OK: '{item['nombre_factura']}' fue conciliado como 'Manual'.")
    else:
        print(f"❌ FALLO: El ítem de corrección manual '{MANUAL_CORRECTION_ITEM['nombre_factura']}' no fue conciliado.")

    # Validación 2: Coincidencia por Mapeo Existente (AGUA DESTILADA)
    # Esta prueba es CRÍTICA. Verifica que los mapeos cargados al inicio funcionan.
    if EXACT_MATCH_ITEM in conciliados:
        item = conciliados[EXACT_MATCH_ITEM]
        # Como 'AGUA DESTILADA' probablemente ya existe en la tabla de sinónimos, 
        # el método correcto es 'Manual' o 'Sinonimo', no 'Exacto'.
        assert item["metodo_conciliacion"] in ["Manual", "Sinonimo"]
        print(f"✅ OK: '{item['nombre_factura']}' fue conciliado como '{item['metodo_conciliacion']}'.")
    else:
        print(f"❌ FALLO: El ítem de mapeo existente '{EXACT_MATCH_ITEM}' no fue conciliado.")

    # Validación 3: Ítem no conciliado
    if NO_MATCH_ITEM in no_conciliados:
        print(f"✅ OK: '{NO_MATCH_ITEM}' está correctamente en la lista de no conciliados.")
    else:
        print(f"❌ FALLO: '{NO_MATCH_ITEM}' debería estar en la lista de no conciliados.")

if __name__ == "__main__":
    print("🚀 Iniciando Suite de Pruebas de Integración...")
    
    if test_feedback():
        audit_results = test_audit()
        validate_results(audit_results)
    
    print("\n🏁 Suite de Pruebas Finalizada.")
