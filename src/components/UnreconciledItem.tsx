import React from 'react';
import { AlertTriangle } from "lucide-react";

interface UnreconciledItemProps {
  name: string;
  bestMatch: string;
  similarity: number;
}

export function UnreconciledItem({ name, bestMatch, similarity }: UnreconciledItemProps) {
  return (
    <div className="p-4 border border-border rounded-lg bg-card space-y-2">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-warning mt-0.5 flex-shrink-0" />
        <div className="space-y-1 flex-1">
          <p className="text-foreground">{name}</p>
          <p className="text-sm italic text-muted-foreground">
            Mejor intento en BD: "{bestMatch}" (Similitud: {similarity}%)
          </p>
        </div>
      </div>
    </div>
  );
}