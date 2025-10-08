import pyodbc
import pandas as pd
from dotenv import load_dotenv
import os

# Carga la cadena de conexión desde el archivo .env
load_dotenv()
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")
CSV_FILE_PATH = "data/medicamentos.csv" # Asumiendo que guardaste el csv en una carpeta 'data'

def seed_database():
    if not DB_CONNECTION_STRING:
        print("Error: La variable DB_CONNECTION_STRING no está configurada en el archivo .env")
        return

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        print("Conexión exitosa. Empezando el proceso de carga...")

        df = pd.read_csv(CSV_FILE_PATH, dtype=str, encoding='latin-1') # latin-1 es común en exports de SQL Server

        cursor.execute("IF OBJECT_ID('dbo.medicamentos', 'U') IS NOT NULL DELETE FROM dbo.medicamentos")
        print("Tabla 'medicamentos' limpiada.")

        print(f"Insertando {len(df)} registros...")
        for index, row in df.iterrows():
            cursor.execute(
                """
                INSERT INTO dbo.medicamentos (codigo, troquel, nombre, precio, presentacion, laboratorio)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                row.get('codigo'),
                row.get('troquel'),
                row.get('nombre'),
                float(row.get('precio')) if pd.notna(row.get('precio')) else None,
                row.get('presentacion'),
                row.get('laboratorio')
            )

        conn.commit()
        print("¡Proceso de carga completado exitosamente!")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    seed_database()