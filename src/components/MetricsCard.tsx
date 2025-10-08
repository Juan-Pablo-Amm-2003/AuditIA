import { Card } from "./ui/card";
import { AlertCircle } from "lucide-react";

interface MetricsCardProps {
  title: string;
  value: number;
  type?: 'default' | 'alert';
}

export function MetricsCard({ title, value, type = 'default' }: MetricsCardProps) {
  const isAlert = type === 'alert' && value > 0;
  
  return (
    <Card className={`p-6 ${isAlert ? 'border-destructive bg-destructive/5' : ''}`}>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{title}</p>
          {isAlert && <AlertCircle className="w-5 h-5 text-destructive" />}
        </div>
        <p className={`text-3xl ${isAlert ? 'text-destructive' : 'text-foreground'}`}>
          {value}
        </p>
      </div>
    </Card>
  );
}
