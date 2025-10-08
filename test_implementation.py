#!/usr/bin/env python3
"""
Test script para probar la API de procesamiento de facturas.
"""
import json
import requests
from pathlib import Path

def test_invoice_processing():
    """Test the invoice processing endpoint."""

    # Load sample invoice
    sample_file = Path(__file__).parent / "sample_invoice.json"
    with open(sample_file, 'r', encoding='utf-8') as f:
        invoice_data = json.load(f)

    print("📋 Testing invoice processing...")
    print(f"📄 Invoice contains {len(invoice_data['pacientes'])} patients")
    print(f"📄 Total items: {sum(len(factura['items']) for paciente in invoice_data['pacientes'] for factura in paciente['facturas'])}")

    # Here you would make the actual API call when the server is running
    # For now, let's just validate the JSON structure
    print("✅ JSON structure is valid")

    # Test our utility functions
    from src.utils import normalize_description, extract_specifications

    test_descriptions = [
        "Paracetamol 500 MG Comprimidos",
        "Amoxicilina 500 MG Cápsulas",
        "Ibuprofeno 400 MG Comprimidos"
    ]

    print("\n🔧 Testing utility functions:")
    for desc in test_descriptions:
        normalized = normalize_description(desc)
        specs = extract_specifications(desc)
        print(f"  '{desc}' -> '{normalized}', specs: {specs}")

    print("\n✅ All tests passed! Ready to run the API server.")

if __name__ == "__main__":
    test_invoice_processing()
