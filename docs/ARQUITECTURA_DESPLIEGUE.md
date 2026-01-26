# Arquitectura de Despliegue - 3 Servicios

## 🎯 Problema y Solución

### El Desafío
- **Leapcell solo soporta serverless** (se apaga después de cada request)
- **WhatsApp Web requiere proceso persistente** (mantener sesión y navegador)
- **No se puede "pasar la sesión"** de WhatsApp entre servicios

### ✅ Solución: Arquitectura Híbrida
Usar diferentes plataformas según las necesidades de cada servicio.

---

## 🏗️ Arquitectura de 3 Servicios

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE COMUNICACIÓN                        │
└─────────────────────────────────────────────────────────────────────┘

    WhatsApp Usuario
         │
         │ (mensaje)
         ▼
    ┌─────────────────┐
    │  SERVICIO 3     │  ← Node.js PERSISTENTE (Railway/Render/etc)
    │  WhatsApp       │    - whatsapp-web.js
    │  Bridge         │    - Mantiene sesión QR
    └────────┬────────┘    - Puerto: 3000
             │
             │ HTTP POST /agent
             ▼
    ┌─────────────────┐
    │  SERVICIO 2     │  ← Flask SERVERLESS (Leapcell)
    │  Backend        │    - API principal
    │  Principal      │    - Base de datos SQLite
    └────────┬────────┘    - Panel /admin
             │              - Puerto: 5000
             │
             │ HTTP POST /chat
             ▼
    ┌─────────────────┐
    │  SERVICIO 1     │  ← Flask SERVERLESS (Leapcell)
    │  Model API      │    - Modelo LLM (GGUF)
    │  (LLM)          │    - Inferencia
    └─────────────────┘    - Puerto: 8001
```

---

## 📦 Servicio 1: Model API (LLM)

### Descripción
API Flask dedicada exclusivamente a inferencia del modelo LLM.

### Características
- **Tipo**: Serverless OK ✅
- **Framework**: Flask
- **Modelo**: llama-cpp-python + GGUF
- **Puerto**: 8001

### Plataforma Recomendada
- **Leapcell** (serverless) ✅
- Alternativas: Railway, Render

### ¿Por qué puede ser serverless?
- Solo procesa requests individuales
- No mantiene estado entre llamadas
- Carga el modelo en cada cold start (lento pero funcional)

### Archivos del Servicio
```
service-1-model/
├── model_api.py          # API principal
├── requirements.txt      # Dependencias Python
├── .env                  # Variables de entorno
└── models/              # Carpeta para modelo GGUF
    └── qwen2.5-3b-instruct-q4_k_m.gguf
```

### Variables de Entorno
```bash
LOCAL_MODEL_PATH=/app/models/qwen2.5-3b-instruct-q4_k_m.gguf
N_CTX=2048
N_THREADS=1
PORT=8001
```

### Endpoints
- `GET /health` - Health check
- `POST /chat` - Inferencia del modelo

---

## 📦 Servicio 2: Backend Principal (Flask)

### Descripción
Backend principal con lógica de negocio, base de datos y panel admin.

### Características
- **Tipo**: Serverless OK ✅
- **Framework**: Flask
- **Base de datos**: SQLite (incluida en el dyno)
- **Puerto**: 5000

### Plataforma Recomendada
- **Leapcell** (serverless) ✅
- Alternativas: Railway, Render

### ¿Por qué puede ser serverless?
- SQLite se persiste en volumen
- No mantiene sesión de WhatsApp
- Solo orquesta llamadas HTTP

### Archivos del Servicio
```
service-2-backend/
├── app.py               # API principal + admin
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno
├── templates/           # HTML del panel admin
└── instance/           # Base de datos SQLite
    └── app.db
