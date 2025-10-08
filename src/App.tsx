import React, { useState } from "react";
import { FileUpload } from "./components/FileUpload";
import { LoadingState } from "./components/LoadingState";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";

type ViewState = 'initial' | 'loading' | 'results';

export default function App() {
  const [viewState, setViewState] = useState<ViewState>('initial');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [threshold, setThreshold] = useState<number>(5);
  // Estado para guardar el resumen de texto que devuelve la API
  const [summaryText, setSummaryText] = useState<string>('');

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleStartAudit = async () => {
    if (!selectedFile) return;

    setViewState('loading');

    const formData = new FormData();
    formData.append("file", selectedFile);

    const apiUrl = new URL("http://127.0.0.1:8000/invoices/audit/upload_invoice");
    apiUrl.searchParams.append("surcharge_threshold", threshold.toString());

    try {
      const response = await fetch(apiUrl.toString(), {
        method: "POST",
        body: formData,
        headers: {
          "Accept": "application/json",
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error del servidor: ${response.status} - ${errorText || response.statusText}`);
      }

      // Extraemos la propiedad 'summary' de la respuesta JSON
      const results = await response.json();
      setSummaryText(results.summary);
      setViewState('results');

    } catch (error) {
      console.error("Error al auditar la factura:", error);
      alert(`No se pudo completar la auditoría: ${error instanceof Error ? error.message : String(error)}`);
      handleNewAudit();
    }
  };

  const handleNewAudit = () => {
    setViewState('initial');
    setSelectedFile(null);
    // Limpiamos el estado del resumen
    setSummaryText('');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8 text-center">
          <h1 className="text-foreground mb-2">AuditIA: Auditor de Facturas Médicas</h1>
          <p className="text-muted-foreground">
            Sistema inteligente de auditoría médica basado en IA
          </p>
        </div>

        {viewState === 'initial' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <FileUpload 
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
            />

            <div className="space-y-2">
              <Label htmlFor="threshold">Umbral de Sobreprecio (%)</Label>
              <Input
                id="threshold"
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                min="0"
                max="100"
                step="0.1"
                className="max-w-xs"
              />
              <p className="text-sm text-muted-foreground">
                Se marcarán como sobreprecio las diferencias superiores a este porcentaje
              </p>
            </div>

            <Button
              onClick={handleStartAudit}
              disabled={!selectedFile}
              className="w-full h-12 bg-primary hover:bg-primary/90"
              size="lg"
            >
              Iniciar Auditoría
            </Button>
          </div>
        )}

        {viewState === 'loading' && <LoadingState />}

        {/* --- SECCIÓN DE RESULTADOS MODIFICADA --- */}
        {viewState === 'results' && summaryText && (
          <div className="space-y-8">
            <div className="flex justify-end">
              <Button
                onClick={handleNewAudit}
                variant="outline"
                className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
              >
                Auditar Nueva Factura
              </Button>
            </div>

            {/* Contenedor para mostrar el resumen */}
            <div className="p-6 border border-border rounded-lg bg-card">
              <h2 className="text-xl font-semibold text-foreground mb-4">Resumen de la Auditoría</h2>
              {/* Usamos <pre> para respetar los saltos de línea y espacios del texto */}
              <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-sans">
                {summaryText}
              </pre>
            </div>

            <div className="pt-6 border-t border-border">
              <Button
                onClick={handleNewAudit}
                className="w-full h-12 bg-primary hover:bg-primary/90"
                size="lg"
              >
                Auditar Nueva Factura
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}