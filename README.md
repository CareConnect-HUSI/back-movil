# Back-Móvil CareConnect

## Descripción
El backend móvil de CareConnect es un componente clave del sistema desarrollado para el Hospital Universitario San Ignacio. Proporciona una API REST para la aplicación móvil utilizada por enfermeras auxiliares, permitiendo autenticación, consulta de pacientes asignados, registro de horas de visitas, gestión de insumos y actualización de estados de visitas. Se integra con módulos de geocodificación y optimización de rutas, asegurando la sincronización con el portal web administrativo.

## Funcionalidades
- **Autenticación**: Login de enfermeras con JWT (endpoint `POST /login`).
- **Pacientes Asignados**: Consulta de pacientes por fecha y enfermera (`GET /pacientes-asignados`).
- **Gestión de Visitas**: Registro de horas (`POST /visita/{id}/hora`), procedimientos (`GET /visita/{visita_id}/procedimientos`), insumos (`GET/POST /visita/{visita_id}/insumos`), y estado (`GET/PUT /visita/{visita_id}/estado`).
- **Seguridad**: Autenticación mediante tokens JWT para endpoints protegidos.

## Tecnologías
- **Framework**: FastAPI
- **Base de Datos**: PostgreSQL (via `psycopg2`)
- **Autenticación**: JWT y bcrypt
- **Dependencias Principales**:
  - `fastapi`
  - `pydantic`
  - `psycopg2-binary`
  - `python-jose[cryptography]`
  - `bcrypt`
  - `python-dotenv`
  - `pyngrok`
- **Python**: 3.9+

## Requisitos
- Python 3.9 o superior
- PostgreSQL (configurado en `.env`)
- Archivo `.env` con:
  ```
  DB_HOST=jdbc:postgresql://your_host/database
  DB_PORT=5432
  DB_NAME=neondb
  DB_USER=neondb_owner
  DB_PASSWORD=your_password
  SECRET_KEY=your_jwt_secret
  ```

## Instalación
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/careconnect/back-movil.git
   cd back-movil
   ```

2. Configurar el entorno virtual e instalar dependencias (ver sección "Reconstruir el entorno virtual").

3. Configurar `.env` con las credenciales de la base de datos y la clave JWT.

4. Iniciar el servidor:
   ```bash
   python3 main.py
   ```

   El servicio estará disponible en `http://localhost:8000` (o vía ngrok para acceso público).

## Reconstruir el Entorno Virtual en Otra Máquina
Si clonas el repositorio en otro equipo, sigue estos pasos para configurar el entorno virtual:

1. **Crear un nuevo entorno virtual**:
   ```bash
   python -m venv venv
   ```

2. **Activar el entorno**:
   - **Windows (CMD o PowerShell)**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

3. **Instalar las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar el web service**:
   ```bash
   python3 main.py
   ```

Estos pasos aseguran que el entorno virtual esté correctamente configurado y que todas las dependencias necesarias sean instaladas para ejecutar el proyecto sin problemas.

## Uso
- **Autenticación**: Usa `POST /login` con email y contraseña para obtener un token JWT.
- **Endpoints Protegidos**: Incluye el token en el header `Authorization: Bearer <token>` para acceder a endpoints como `GET /pacientes-asignados`.
- **Ejemplo**:
  ```bash
  curl -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d '{"email": "enfermera@example.com", "password": "password123"}'
  ```


## Autoría
- Juan David González
- Lina María Salamanca
- Laura Alexandra Rodríguez
- Axel Nicolás Caro

**Pontificia Universidad Javeriana**  
**Mayo 26, 2025**