```

### Variables de Entorno
```bash
DATABASE_PATH=/app/instance/app.db
MODEL_API_URL=https://tu-servicio-1.leapcell.dev
DEFAULT_TIMEZONE=America/Lima
DAILY_CHECKIN_HOUR=8
PORT=5000
```

### Endpoints
- `GET /health` - Health check
- `POST /agent` - Recibe mensaje y orquesta respuesta
- `GET /admin` - Panel de administración
- `POST /form/update` - Actualiza formularios
- `POST /alert` - Crea alertas
- `GET /alerts/pending` - Alertas pendientes
- `POST /alerts/:id/sent` - Marca alerta como enviada

---

## 📦 Servicio 3: WhatsApp Bridge (Node.js)

### Descripción
⚠️ **ESTE ES EL SERVICIO CRÍTICO QUE NO PUEDE SER SERVERLESS**

### Características
- **Tipo**: PERSISTENTE (24/7) ⚠️
- **Framework**: Node.js + whatsapp-web.js
- **Puerto**: 3000

### ¿Por qué DEBE ser persistente?
1. **Mantiene sesión de WhatsApp Web** activa todo el tiempo
2. **Controla navegador Chromium** en segundo plano
3. **Guarda archivos de sesión** (.wwebjs_auth)
4. **Escucha mensajes** en tiempo real (no puede "dormir")

### Plataforma Recomendada
**NO PUEDE DESPLEGARSE EN LEAPCELL** ❌

Opciones viables:
1. **Railway** ($5/mes) ✅ RECOMENDADO
   - Soporta procesos persistentes
   - Plan Hobby gratuito disponible
   - Fácil despliegue desde GitHub

2. **Render** (plan gratuito limitado) ✅
   - Web Services (no serverless)
   - Se duerme después de 15 min sin uso (plan free)
   - Plan pagado: $7/mes sin sleep

3. **Fly.io** ($5/mes aprox) ✅
   - Soporta procesos persistentes
   - Buen free tier

4. **VPS tradicional** (DigitalOcean, Linode, etc)
   - Mayor control
   - Requiere configuración manual

### Archivos del Servicio
```
service-3-whatsapp/
├── index.js             # Bridge WhatsApp
├── package.json         # Dependencias Node
├── .env                 # Variables de entorno
└── .wwebjs_auth/       # Sesión WhatsApp (generada automáticamente)
```

### Variables de Entorno
```bash
FLASK_URL=https://tu-servicio-2.leapcell.dev
DEFAULT_ROLE=formulario
PORT=3000
```

### ¿Cómo funciona?
1. **Inicialización**: Genera QR que debes escanear con WhatsApp
2. **Sesión persistente**: Guarda sesión en `.wwebjs_auth/`
3. **Escucha mensajes**: 24/7 esperando mensajes de WhatsApp
4. **Reenvía a Backend**: Hace HTTP POST a Servicio 2
5. **Responde**: Envía respuesta del backend al usuario

---

## 🔄 Flujo Completo de un Mensaje

```
1. Usuario envía mensaje por WhatsApp
   │
   ▼
2. Servicio 3 (Node persistente) recibe el mensaje
   │
   ▼
3. Servicio 3 hace POST a Servicio 2: /agent
   body: { phone: "...", message: "...", role: "formulario" }
   │
   ▼
4. Servicio 2 (Flask):
   - Verifica si productor está autorizado
   - Construye contexto (historial, formulario, etc)
   - Hace POST a Servicio 1: /chat
   │
   ▼
5. Servicio 1 (Model API):
   - Carga modelo GGUF
   - Procesa con LLM
   - Devuelve JSON con respuesta
   │
   ▼
6. Servicio 2:
   - Recibe respuesta del modelo
   - Actualiza base de datos si necesario
   - Devuelve respuesta al Servicio 3
   │
   ▼
7. Servicio 3:
   - Extrae "respuesta_chat" del JSON
   - Envía mensaje de vuelta por WhatsApp
   │
   ▼
8. Usuario recibe respuesta
```

---

## 🚀 Guía de Despliegue

### Paso 1: Desplegar Servicio 1 (Model API) en Leapcell

1. Crear nuevo proyecto en Leapcell
2. Conectar GitHub (carpeta `service-1-model/`)
3. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python model_api.py`
   - Puerto: 8001
4. Variables de entorno (ver arriba)
5. **IMPORTANTE**: Subir modelo GGUF (3-4 GB)
   - Usar volumen persistente en Leapcell
   - O descargar en build: `wget` en script de inicio

6. Deploy y anotar URL: `https://model-api-xxx.leapcell.dev`

### Paso 2: Desplegar Servicio 2 (Backend) en Leapcell

1. Crear nuevo proyecto en Leapcell
2. Conectar GitHub (carpeta `service-2-backend/`)
3. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Puerto: 5000
4. Variables de entorno:
   - `MODEL_API_URL=https://model-api-xxx.leapcell.dev` (URL del Servicio 1)
   - Resto de variables (ver arriba)
