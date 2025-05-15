# back-móvil

### **Reconstruir el entorno virtual en otra máquina**

Si otra persona (o tú mismo en otro equipo) clona el repositorio, deberá seguir estos pasos para configurar el entorno virtual correctamente:

**1. Crear un nuevo entorno virtual**  
```bash
python -m venv venv
```
o
```bash
python3 -m venv venv
```
Dependiendo de la versión de Python

**2. Activarlo**

  **2.1 Windows (CMD o PowerShell)**  
```bash
venv\Scripts\activate
```
  **2.2 macOS/Linux**  
```bash
source venv/bin/activate
```

**3. Instalar las dependencias**  
```bash
pip install -r requirements.txt
```

**4. Iniciar el web service**  
```bash
python3 main.py
```
o
```bash
python main.py
```
Dependiendo de la versión de Python

Estos pasos aseguran que el entorno virtual esté correctamente configurado y que todas las dependencias necesarias sean instaladas para ejecutar el proyecto sin problemas.

