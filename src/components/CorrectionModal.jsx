import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { X } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

const CorrectionModal = ({ item, onClose, onCorrected }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (item) {
        // Reiniciar estado cuando se abre un nuevo modal
        setSearchTerm('');
        setSearchResults([]);
        setSelected(null);
    }
  }, [item]);

  useEffect(() => {
    if (searchTerm.length > 2) {
      const delayDebounceFn = setTimeout(async () => {
        try {
          const response = await axios.get(`${API_URL}/db/search_medicamentos?q=${searchTerm}`);
          setSearchResults(response.data);
        } catch (error) {
          console.error('Error searching for medicamentos:', error);
          toast.error('Error al buscar medicamentos.');
        }
      }, 300);
      return () => clearTimeout(delayDebounceFn);
    } else {
      setSearchResults([]);
    }
  }, [searchTerm]);

  const handleSave = async () => {
    if (!selected) {
      toast.error('Por favor, selecciona un medicamento de la lista.');
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/feedback/manual_review`, {
        nombre_factura: item.nombre_factura,
        codigo_bd_correcto: selected.codigo,
      });
      toast.success('Corrección enviada con éxito.');
      
      // --- CAMBIO CLAVE: Pasamos el objeto completo al App.jsx ---
      onCorrected(selected);
      
      onClose();
    } catch (error) {
      toast.error('Error al enviar la corrección.');
    } finally {
      setLoading(false);
    }
  };

  if (!item) return null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-lg relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-white">
          <X size={24} />
        </button>
        <h2 className="text-xl font-bold mb-4">Corregir Ítem No Conciliado</h2>
        <p className="mb-1">Ítem original: <span className="font-semibold text-yellow-400">{item.nombre_factura}</span></p>
        <p className="text-sm text-gray-400 mb-4">Mejor intento: {item.mejor_intento?.nombre_bd || 'N/A'} (Score: {item.mejor_intento?.score?.toFixed(2) ?? 'N/A'})</p>
        
        <input 
          type="text"
          placeholder="Buscar medicamento por nombre..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-2 rounded-md bg-gray-700 border border-gray-600 mb-4"
        />

        <div className="max-h-60 overflow-y-auto bg-gray-900 rounded-md p-2">
          {searchResults.map((med) => (
            <div 
              key={med.codigo}
              onClick={() => setSelected(med)}
              className={`p-2 cursor-pointer rounded-md ${selected?.codigo === med.codigo ? 'bg-blue-600' : 'hover:bg-gray-700'}`}>
              <p className="font-semibold">{med.nombre}</p>
              <p className="text-sm text-gray-400">Código: {med.codigo} - Precio: ${med.precio}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end gap-4">
          <button onClick={onClose} className="py-2 px-4 rounded-md bg-gray-600 hover:bg-gray-700">Cancelar</button>
          <button onClick={handleSave} disabled={!selected || loading} className="py-2 px-4 rounded-md bg-blue-600 hover:bg-blue-700 disabled:bg-gray-500">
            {loading ? 'Guardando...' : 'Guardar Corrección'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CorrectionModal;