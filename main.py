import datetime
from fastapi import FastAPI, HTTPException, Depends, Header # type: ignore
from pydantic import BaseModel, ConfigDict  # type: ignore
import psycopg2  # type: ignore
from psycopg2 import Error  # type: ignore
from dotenv import load_dotenv  # type: ignore
from pyngrok import ngrok # type: ignore
import bcrypt # type: ignore
from jose import jwt, JWTError # type: ignore
import os
from datetime import datetime, timedelta

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

class PatientResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    nombre: str
    diagnostico: str
    hora: str
    direccion: str
    estadoVisita: str

class PatientsListResponse(BaseModel):
    patients: list[PatientResponse]

# Configuración de la conexión a la base de datos
conexion_params = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": "require" 
}

def conectar_db():
    try:
        conexion = psycopg2.connect(**conexion_params)
        return conexion
    except (Exception, Error) as error:
        print("Error al conectar a la base de datos:", error)
        return None
    
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

@app.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    conn = conectar_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, password FROM enfermera WHERE email = %s", (data.email,))
        result = cur.fetchone()
        if result is None:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

        id_, nombre, hashed_pw = result
        print(result)

        if hashed_pw.startswith("$2a$"):
            # Contraseña cifrada
            if not bcrypt.checkpw(data.password.encode(), hashed_pw.encode()):
                raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
        else:
            # Contraseña en texto plano
            if data.password != hashed_pw:
                raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
        # Token con expiración de 24 horas
        payload = {
            "id": id_,
            "nombre": nombre,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return {"token": token, "nombre": nombre}

    except HTTPException:
        # Permitir que errores 401 se propaguen tal como están
        raise
    except Exception as e:
        print("Error en login:", e)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass  # Evita errores si conn o cur no se crearon correctamente


@app.get("/pacientes", response_model=PatientsListResponse)
async def get_pacientes(current_user: dict = Depends(get_current_user)):
    conn = conectar_db()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    try:
        cur = conn.cursor()
        # Del token se extrae el id del usuario
        id_ = current_user["id"]
        # Se obtiene la fecha actual
        fecha_actual = datetime.now().date()
        # Se obtiene la fecha de la visita
        fecha_visita = fecha_actual.strftime("%Y-%m-%d")
        cur.execute("""
            SELECT
                p.nombre || ' ' || p.apellido AS nombre_completo,
                a.name AS diagnostico,
                v.hora_inicio_calculada,
                p.direccion,
                v.estado
            FROM
                visita v
            JOIN actividad_paciente_visita apv ON v.actividad_paciente_visita_id = apv.id
            JOIN paciente p ON apv.paciente_id = p.id
            JOIN actividad a ON apv.actividad_id = a.id
            WHERE
                v.enfermera_id = %s
                AND v.fecha_visita = %s
                AND p.estado = 'Activo'
        """, (id_,fecha_visita))
        result = cur.fetchall()
        print("Resultado de la consulta:", result)
        pacientes = []
        for row in result:
             paciente = PatientResponse(
                nombre=row[0] or "Sin nombre",
                diagnostico=row[1] or "Sin diagnóstico",
                hora=row[2].strftime("%H:%M") if row[2] else "Sin hora",
                direccion=row[3] or "Sin dirección",
                estadoVisita=row[4] or "Sin estado",
            )
        pacientes.append(paciente)

        print("Pacientes:", pacientes)
        return {"patients":pacientes}
    except Exception as e:
        print("Error en get_pacientes:", e)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception as e:
            print("Error al cerrar conexión:", e)


public_url = ngrok.connect(8000, "http")
print(f"Web service accesible en: {public_url}")

if __name__ == "__main__":
    import uvicorn  # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)