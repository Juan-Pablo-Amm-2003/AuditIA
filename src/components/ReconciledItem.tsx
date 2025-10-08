import { Card } from "./ui/card";
import { Badge } from "./ui/badge";

interface ReconciledItemProps {
  name: string;
  code: string;
  invoicedPrice: number;
  referencePrice: number;
  overpricing: number | null;
  overpricingPercent: number | null;
  confidence: number;
}

export function ReconciledItem({
  name,
  code,
  invoicedPrice,
  referencePrice,
  overpricing,
  overpricingPercent,
  confidence
}: ReconciledItemProps) {
  const hasOverpricing = overpricing !== null && overpricing > 0;

  const getConfidenceBadgeColor = (conf: number) => {
    if (conf >= 90) return 'bg-success text-success-foreground';
    if (conf >= 75) return 'bg-warning text-warning-foreground';
    return 'bg-muted text-muted-foreground';
  };

  return (
    <Card className="p-6 space-y-4">
      <div className="space-y-1">
        <h4 className="text-foreground">{name}</h4>
        <p className="text-sm text-muted-foreground">Código: {code}</p>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Precio Facturado:</span>
          <span className="text-foreground">${invoicedPrice.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Precio de Referencia:</span>
          <span className="text-foreground">${referencePrice.toFixed(2)}</span>
        </div>
      </div>

      <div className="pt-3 border-t border-border space-y-3">
        {hasOverpricing ? (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-destructive">
              <span className="font-medium">Hallazgo:</span> Sobreprecio de ${overpricing?.toFixed(2)} ({overpricingPercent?.toFixed(2)}%)
            </p>
          </div>
        ) : (
          <div className="p-3 bg-success/10 border border-success/20 rounded-md">
            <p className="text-success">
              <span className="font-medium">Hallazgo:</span> Precio correcto
            </p>
          </div>
        )}

        <div className="flex items-center gap-2">
          <Badge className={getConfidenceBadgeColor(confidence)}>
            Confianza: {confidence}%
          </Badge>
        </div>
      </div>
    </Card>
  );
}
