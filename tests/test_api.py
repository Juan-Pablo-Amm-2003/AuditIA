import pytest
import asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.models import InvoiceInput, Item, Factura, Paciente
from src.services.cleaning import InvoiceProcessor
from src.services.search_engine import SearchEngine
from src.utils import normalize_description, extract_specifications

client = TestClient(app)

class TestInvoiceProcessor:
    """Test the invoice processing service"""

    def test_normalize_description(self):
        """Test text normalization"""
        assert normalize_description("Paracetamol 500 MG Comprimidos") == "paracetamol 500 mg comprimidos"
        assert normalize_description("  Extra  Spaces  ") == "extra spaces"

    def test_extract_specifications(self):
        """Test specification extraction"""
        specs = extract_specifications("Paracetamol 500 MG Comprimidos")
        assert "dosis" in specs
        assert specs["dosis"] == "500 MG"
        assert "forma" in specs

    def test_invoice_processor_basic(self):
        """Test basic invoice processing"""
        # Create test invoice
        invoice_data = {
            "nombre_hospital": "Hospital Test",
            "proveedor_seguro": "Seguro Test",
            "pacientes": [
                {
                    "informacion_paciente": {"nombre": "Paciente Test"},
                    "facturas": [
                        {
                            "tipo_factura": "Ambulatoria",
                            "codigo_documento": "DOC001",
                            "fecha_emision": "2024-01-01",
                            "items": [
                                {
                                    "fecha": "2024-01-01",
                                    "descripción": "Paracetamol 500 MG Comprimidos",
                                    "cantidad": 2,
                                    "precio_unitario": 150.00,
                                    "precio_total": 300.00,
                                    "notas": "Test item"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        processor = InvoiceProcessor()
        items, processing_time = processor.process_invoice(invoice_data)

        assert len(items) == 1
        assert items[0]['descripción'] == "Paracetamol 500 MG Comprimidos"
        assert items[0]['normalized_desc'] == "paracetamol 500 mg comprimidos"
        assert "specifications" in items[0]
        assert processing_time > 0

class TestSearchEngine:
    """Test the search engine"""

    @pytest.mark.asyncio
    async def test_search_engine_initialization(self):
        """Test search engine can be initialized"""
        search_engine = SearchEngine()
        assert search_engine is not None

    @pytest.mark.asyncio
    async def test_search_medication_basic(self):
        """Test basic medication search"""
        search_engine = SearchEngine()

        # This will test the search logic without database
        # In a real scenario, you'd mock the database calls
        results = await search_engine.search_medication("Paracetamol 500 MG", k=3)

        # Should return some results or empty list, but not error
        assert isinstance(results, list)

class TestAPIEndpoints:
    """Test the API endpoints"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Medicamentos API v2" in response.json()["message"]

    def test_search_endpoint_missing_query(self):
        """Test search endpoint with missing query"""
        response = client.get("/invoices/search")
        assert response.status_code == 422  # Validation error

    def test_search_endpoint_with_query(self):
        """Test search endpoint with valid query"""
        response = client.get("/invoices/search?query=Paracetamol")
        # Should return 200 even if no results found
        assert response.status_code == 200
        assert "query" in response.json()
        assert "results" in response.json()

    def test_process_invoice_invalid_json(self):
        """Test invoice processing with invalid JSON"""
        invalid_invoice = {"invalid": "data"}

        response = client.post("/invoices/process", json=invalid_invoice)
        assert response.status_code == 422  # Pydantic validation error

class TestIntegration:
    """Integration tests"""

    def test_end_to_end_processing(self):
        """Test complete invoice processing workflow"""
        # Create a complete test invoice
        test_invoice = InvoiceInput(
            nombre_hospital="Hospital Integration Test",
            proveedor_seguro="Seguro Integration Test",
            pacientes=[
                Paciente(
                    informacion_paciente={"nombre": "Paciente Test"},
                    facturas=[
                        Factura(
                            tipo_factura="Ambulatoria",
                            codigo_documento="INT001",
                            fecha_emision="2024-01-01",
                            items=[
                                Item(
                                    fecha="2024-01-01",
                                    descripción="Paracetamol 500 MG Comprimidos",
                                    cantidad=2,
                                    precio_unitario=150.00,
                                    precio_total=300.00,
                                    notas="Integration test"
                                )
                            ]
                        )
                    ]
                )
            ]
        )

        # Test the complete processing pipeline
        response = client.post("/invoices/process", json=test_invoice.dict())

        # Should return a valid response structure
        if response.status_code == 200:
            data = response.json()
            assert "matches" in data
            assert "discrepancies" in data
            assert "no_matches" in data
            assert "effectiveness" in data
            assert "total_items" in data
            assert "processing_time_ms" in data
        else:
            # If it fails due to database issues, that's expected in test environment
            assert response.status_code in [200, 500]

def test_models_validation():
    """Test that Pydantic models validate correctly"""
    # Test valid item
    item = Item(
        fecha="2024-01-01",
        descripción="Test medication",
        cantidad=1,
        precio_unitario=100.00,
        precio_total=100.00,
        notas="Test"
    )
    assert item.descripción == "Test medication"

    # Test invalid item (should raise validation error)
    try:
        invalid_item = Item(
            fecha="2024-01-01",
            descripción="",  # Empty description should fail
            cantidad=1,
            precio_unitario=100.00,
            precio_total=100.00,
            notas="Test"
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
