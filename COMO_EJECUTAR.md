# 🚀 Cómo Ejecutar el Proyecto

## Comandos Rápidos

### Para Desarrollo Local (Opción Rápida)

```bash
# 1. BUILD: Instalar dependencias
pip install -r requirements.txt

# 2. START: Ejecutar el servidor
python app.py
```

El servidor estará disponible en `http://localhost:5000`

---

## 📋 Comandos Completos por Tipo de Ejecución

### Opción 1: Monolito (Desarrollo Rápido)

Esta opción ejecuta todo en un solo proceso usando los archivos en la raíz del proyecto.

#### BUILD (Instalar Dependencias)
```bash
# Python
pip install -r requirements.txt

# Node.js (opcional, solo si usas WhatsApp)
cd whatsapp
npm install
cd ..
```

#### START (Ejecutar Servicios)
```bash
# Terminal 1: Backend Principal + Model API
python app.py
# → http://localhost:5000 (Backend)
# → http://localhost:5000/admin (Panel de Administración)

# Terminal 2 (Opcional): Model API Separado
python model_api.py
# → http://localhost:8001

# Terminal 3 (Opcional): WhatsApp Bridge
cd whatsapp
FLASK_URL=http://localhost:5000 npm start
```

---

### Opción 2: Servicios Separados (Arquitectura de Producción)

Esta opción ejecuta 3 servicios independientes en diferentes terminales.

#### BUILD (Instalar Dependencias de Cada Servicio)

```bash
# Servicio 1: Model API
cd service-1-model
pip install -r requirements.txt
cd ..

# Servicio 2: Backend Principal
cd service-2-backend
pip install -r requirements.txt
cd ..

# Servicio 3: WhatsApp Bridge
cd service-3-whatsapp
npm install
cd ..
```

#### START (Ejecutar Cada Servicio)

**Terminal 1: Servicio 1 (Model API)**
```bash
cd service-1-model
python model_api.py
# → http://localhost:8001
```

**Terminal 2: Servicio 2 (Backend Principal)**
```bash
cd service-2-backend
MODEL_API_URL=http://localhost:8001 python app.py
# → http://localhost:5000
# → http://localhost:5000/admin
```

**Terminal 3: Servicio 3 (WhatsApp Bridge)**
```bash
cd service-3-whatsapp
FLASK_URL=http://localhost:5000 npm start
# Escanea el código QR que aparece en la terminal
```

---

## 🔧 Comandos Detallados

### BUILD: Preparación del Entorno

El "build" en este proyecto significa instalar las dependencias necesarias:

1. **Dependencias Python:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Esto instala:
   - Flask (framework web)
   - llama-cpp-python (para el modelo de IA)
   - requests (para comunicación HTTP)

2. **Dependencias Node.js (solo para WhatsApp):**
   ```bash
   cd whatsapp  # o service-3-whatsapp
   npm install
   ```
   
   Esto instala:
   - whatsapp-web.js (cliente de WhatsApp)
   - axios (cliente HTTP)
   - qrcode-terminal (para mostrar QR en terminal)

3. **Descargar el Modelo de IA (requerido para funcionalidad completa):**
   ```bash
   mkdir -p models
   wget -O models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
     https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
   ```

### START: Ejecución de Servicios

El "start" es ejecutar los servicios:

1. **Backend Principal (app.py):**
   ```bash
   python app.py
   ```
   - Puerto: 5000
   - Endpoints: `/health`, `/agent`, `/admin`, etc.
   - Base de datos: SQLite en `instance/app.db`

2. **Model API (model_api.py):**
   ```bash
   python model_api.py
   ```
   - Puerto: 8001
   - Endpoints: `/health`, `/chat`
   - Carga el modelo Qwen 0.5B para inferencia

3. **WhatsApp Bridge:**
   ```bash
   cd whatsapp
   npm start
   ```
   - Muestra código QR en terminal
   - Mantiene conexión persistente con WhatsApp

---

## 🎯 Casos de Uso Comunes

### Solo quiero probar el backend sin IA
```bash
pip install -r requirements.txt
python app.py
# Accede a http://localhost:5000/admin
```

