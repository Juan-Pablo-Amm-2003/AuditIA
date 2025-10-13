import React, { useState } from 'react';
import axios from 'axios';
import { Toaster, toast } from 'react-hot-toast';
import FileUpload from './components/FileUpload';
import Spinner from './components/Spinner';
import ResultsDashboard from './components/ResultsDashboard';
import CorrectionModal from './components/CorrectionModal';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [surchargeThreshold, setSurchargeThreshold] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [auditResult, setAuditResult] = useState(null);
  const [itemToCorrect, setItemToCorrect] = useState(null);

  const handleAudit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setAuditResult(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `${API_URL}/invoices/audit/upload_invoice?surcharge_threshold=${surchargeThreshold}`,
        formData
      );
      setAuditResult(response.data);
      toast.success('Auditoría completada con éxito.');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Ocurrió un error inesperado.';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleNewAudit = () => {
    setAuditResult(null);
    setFile(null);
    setError(null);
  };

  // --- FUNCIÓN CORREGIDA ---
  const handleCorrectionSuccess = (correctedDataFromDB) => {
    if (!itemToCorrect || !auditResult) return;

    setItemToCorrect(null); // Cierra el modal

    // Actualizamos el estado de los resultados sin recargar la página
    setAuditResult(prevResult => {
      const newResult = JSON.parse(JSON.stringify(prevResult));
      const itemToMoveName = itemToCorrect.nombre_factura;

      // 1. Buscamos y removemos el ítem de la lista de "no conciliados"
      const itemIndex = newResult.items_no_conciliados.findIndex(
        item => item.nombre_factura === itemToMoveName
      );

      if (itemIndex > -1) {
        // Sacamos el ítem de la lista para moverlo
        const [itemToMove] = newResult.items_no_conciliados.splice(itemIndex, 1);

        // 2. Creamos el nuevo ítem conciliado con todos los datos
        const newItemConciliado = {
          ...itemToMove, // Arrastramos todos los datos originales (precio_factura, cantidad, etc.)
          codigo_bd: correctedDataFromDB.codigo,
          nombre_bd: correctedDataFromDB.nombre,
          precio_referencia: correctedDataFromDB.precio,
          confianza: 100, // La corrección manual tiene 100% de confianza
          monto_sobreprecio: 0, // Se puede recalcular o dejar en 0 por ahora
          porcentaje_sobreprecio: 0,
        };

        // 3. Lo agregamos a la lista de "conciliados"
        newResult.items_conciliados.push(newItemConciliado);
        
        // 4. Actualizamos las métricas
        newResult.metricas.items_conciliados += 1;
        newResult.metricas.items_no_conciliados -= 1;
      }

      return newResult;
    });

    toast.success('Ítem corregido y actualizado en la vista.');
  };

  return (
    <div className="bg-gray-900 text-white min-h-screen font-sans">
      <Toaster position="top-right" toastOptions={{ style: { background: '#333', color: '#fff' } }} />
      <aside className="fixed top-0 left-0 w-64 h-full bg-gray-800 p-5">
        <h1 className="text-2xl font-bold">AuditIA</h1>
      </aside>
      <main className="ml-64 p-10">
        {loading && (
          <div className="flex items-center justify-center h-full"><Spinner /></div>
        )}
        
        {!loading && auditResult && (
          <div>
            <ResultsDashboard result={auditResult} onCorrectItem={setItemToCorrect} />
            <button onClick={handleNewAudit} className="mt-8 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg">
              Auditar Nueva Factura
            </button>
          </div>
        )}

        {!loading && !auditResult && (
          <div>
            <h2 className="text-3xl font-semibold mb-6">Auditor de Facturas Médicas</h2>
            <FileUpload onFileSelect={setFile} file={file} />
            <div className="mt-4">
              <label htmlFor="threshold" className="block mb-2">Umbral de Sobreprecio (%)</label>
              <input 
                type="number" id="threshold" value={surchargeThreshold}
                onChange={(e) => setSurchargeThreshold(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-lg p-2 w-full max-w-xs"
              />
            </div>
            <button onClick={handleAudit} disabled={!file} className="mt-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg">
              Iniciar Auditoría
            </button>
            {error && <p className="mt-4 text-red-400">{error}</p>}
          </div>
        )}
      </main>
      <CorrectionModal 
        item={itemToCorrect}
        onClose={() => setItemToCorrect(null)}
        onCorrected={handleCorrectionSuccess}
      />
    </div>
  );
}

export default App;