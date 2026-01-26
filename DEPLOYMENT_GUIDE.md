# Guía Completa de Despliegue - 3 Servicios

Esta guía te llevará paso a paso para desplegar los 3 servicios de la arquitectura.

## 📋 Pre-requisitos

- Cuenta en [Leapcell](https://leapcell.io) (para Servicios 1 y 2)
- Cuenta en [Railway](https://railway.app) o [Render](https://render.com) (para Servicio 3)
- Repositorio GitHub con el código
- Modelo GGUF descargado (~3-4 GB)

## 🎯 Orden de Despliegue

**IMPORTANTE**: Desplegar en este orden para que las URLs estén disponibles.

```
1. Servicio 1 (Model API) → Anotar URL
2. Servicio 2 (Backend) → Usar URL del Servicio 1, Anotar URL
3. Servicio 3 (WhatsApp) → Usar URL del Servicio 2
```

---

## 🚀 PASO 1: Desplegar Servicio 1 (Model API)

### 1.1 Preparar Modelo GGUF

Si aún no tienes el modelo:
```bash
mkdir -p models
wget -O models/qwen2.5-3b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
```

### 1.2 Crear Proyecto en Leapcell

1. Ir a https://leapcell.io
2. Click en "New Project"
3. Seleccionar "Deploy from GitHub"
4. Autorizar acceso a tu repositorio
5. Seleccionar el repositorio
6. **Root Directory**: `service-1-model`

### 1.3 Configurar Build

En la configuración del proyecto:
```
Framework: Python
Build Command: pip install -r requirements.txt
Start Command: python model_api.py
Port: 8001
```

### 1.4 Variables de Entorno

En Settings → Environment Variables:
```
LOCAL_MODEL_PATH=/app/models/qwen2.5-3b-instruct-q4_k_m.gguf
N_CTX=2048
N_THREADS=1
```

### 1.5 Configurar Almacenamiento (Modelo GGUF)

**Opción A: Volumen Persistente** (recomendado)
1. En Leapcell, ir a "Storage" o "Volumes"
2. Crear nuevo volumen de 5 GB
3. Montar en: `/app/models`
4. Subir `qwen2.5-3b-instruct-q4_k_m.gguf` al volumen

**Opción B: Descargar en Build**
Crear archivo `download_model.sh` en `service-1-model/`:
```bash
#!/bin/bash
mkdir -p models
if [ ! -f models/qwen2.5-3b-instruct-q4_k_m.gguf ]; then
  wget -O models/qwen2.5-3b-instruct-q4_k_m.gguf \
    https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
fi
```

Modificar Build Command:
```
bash download_model.sh && pip install -r requirements.txt
```

### 1.6 Deploy

1. Click "Deploy"
2. Esperar build (5-10 minutos)
3. Verificar logs: debe decir "Running on http://0.0.0.0:8001"

### 1.7 Anotar URL

Una vez desplegado, copiar la URL:
```
https://model-api-xxxxx.leapcell.dev
```

### 1.8 Probar

```bash
# Health check
curl https://model-api-xxxxx.leapcell.dev/health

# Debería devolver: {"status":"ok"}
```

✅ **Servicio 1 completado**

---

## 🚀 PASO 2: Desplegar Servicio 2 (Backend)

### 2.1 Crear Proyecto en Leapcell

1. Ir a https://leapcell.io
2. Click en "New Project"
3. Seleccionar "Deploy from GitHub"
4. Seleccionar el mismo repositorio
5. **Root Directory**: `service-2-backend`

### 2.2 Configurar Build

```
Framework: Python
Build Command: pip install -r requirements.txt
Start Command: python app.py
Port: 5000
```

### 2.3 Variables de Entorno

⚠️ **IMPORTANTE**: Usar la URL del Servicio 1 que anotaste

En Settings → Environment Variables:
```
MODEL_API_URL=https://model-api-xxxxx.leapcell.dev
DATABASE_PATH=/app/instance/app.db
DEFAULT_TIMEZONE=America/Lima
DAILY_CHECKIN_HOUR=8
```

### 2.4 Configurar Volumen Persistente (Base de Datos)

⚠️ **CRÍTICO**: SQLite necesita persistencia

1. En Leapcell, ir a "Storage" o "Volumes"
2. Crear nuevo volumen de 1 GB
3. Montar en: `/app/instance`
4. Esto persistirá `app.db` entre deploys

### 2.5 Deploy

1. Click "Deploy"
2. Esperar build (2-5 minutos)
3. Verificar logs: debe decir "Running on http://0.0.0.0:5000"

### 2.6 Anotar URL

Una vez desplegado, copiar la URL:
```
https://backend-xxxxx.leapcell.dev
```

### 2.7 Probar

```bash
# Health check
curl https://backend-xxxxx.leapcell.dev/health

# Abrir panel admin en navegador
https://backend-xxxxx.leapcell.dev/admin
```

### 2.8 Configurar Panel Admin

1. Ir a `https://backend-xxxxx.leapcell.dev/admin`
2. Ir a "Agents" y activar los 3 roles
3. Ir a "Producers" y agregar tu número de WhatsApp:
   - Phone: `51987654321@c.us` (formato WhatsApp)
   - Allowed: ✅ (checkbox marcado)
   - Status: `active`

✅ **Servicio 2 completado**

---

## 🚀 PASO 3: Desplegar Servicio 3 (WhatsApp)

⚠️ **NO DESPLEGAR EN LEAPCELL** - Debe ser persistente

### Opción A: Railway (RECOMENDADO)

#### 3.1 Crear Cuenta en Railway

1. Ir a https://railway.app
2. Sign up con GitHub
3. Verificar email

#### 3.2 Nuevo Proyecto

1. Dashboard → "New Project"
2. "Deploy from GitHub repo"
3. Seleccionar tu repositorio
4. Railway detecta automáticamente que es Node.js

#### 3.3 Configurar Root Directory

Si Railway no lo detecta automáticamente:
1. Settings → Service
2. Root Directory: `service-3-whatsapp`

#### 3.4 Variables de Entorno

⚠️ **IMPORTANTE**: Usar la URL del Servicio 2 que anotaste

En Settings → Variables:
```
FLASK_URL=https://backend-xxxxx.leapcell.dev
DEFAULT_ROLE=formulario
```

#### 3.5 Deploy

1. Railway hace deploy automáticamente
2. Ver logs en tiempo real

#### 3.6 Escanear QR

**Problema**: Railway no muestra QR bien en la UI

**Solución temporal**:
1. Ver logs crudos (puede aparecer el QR)
2. O modificar `index.js` para enviar QR a webhook (ver README)

**Mejor opción si tienes VPS**:
Hacer el primer escaneo en local y luego subir `.wwebjs_auth/` a Railway.

#### 3.7 Verificar Conexión

En los logs debe aparecer:
```
Escanea el QR con tu WhatsApp para iniciar sesión.
[QR aparece aquí]
WhatsApp bridge listo.
```

Una vez escaneado:
```
WhatsApp bridge listo.
```

#### 3.8 Probar

Envía un mensaje de WhatsApp al número vinculado:
```
Hola
```

Deberías recibir respuesta del bot.

✅ **Servicio 3 completado**

### Opción B: Render.com

Si prefieres Render:

#### 3.1 Crear Cuenta

1. Ir a https://render.com
2. Sign up con GitHub

#### 3.2 Nuevo Web Service

1. Dashboard → "New" → "Web Service"
2. Connect GitHub repository
3. Seleccionar repositorio

#### 3.3 Configurar

```
Name: whatsapp-bridge
Root Directory: service-3-whatsapp
Environment: Node
Build Command: npm install
Start Command: npm start
```

#### 3.4 Plan

- **Free**: Se duerme después de 15 min (NO para producción)
- **Starter ($7/mes)**: No se duerme (RECOMENDADO)

#### 3.5 Variables de Entorno

```
FLASK_URL=https://backend-xxxxx.leapcell.dev
DEFAULT_ROLE=formulario
```

#### 3.6 Deploy y QR

Mismo proceso que Railway. Ver logs para QR.

---

## 🔄 Verificación del Flujo Completo

### Test 1: Health Checks

```bash
# Servicio 1
curl https://model-api-xxxxx.leapcell.dev/health
# → {"status":"ok"}

# Servicio 2
curl https://backend-xxxxx.leapcell.dev/health
# → {"status":"ok"}
```

### Test 2: Endpoint /agent (desde Servicio 2)

```bash
curl -X POST https://backend-xxxxx.leapcell.dev/agent \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "51987654321@c.us",
    "message": "Hola, ¿me ayudas?",
    "role": "consulta"
  }'
```

Debería devolver JSON con `model_output.respuesta_chat`.

### Test 3: WhatsApp End-to-End

1. Envía mensaje por WhatsApp al número vinculado: `Hola`
2. Deberías recibir respuesta en segundos
3. Revisar logs en Railway/Render (Servicio 3)
4. Revisar logs en Leapcell (Servicio 2)

### Test 4: Panel Admin

1. Abrir `https://backend-xxxxx.leapcell.dev/admin`
2. Ir a "Conversations"
3. Deberías ver el mensaje que enviaste

---

## 📊 Monitoreo

### Logs en Tiempo Real

**Servicio 1 y 2 (Leapcell):**
- Dashboard → Proyecto → Logs

**Servicio 3 (Railway):**
- Dashboard → Proyecto → Deployments → Logs

**Servicio 3 (Render):**
- Dashboard → Servicio → Logs

### Métricas

Monitorear:
- Número de requests
- Tiempo de respuesta
- Errores (4xx, 5xx)
- Memoria usada
- Cold starts (Servicio 1)

### Alertas

Configurar alertas en las plataformas:
- Leapcell: Health checks
- Railway: Crashes y errores
- UptimeRobot: Monitoreo externo

---

## 🐛 Troubleshooting

### Servicio 1: "Cannot load model"

**Causa**: Modelo no encontrado o no hay RAM suficiente

**Solución**:
- Verificar `LOCAL_MODEL_PATH`
- Verificar que volumen está montado
- Aumentar RAM en plan de Leapcell
- Reducir `N_CTX` si falta memoria

### Servicio 2: "Cannot connect to Model API"

**Causa**: URL incorrecta o Servicio 1 caído

**Solución**:
- Verificar `MODEL_API_URL` en variables de entorno
- Hacer health check a Servicio 1
- Ver logs de Servicio 1

### Servicio 2: "Database locked"

**Causa**: SQLite con alta concurrencia

**Solución**:
- Asegurar volumen persistente configurado
- Considerar migrar a PostgreSQL si es frecuente

### Servicio 3: QR no aparece

**Causa**: Railway/Render no muestran bien el QR

**Solución**:
- Ver logs crudos
- Modificar código para enviar QR a webhook
- Hacer primer escaneo en local y subir sesión

### Servicio 3: "Session closed"

**Causa**: Sesión cerrada desde WhatsApp

**Solución**:
- Borrar `.wwebjs_auth/` en el servicio
- Reiniciar servicio
- Escanear nuevo QR

### Servicio 3: "Cannot connect to backend"

**Causa**: URL incorrecta o Servicio 2 caído

**Solución**:
- Verificar `FLASK_URL` en variables de entorno
- Hacer health check a Servicio 2
- Verificar que URL es pública (no localhost)

### WhatsApp no responde

**Checklist**:
1. ✅ Servicio 3 muestra "WhatsApp bridge listo"
2. ✅ Productor está autorizado en `/admin/producers`
3. ✅ Phone format correcto: `51987654321@c.us`
4. ✅ Servicio 2 responde a `/health`
5. ✅ Servicio 1 responde a `/health`
6. Ver logs de Servicio 3 para errores

---

## 💰 Resumen de Costos

| Servicio | Plataforma | Costo Mensual |
|----------|-----------|---------------|
| Servicio 1 (Model API) | Leapcell | $0-5 |
| Servicio 2 (Backend) | Leapcell | $0-5 |
| Servicio 3 (WhatsApp) | Railway | $5 |
| | Render Starter | $7 |
| **TOTAL** | | **$5-17/mes** |

### Free Tier
- Leapcell: Generoso free tier
- Railway: $5 incluidos gratis
- Render Free: Se duerme (no para producción)

---

## 🎉 ¡Listo!

Si completaste todos los pasos:

✅ Servicio 1 respondiendo en Leapcell  
✅ Servicio 2 respondiendo en Leapcell  
✅ Servicio 3 persistente en Railway/Render  
✅ WhatsApp recibiendo y respondiendo mensajes  
✅ Panel admin funcionando  

---

## 📚 Próximos Pasos

1. **Seguridad**: Agregar autenticación al panel admin
2. **Monitoreo**: Configurar alertas y métricas
3. **Backup**: Hacer backup de base de datos
4. **Escalado**: Considerar PostgreSQL si crece
5. **WhatsApp Oficial**: Migrar a Business API en producción

---

## 🆘 Soporte

Si tienes problemas:
1. Revisar logs de cada servicio
2. Verificar variables de entorno
3. Hacer health checks de cada servicio
4. Revisar esta guía paso a paso
5. Consultar READMEs individuales de cada servicio

¡Éxito con tu despliegue! 🚀
