from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv
from pyngrok import ngrok
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import bcrypt
import jwt
import os

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "clave_super_secreta")

# Modelos de datos
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    nombre: str

class PacienteResponse(BaseModel):
    nombre: str
    hora: str
    direccion: str
    estadoVisita: str

# Configuración de la conexión
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
        return psycopg2.connect(**conexion_params)
    except (Exception, Error) as error:
        print("Error al conectar a la base de datos:", error)
        return None

# Login
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
            if not bcrypt.checkpw(data.password.encode(), hashed_pw.encode()):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        else:
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

# Seguridad
security = HTTPBearer()

def get_current_enfermera_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return int(payload["id"])
    except (jwt.DecodeError, KeyError):
        raise HTTPException(status_code=401, detail="Token inválido")

# Endpoint de pacientes asignados (sin edad ni diagnóstico)
@app.get("/pacientes-asignados", response_model=List[PacienteResponse])
def obtener_pacientes_asignados(enfermera_id: int = Depends(get_current_enfermera_id)):
    conn = conectar_db()
    pacientes_respuesta = []

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                p.nombre,
                p.apellido,
                apv.hora,
                p.direccion,
                v.estado
            FROM visita v
            JOIN actividad_paciente_visita apv ON v.actividad_paciente_visita_id = apv.id
            JOIN paciente p ON apv.paciente_id = p.id
            WHERE v.enfermera_id = %s
        """, (enfermera_id,))

        rows = cur.fetchall()
        for row in rows:
            nombre, apellido, hora, direccion, estado_visita = row
            pacientes_respuesta.append(PacienteResponse(
                nombre=f"{nombre} {apellido}",
                hora=hora.strftime("%H:%M") if hora else "Sin hora",
                direccion=direccion or "Sin dirección",
                estadoVisita=estado_visita or "NO_INICIADA"
            ))

        return pacientes_respuesta

    except Exception as e:
        print("Error al obtener pacientes:", e)
        raise HTTPException(status_code=500, detail="Error interno al obtener pacientes")
    finally:
        cur.close()
        conn.close()

# Exponer con ngrok
public_url = ngrok.connect(8000, "http")
print(f"Web service accesible en: {public_url}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
