const MetricCard = ({ label, value, isAlert = false }) => {
  const formatValue = (label, val) => {
    if (label.toLowerCase().includes('ahorro') || label.toLowerCase().includes('monto')) {
      return `$${Number(val).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return val;
  };

  return (
    <div 
      className={`p-4 rounded-lg shadow-md ${isAlert ? 'bg-red-800/50' : 'bg-gray-800'}`}>
      <h3 className="text-sm font-medium text-gray-400">{label}</h3>
      <p className="mt-1 text-3xl font-semibold">{formatValue(label, value)}</p>
    </div>
  );
};

export default MetricCard;
