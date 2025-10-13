import logging
import time
from typing import List, Dict, Any, Tuple
from src.utils import clean_and_deduplicate

logger = logging.getLogger(__name__)

class InvoiceProcessor:
    def process_invoice(self, invoice_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float]:
        start_time = time.time()
        logger.info("Starting invoice processing...")
        try:
            items = []
            if "pacientes" in invoice_data:
                for paciente in invoice_data["pacientes"]:
                    if "facturas" in paciente:
                        for factura in paciente["facturas"]:
                            if "items" in factura:
                                items.extend(factura["items"])
            
            logger.info(f"Extracted {len(items)} total items from invoice.")
            aggregated_df = clean_and_deduplicate(items)
            processed_items = aggregated_df.to_dict('records')
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"Aggregated into {len(processed_items)} unique items in {processing_time:.2f}ms.")
            return processed_items, processing_time
        except Exception as e:
            logger.error(f"Error processing invoice: {e}", exc_info=True)
            raise ValueError(f"An unexpected error occurred: {e}")