### Quiero probar todo el sistema con IA
```bash
# Terminal 1
python app.py

# Terminal 2
python model_api.py

# Terminal 3
cd whatsapp
npm install
FLASK_URL=http://localhost:5000 npm start
```

### Desarrollo con arquitectura separada
```bash
# Terminal 1
cd service-1-model && python model_api.py

# Terminal 2
cd service-2-backend && MODEL_API_URL=http://localhost:8001 python app.py

# Terminal 3
cd service-3-whatsapp && FLASK_URL=http://localhost:5000 npm start
```

---

## 📦 Scripts de Conveniencia

Para facilitar la ejecución, puedes usar estos comandos:

### Usando Make (si tienes make instalado)

Crea un archivo `Makefile`:
```makefile
.PHONY: build start dev

build:
	pip install -r requirements.txt
	cd whatsapp && npm install

start:
	python app.py

dev:
	python app.py
```

Luego ejecuta:
```bash
make build  # Instalar dependencias
make start  # Ejecutar servidor
```

### Usando Scripts Bash

Crea un archivo `start.sh`:
```bash
#!/bin/bash
echo "🚀 Iniciando Asistente Agrario..."
python app.py
```

Hazlo ejecutable y ejecútalo:
```bash
chmod +x start.sh
./start.sh
```

---

## 🌍 Variables de Entorno

Puedes configurar el proyecto con variables de entorno:

```bash
# Para el backend
export DATABASE_PATH=/ruta/a/tu/base.db
export LOCAL_MODEL_PATH=/ruta/a/modelo.gguf
export N_CTX=2048
export N_THREADS=1

# Para WhatsApp
export FLASK_URL=http://localhost:5000

# Ejecutar
python app.py
```

O usar un archivo `.env`:
```bash
# Copiar ejemplo
cp .env.example .env

# Editar .env con tus valores
nano .env

# Ejecutar (el app.py carga automáticamente .env)
python app.py
```

---

## ✅ Verificar que Todo Funciona

1. **Backend corriendo:**
   ```bash
   curl http://localhost:5000/health
   # Respuesta: {"status":"ok","time":"..."}
   ```

2. **Model API corriendo:**
   ```bash
   curl http://localhost:8001/health
   # Respuesta: {"status":"ok"}
   ```

3. **Panel de administración:**
   - Abre: http://localhost:5000/admin
   - Deberías ver la interfaz web

4. **WhatsApp conectado:**
   - Verifica que aparezca "Client is ready!" en la terminal

---

## 🆘 Problemas Comunes

### Error: "No module named 'flask'"
```bash
# Solución: Instalar dependencias
pip install -r requirements.txt
```

### Error: "No se encontró el modelo local"
```bash
# Solución: Descargar el modelo
mkdir -p models
wget -O models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

### Error: "Address already in use"
```bash
# Solución: Puerto ocupado, cambia el puerto o detén el proceso
# Encontrar proceso en puerto 5000:
lsof -i :5000
# Matar proceso:
kill -9 <PID>
```

### WhatsApp no muestra QR
```bash
# Solución: Verificar que Node.js y npm están instalados
node --version
npm --version

# Reinstalar dependencias
cd whatsapp
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 Más Información

- **Guía Completa de Despliegue:** Ver `DEPLOYMENT_GUIDE.md`
- **Inicio Rápido:** Ver `QUICK_START.md`
- **Arquitectura:** Ver `docs/ARQUITECTURA_DESPLIEGUE.md`
- **FAQ:** Ver `docs/FAQ.md`

---

## 💡 Resumen de Comandos

```bash
# 🔨 BUILD (Instalar dependencias)
pip install -r requirements.txt
cd whatsapp && npm install

# 🚀 START (Ejecutar servidor)
python app.py                    # Backend en http://localhost:5000
python model_api.py              # Model API en http://localhost:8001
cd whatsapp && npm start         # WhatsApp Bridge

# 🌐 Acceder
http://localhost:5000            # API
http://localhost:5000/admin      # Panel de Administración
```

¡Eso es todo! 🎉
