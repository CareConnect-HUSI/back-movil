from fastapi import FastAPI, HTTPException, Depends #type: ignore
from pydantic import BaseModel #type: ignore
import psycopg2 #type: ignore
from psycopg2 import Error #type: ignore
from dotenv import load_dotenv #type: ignore
from pyngrok import ngrok #type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials #type: ignore
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field #type: ignore
import bcrypt #type: ignore 
import jwt #type: ignore
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
    visita_id: int = Field(..., alias="visitaId")
    nombre: str
    hora: str
    direccion: str
    telefono: str
    estadoVisita: str

class HorasVisitaRequest(BaseModel):
    llegada: str
    salida: str

class ProcedimientoResponse(BaseModel):
    nombre: str

class InsumoResponse(BaseModel):
    codigo: int
    insumo: str

class InsumoConsumidoRequest(BaseModel):
    codigo: int  # este será el instalacion_insumo_id
    cantidad: int


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
                v.id, 
                p.nombre,
                p.apellido,
                apv.hora,
                p.direccion,
                p.telefono,    
                v.estado    
            FROM visita v
            JOIN actividad_paciente_visita apv ON v.actividad_paciente_visita_id = apv.id
            JOIN paciente p ON apv.paciente_id = p.id
            WHERE v.enfermera_id = %s
        """, (enfermera_id,))

        rows = cur.fetchall()
        for row in rows:
            visita_id, nombre, apellido, hora, direccion, telefono, estado_visita = row
            pacientes_respuesta.append(PacienteResponse(
                visitaId = visita_id,
                nombre=f"{nombre} {apellido}",
                hora=hora.strftime("%H:%M") if hora else "Sin hora",
                direccion=direccion or "Sin dirección",
                telefono=telefono or "Sin teléfono",
                estadoVisita=estado_visita or "NO_INICIADA"
            ))

        return pacientes_respuesta

    except Exception as e:
        print("Error al obtener pacientes:", e)
        raise HTTPException(status_code=500, detail="Error interno al obtener pacientes")
    finally:
        cur.close()
        conn.close()

@app.post("/visita/{id}/hora")
def registrar_horas_visita(id: int, body: HorasVisitaRequest):
    print(">>> POST recibido:", id, body)
    conn = conectar_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE visita
            SET hora_inicio_ejecutada = %s, hora_fin_ejecutada = %s
            WHERE id = %s
        """, (body.llegada, body.salida, id))
        conn.commit()
        return {"mensaje": "Horas actualizadas"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/visita/{visita_id}/procedimientos", response_model=List[ProcedimientoResponse])
def obtener_procedimientos(visita_id: int, token: HTTPAuthorizationCredentials = Depends(security)):
    conn = conectar_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.name
            FROM actividad_paciente_visita apv
            JOIN actividad a ON apv.actividad_id = a.id
            JOIN visita v ON v.actividad_paciente_visita_id = apv.id
            WHERE v.id = %s
        """, (visita_id,))
        rows = cur.fetchall()
        return [ProcedimientoResponse(nombre=row[0]) for row in rows]
    except Exception as e:
        print("Error al obtener procedimientos:", e)
        raise HTTPException(status_code=500, detail="Error interno al obtener procedimientos")
    finally:
        cur.close()
        conn.close()

@app.get("/visita/{visita_id}/insumos", response_model=List[InsumoResponse])
def obtener_insumos_por_visita(visita_id: int):
    conn = conectar_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT iip.id, a.name AS insumo
            FROM visita v
            JOIN actividad_paciente_visita apv ON v.actividad_paciente_visita_id = apv.id
            JOIN paciente p ON apv.paciente_id = p.id
            JOIN instalacion_insumos_paciente iip ON p.id = iip.paciente_id
            JOIN actividad a ON iip.actividad_id = a.id
            WHERE v.id = %s
        """, (visita_id,))
        rows = cur.fetchall()
        return [InsumoResponse(codigo=row[0], insumo=row[1]) for row in rows]
    except Exception as e:
        print("Error al obtener insumos:", e)
        raise HTTPException(status_code=500, detail="Error interno al obtener insumos")
    finally:
        cur.close()
        conn.close()

@app.post("/visita/{visita_id}/insumos/consumidos")
def registrar_insumos_consumidos(
    visita_id: int,
    insumos: List[InsumoConsumidoRequest]
):
    conn = conectar_db()
    try:
        cur = conn.cursor()
        for insumo in insumos:
            # Verificamos si ya existe ese registro
            cur.execute("""
                SELECT id FROM insumos_consumidos
                WHERE instalacion_insumos_paciente_id = %s AND visita_id = %s
            """, (insumo.codigo, visita_id))
            existe = cur.fetchone()

            if existe:
                # Si ya existe, actualizamos la cantidad
                cur.execute("""
                    UPDATE insumos_consumidos
                    SET cantidad_consumida = %s
                    WHERE instalacion_insumos_paciente_id = %s AND visita_id = %s
                """, (insumo.cantidad, insumo.codigo, visita_id))
            else:
                # Si no existe, lo insertamos
                cur.execute("""
                    INSERT INTO insumos_consumidos (instalacion_insumos_paciente_id, visita_id, cantidad_consumida)
                    VALUES (%s, %s, %s)
                """, (insumo.codigo, visita_id, insumo.cantidad))

        conn.commit()
        return {"mensaje": "Insumos consumidos registrados correctamente"}
    except Exception as e:
        print("Error al registrar insumos consumidos:", e)
        raise HTTPException(status_code=500, detail="Error al registrar insumos consumidos")
    finally:
        cur.close()
        conn.close()

# Exponer con ngrok
public_url = ngrok.connect(8000, "http")
print(f"Web service accesible en: {public_url}")

if __name__ == "__main__":
    import uvicorn #type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)
