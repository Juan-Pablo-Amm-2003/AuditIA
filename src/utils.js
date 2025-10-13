// src/utils.js

/**
 * Formatea un número como moneda argentina.
 * Maneja de forma segura valores nulos o no numéricos.
 * @param {number | null | undefined} price - El precio a formatear.
 * @returns {string} - El precio formateado o un texto alternativo.
 */
export const formatPrice = (price) => {
    if (price === null || price === undefined || isNaN(Number(price))) {
      return '$ (sin dato)';
    }
    return `$${Number(price).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  
  /**
   * Formatea un valor numérico para las tarjetas de métricas.
   * @param {string} label - La etiqueta de la métrica.
   * @param {number | null | undefined} value - El valor a formatear.
   * @returns {string} - El valor formateado.
   */
  export const formatMetricValue = (label, value) => {
    const numValue = value ?? 0;
    if (label.toLowerCase().includes('ahorro') || label.toLowerCase().includes('monto')) {
      return formatPrice(numValue);
    }
    return numValue.toString();
  };