import { Upload } from "lucide-react";
import React, { useState } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
}

export function FileUpload({ onFileSelect, selectedFile }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].name.endsWith('.json')) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-input')?.click()}
      className={`
        relative border-2 border-dashed rounded-lg p-16 text-center cursor-pointer
        transition-all duration-200
        ${isDragging 
          ? 'border-primary bg-primary/5' 
          : selectedFile 
            ? 'border-success bg-success/5'
            : 'border-border bg-card hover:border-primary/50 hover:bg-primary/5'
        }
      `}
    >
      <input
        id="file-input"
        type="file"
        accept=".json"
        onChange={handleFileInput}
        className="hidden"
        aria-label="File uploader"
      />
      
      <div className="flex flex-col items-center gap-4">
        <div className={`
          p-4 rounded-full
          ${selectedFile ? 'bg-success/10' : 'bg-muted'}
        `}>
          <Upload className={`w-8 h-8 ${selectedFile ? 'text-success' : 'text-muted-foreground'}`} />
        </div>
        
        {selectedFile ? (
          <div className="space-y-2">
            <p className="text-success">Archivo seleccionado: {selectedFile.name}</p>
            <p className="text-sm text-muted-foreground">Hacé clic en "Iniciar Auditoría" para continuar</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-foreground">Arrastrá tu factura .json aquí o hacé clic para seleccionar</p>
            <p className="text-sm text-muted-foreground">Solo archivos .json</p>
          </div>
        )}
      </div>
    </div>
  );
}