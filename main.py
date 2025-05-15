from fastapi import FastAPI, HTTPException  # type: ignore
from pydantic import BaseModel  # type: ignore
import psycopg2  # type: ignore
from psycopg2 import Error  # type: ignore
from dotenv import load_dotenv  # type: ignore
from pyngrok import ngrok # type: ignore
import bcrypt # type: ignore
import jwt  # type: ignore
import os

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "clave_super_secreta")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    nombre: str

# Configuración de la conexión a la base de datos
conexion_params = {
    "host": os.getenv("DB_HOST").replace("jdbc:postgresql://", "").split("/")[0],
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "neondb"),
    "user": os.getenv("DB_USER", "neondb_owner"),
    "password": os.getenv("DB_PASSWORD", "npg_1YOUFf6IhLZA"),
    "sslmode": "require" 
}

def conectar_db():
    try:
        conexion = psycopg2.connect(**conexion_params)
        return conexion
    except (Exception, Error) as error:
        print("Error al conectar a la base de datos:", error)
        return None

@app.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    conn = conectar_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, password FROM enfermera WHERE email = %s", (data.email,))
        result = cur.fetchone()
        if result is None:
            raise HTTPException(status_code=401, detail="Correo no encontrado")

        id_, nombre, hashed_pw = result
        if hashed_pw.startswith("$2a$"):
        # contraseña cifrada
            if not bcrypt.checkpw(data.password.encode(), hashed_pw.encode()):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        else:
        # contraseña en texto plano
            if data.password != hashed_pw:
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        token = jwt.encode({"id": id_, "nombre": nombre}, SECRET_KEY, algorithm="HS256")
        return {"token": token, "nombre": nombre}

    except Exception as e:
        print("Error en login:", e)
        raise HTTPException(status_code=500, detail="Error interno")

    finally:
        cur.close()
        conn.close()


public_url = ngrok.connect(8000, "http")
print(f"Web service accesible en: {public_url}")

if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)