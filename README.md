# API de Auditoría de Medicamentos v2.0

Este repositorio contiene el backend para la aplicación de auditoría de facturas médicas. La API está construida con FastAPI y utiliza un motor de IA para conciliar ítems de facturas con una base de datos de medicamentos.

## Puesta en Marcha del Proyecto (Setup)

Sigue estos pasos para levantar el entorno de desarrollo local.

### 1. Prerrequisitos

- Python 3.8 o superior.
- Git.

### 2. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

### 3. Configurar el Entorno Virtual

Es una buena práctica trabajar en un entorno virtual para aislar las dependencias del proyecto.

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en Windows
.\venv\Scripts\activate

# Activar en macOS/Linux
source venv/bin/activate
```

### 4. Instalar Dependencias

Instala todas las librerías necesarias desde el archivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

El proyecto necesita un archivo `.env` en la raíz para almacenar claves de API y configuraciones. Crea un archivo llamado `.env` y añade las siguientes variables:

```
# Clave de API de OpenAI para el asistente de IA
OPENAI_API_KEY="tu_clave_de_openai_aqui"

# Cadena de conexión para la base de datos SQL Server
DB_CONNECTION_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=tu_servidor;DATABASE=tu_base_de_datos;UID=tu_usuario;PWD=tu_contraseña"
```

### 6. Ejecutar la Aplicación

Una vez que todo está configurado, puedes iniciar el servidor.

```bash
uvicorn src.main:app --reload
```

El servidor estará disponible en `http://127.0.0.1:8000`.

---

## Documentación de la API para el Equipo de Front-End

### 1. La Documentación Automática (¡La forma más fácil!)

Gracias a que usamos **FastAPI**, el backend ya genera una documentación interactiva increíble. Una vez iniciado el servidor, visita estas URLs:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

En `/docs`, no solo podrás ver los endpoints, sino también **probarlos directamente desde el navegador**.

---

### 2. Resumen Técnico para Integración

### **URL Base:** `http://127.0.0.1:8000`

---

## Endpoints Principales

### **1. Auditar Factura desde Archivo (Método Recomendado) 📄**

- **Endpoint:** `POST /invoices/audit/upload_invoice`
- **Descripción:** Recibe un archivo de factura en formato JSON y devuelve un resumen de la auditoría en formato JSON.
- **Parámetros (Query String):**
    - `surcharge_threshold` (float, opcional, por defecto: `5.0`)
- **Cuerpo (Body):** `multipart/form-data` con un campo `file`.
- **Respuesta Exitosa (200 OK):**
    - **Content-Type:** `application/json`
    - **Cuerpo:** Un objeto JSON con el resumen.
      ```json
      {
        "summary": "*** RESUMEN DE AUDITORÍA ***\n... (texto completo del resumen) ..."
      }
      ```
- **Ejemplo de uso (cURL):**
  ```bash
  curl -X POST "http://127.0.0.1:8000/invoices/audit/upload_invoice?surcharge_threshold=5" \
       -F "file=@/ruta/a/tu/factura.json"
  ```

---

### **2. Auditar Factura desde Cuerpo JSON (Método Alternativo) 💻**

- **Endpoint:** `POST /invoices/audit/full_process`
- **Descripción:** Similar al anterior, pero recibe el objeto JSON directamente en el cuer.
- **Parámetros (Query String):**
    - `surcharge_threshold` (float, opcional, por defecto: `5.0`).
- **Cuerpo (Body):** `application/json` con el objeto de la factura.
- **Respuesta Exitosa (200 OK):**
    - **Content-Type:** `application/json`
    - **Cuerpo:** Un objeto JSON con el resumen.
      ```json
      {
        "summary": "*** RESUMEN DE AUDITORÍA ***\n... (texto completo del resumen) ..."
      }
      ```
- **Ejemplo de uso (cURL):**
  ```bash
  curl -X POST "http://127.0.0.1:8000/invoices/audit/full_process?surcharge_threshold=5" \
       -H "Content-Type: application/json" \
       -d @/ruta/a/tu/factura.json
  ```