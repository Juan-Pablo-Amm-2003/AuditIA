import React from 'react';
import MetricCard from './MetricCard';
import AuditItemCard from './AuditItemCard';

const ResultsDashboard = ({ result, onCorrectItem }) => {
  // Asignamos valores por defecto a cada propiedad para evitar errores.
  const { 
    metricas = {}, 
    items_con_sobreprecio = [], 
    items_conciliados = [], 
    items_no_conciliados = [] 
  } = result || {};

  // Filtramos para obtener solo los conciliados sin sobreprecio.
  const sobreprecioNombres = new Set(items_con_sobreprecio.map(item => item.nombre_factura));
  const conciliadosSinSobreprecio = items_conciliados.filter(item => !sobreprecioNombres.has(item.nombre_factura));

  return (
    <div>
      <h2 className="text-3xl font-semibold mb-6">Resultados de la Auditoría</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard label="Ahorro Potencial" value={metricas.ahorro_potencial} />
        <MetricCard label="Monto Total Facturado" value={metricas.monto_total_facturado} />
        <MetricCard 
          label="Ítems con Sobreprecio" 
          value={metricas.items_con_sobreprecio} 
          isAlert={(metricas.items_con_sobreprecio ?? 0) > 0} 
        />
        <MetricCard label="Ítems no Conciliados" value={metricas.items_no_conciliados} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <section>
          <h3 className="text-xl font-semibold mb-4 text-red-400">Ítems con Sobreprecio</h3>
          <div className="space-y-4">
            {items_con_sobreprecio.length > 0 ? (
              items_con_sobreprecio.map(item => <AuditItemCard key={item.codigo_bd || item.nombre_factura} item={item} type="sobreprecio" />)
            ) : (
              <p className="text-gray-500">No se encontraron ítems con sobreprecio.</p>
            )}
          </div>
        </section>

        <section>
          <h3 className="text-xl font-semibold mb-4 text-green-400">Ítems con Precio Correcto</h3>
          <div className="space-y-4">
            {conciliadosSinSobreprecio.length > 0 ? (
              conciliadosSinSobreprecio.map(item => <AuditItemCard key={item.codigo_bd || item.nombre_factura} item={item} type="conciliado" />)
            ) : (
              <p className="text-gray-500">No se encontraron otros ítems conciliados.</p>
            )}
          </div>
        </section>

        <section>
          <h3 className="text-xl font-semibold mb-4 text-yellow-400">Ítems No Conciliados</h3>
          <div className="space-y-4">
            {items_no_conciliados.length > 0 ? (
              items_no_conciliados.map(item => 
                <AuditItemCard key={item.nombre_factura} item={item} type="no-conciliado" onCorrect={onCorrectItem} />
              )
            ) : (
              <p className="text-gray-500">¡Todos los ítems fueron conciliados!</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default ResultsDashboard;