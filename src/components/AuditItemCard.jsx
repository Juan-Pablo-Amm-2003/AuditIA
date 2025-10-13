import { AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import { formatPrice } from '../utils';

const AuditItemCard = ({ item, type, onCorrect }) => {
  const typeStyles = {
    sobreprecio: { 
      bgColor: 'bg-red-900/50', 
      borderColor: 'border-red-700', 
      icon: <AlertTriangle className="h-6 w-6 text-red-400" /> 
    },
    conciliado: { 
      bgColor: 'bg-green-900/50', 
      borderColor: 'border-green-700', 
      icon: <CheckCircle className="h-6 w-6 text-green-400" /> 
    },
    'no-conciliado': { 
      bgColor: 'bg-yellow-900/50', 
      borderColor: 'border-yellow-700', 
      icon: <HelpCircle className="h-6 w-6 text-yellow-400" /> 
    },
  };

  const styles = typeStyles[type];

  return (
    <div className={`p-4 rounded-lg border ${styles.bgColor} ${styles.borderColor}`}>
      <div className="flex items-start justify-between">
        <p className="font-semibold text-lg flex-1 pr-4">{item.nombre_factura}</p>
        {styles.icon}
      </div>
      
      {type === 'sobreprecio' && (
        <div className="mt-3 text-sm space-y-1">
          <p className="text-gray-400">Código: <span className="font-semibold text-white">{item.codigo_bd}</span></p>
          <p>Cantidad Total: <span className="font-bold">{item.cantidad_total}</span></p>
          <p>Precio Facturado (Unitario): <span className="font-bold text-red-400">{formatPrice(item.precio_factura)}</span></p>
          <p>Precio de Referencia (Unitario): <span className="font-bold text-green-400">{formatPrice(item.precio_referencia)}</span></p>
          <p className="mt-1">Sobreprecio: <span className="font-bold text-red-400">{item.porcentaje_sobreprecio?.toFixed(2)}%</span></p>
        </div>
      )}

      {type === 'conciliado' && (
        <div className="mt-3 text-sm space-y-1">
          <p className="text-gray-400">Código: <span className="font-semibold text-white">{item.codigo_bd}</span></p>
          <p>Cantidad Total: <span className="font-bold">{item.cantidad_total}</span></p>
          <p>Precio Facturado (Unitario): <span className="font-bold">{formatPrice(item.precio_factura)}</span></p>
          <p>Precio de Referencia (Unitario): <span className="font-bold">{formatPrice(item.precio_referencia)}</span></p>
        </div>
      )}

      {type === 'no-conciliado' && (
        <div className="mt-3 text-sm">
          <p className="text-gray-400">Mejor intento: <span className="font-semibold text-yellow-400">{item.mejor_intento?.nombre_bd || 'N/A'}</span></p>
          <p className="text-gray-500">Score: {item.mejor_intento?.score?.toFixed(2) ?? 'N/A'}</p>
          <button 
            onClick={() => onCorrect(item)} 
            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-1 px-3 rounded-md text-xs"
          >
            Corregir
          </button>
        </div>
      )}
    </div>
  );
};

export default AuditItemCard;