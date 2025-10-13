import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud } from 'lucide-react';

const FileUpload = ({ onFileSelect, file }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json'],
    },
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed border-gray-600 rounded-lg p-10 text-center cursor-pointer transition-colors
        ${isDragActive ? 'bg-gray-700 border-blue-500' : 'bg-gray-800'}`}
    >
      <input {...getInputProps()} />
      <UploadCloud className="mx-auto h-12 w-12 text-gray-500" />
      {file ? (
        <p className="mt-4 text-green-400">Archivo seleccionado: {file.name}</p>
      ) : (
        <p className="mt-4 text-gray-400">
          {isDragActive
            ? 'Suelta el archivo aquí...'
            : 'Arrastra y suelta un archivo .json aquí, o haz clic para seleccionarlo'}
        </p>
      )}
    </div>
  );
};

export default FileUpload;