5. Configurar volumen persistente para SQLite:
   - Montar `/app/instance` para persistir `app.db`

6. Deploy y anotar URL: `https://backend-xxx.leapcell.dev`

7. Acceder al panel admin: `https://backend-xxx.leapcell.dev/admin`

### Paso 3: Desplegar Servicio 3 (WhatsApp) en Railway ⚠️

**NO DESPLEGAR EN LEAPCELL - DEBE SER PERSISTENTE**

#### Opción A: Railway (RECOMENDADO)

1. Crear cuenta en Railway.app
2. New Project → Deploy from GitHub
3. Seleccionar repo y carpeta `service-3-whatsapp/`
4. Railway detecta automáticamente Node.js
5. Configurar variables de entorno:
   ```
   FLASK_URL=https://backend-xxx.leapcell.dev
   DEFAULT_ROLE=formulario
   ```
6. Deploy
7. Ver logs: aparecerá el QR para escanear
8. Escanear QR con WhatsApp
9. ✅ Sesión queda guardada en `.wwebjs_auth/`

#### Opción B: Render.com

1. Crear cuenta en Render
2. New → Web Service
3. Conectar GitHub (carpeta `service-3-whatsapp/`)
4. Tipo: **Web Service** (no Background Worker)
5. Build: `npm install`
6. Start: `npm start`
7. Variables de entorno (igual que arriba)
8. ⚠️ En plan gratuito se duerme después de 15 min
   - Para uso real, necesitas plan pagado ($7/mes)

#### Opción C: VPS Manual

Si tienes un servidor:

```bash
# Instalar Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clonar repo
git clone https://github.com/tu-usuario/repo.git
cd repo/service-3-whatsapp

# Instalar dependencias
npm install

# Configurar .env
echo "FLASK_URL=https://backend-xxx.leapcell.dev" > .env
echo "DEFAULT_ROLE=formulario" >> .env

# Iniciar con PM2 (para que no se caiga)
npm install -g pm2
pm2 start index.js --name whatsapp-bridge
pm2 save
pm2 startup
```

---

## 🔒 Consideraciones de Seguridad

1. **Secrets**: Usar variables de entorno, no hardcodear
2. **CORS**: Configurar en Servicio 2 solo para dominios confiables
3. **Rate Limiting**: Implementar en todos los endpoints
4. **WhatsApp**: Migrar a Business API en producción
5. **Base de datos**: Considerar PostgreSQL si crece

---

## 📊 Costos Estimados

| Servicio | Plataforma | Costo Mensual |
|----------|-----------|---------------|
| Servicio 1 (Model API) | Leapcell | Gratis / $5 |
| Servicio 2 (Backend) | Leapcell | Gratis / $5 |
| Servicio 3 (WhatsApp) | Railway | $5 |
| **TOTAL** | | **~$5-15/mes** |

### Optimización de Costos
- Leapcell tiene free tier generoso
- Railway: $5/mes incluyen bastante uso
- Render free tier: solo si no te importa que se duerma

---

## ❓ Preguntas Frecuentes

### ¿Puedo usar solo Leapcell?
**NO** para WhatsApp. Leapcell es serverless, WhatsApp necesita persistente.

### ¿Puedo "pasar la sesión" de WhatsApp?
**NO**. La sesión vive en el proceso Node con archivos locales.

### ¿Y si uso Next.js?
Next.js serverless (Vercel) **NO** sirve para WhatsApp. Solo para frontend.

### ¿Necesito VPS?
No necesariamente. Railway/Render son más fáciles y baratos.

### ¿Cuánta RAM necesito?
- Servicio 1: 2-4 GB (modelo GGUF)
- Servicio 2: 512 MB - 1 GB
- Servicio 3: 512 MB

### ¿Funcionará con modelo grande?
Depende de la RAM. Qwen 3B funciona con 2 GB. Modelos más grandes necesitan más.

---

## 🎯 Conclusión

La arquitectura de 3 servicios **SÍ FUNCIONA** si:

✅ Servicio 1 y 2 van a Leapcell (serverless)  
✅ Servicio 3 va a Railway/Render/VPS (persistente)  
✅ Se comunican por HTTP con URLs públicas  
✅ Servicio 3 mantiene sesión de WhatsApp 24/7  

**NO INTENTES** poner WhatsApp en serverless. No funcionará.

Para más detalles técnicos, ver archivos en cada carpeta de servicio.
