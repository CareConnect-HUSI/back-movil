from fastapi import FastAPI, HTTPException  # type: ignore
from pydantic import BaseModel  # type: ignore
import psycopg2  # type: ignore
from psycopg2 import Error  # type: ignore
from dotenv import load_dotenv  # type: ignore
from pyngrok import ngrok # type: ignore
import os

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configuración de la conexión a la base de datos
conexion_params = {
    "host": os.getenv("DB_HOST", "tu-host.neon.tech"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "nombre_base_datos"),
    "user": os.getenv("DB_USER", "tu_usuario"),
    "password": os.getenv("DB_PASSWORD", "tu_contraseña"),
    "sslmode": "require" 
}

def conectar_db():
    try:
        conexion = psycopg2.connect(**conexion_params)
        return conexion
    except (Exception, Error) as error:
        print("Error al conectar a la base de datos:", error)
        return None

# Modelo para la respuesta (opcional, ajusta según tus necesidades)
class Item(BaseModel):
    id: int
    nombre: str  # Ajusta los campos según tu tabla

@app.get("/datos", response_model=list[Item])
async def obtener_datos():
    conexion = conectar_db()
    if conexion is None:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

    try:
        cursor = conexion.cursor()
        # Consulta de ejemplo (ajusta según tu tabla)
        cursor.execute("SELECT id, nombre FROM enfermera")
        resultados = cursor.fetchall()

        # Convertir resultados a lista de diccionarios
        datos = [{"id": fila[0], "nombre": fila[1]} for fila in resultados]

        return datos

    except (Exception, Error) as error:
        print("Error al ejecutar la consulta:", error)
        raise HTTPException(status_code=500, detail="Error al obtener los datos")

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


public_url = ngrok.connect(8000, "http")
print(f"Web service accesible en: {public_url}")

if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)