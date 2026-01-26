# Arquitectura Real del Sistema

## 3 Partes del Sistema:

### 1. Backend Flask en Leapcell (app.py)
- **Dónde:** Leapcell
- **Qué es:** Tu aplicación Flask principal con:
  - Panel de administración (`/admin`)
  - API de agentes (`/agent`)
  - Base de datos SQLite
  - Modelo de lenguaje (GGUF local o API externa)
- **Cómo ejecutar:**
  ```bash
  python app.py
  ```
- **URL:** `https://tu-app.leapcell.io`

### 2. Puente WhatsApp (whatsapp/index.js)
- **Dónde:** Tu computadora local o un servidor
- **Qué es:** Cliente de WhatsApp Web que conecta con el backend
- **Cómo ejecutar:**
  ```bash
  cd whatsapp
  export FLASK_URL="https://tu-app.leapcell.io"
  npm install
  npm start
  ```
- **Nota:** Este NO va en Vercel porque necesita sesión persistente de navegador

### 3. Webhook en Vercel (api/webhook.js) - OPCIONAL
- **Dónde:** Vercel
- **Qué es:** Endpoint para recibir webhooks de WhatsApp Business API
- **Para qué:** Si en el futuro migras a WhatsApp Business API oficial
- **URL:** `https://tu-proyecto.vercel.app/webhook`

## Flujo de Ejecución

```
WhatsApp → Puente Local (Node.js) → Backend Leapcell (Flask) → Modelo
                                          ↑
                                   Panel Admin aquí
```

## Setup Rápido

1. **Despliega app.py en Leapcell:**
   - Sube el repositorio a Leapcell
   - Configura variables de entorno (LOCAL_MODEL_PATH, etc.)
   - La app correrá en `https://tu-app.leapcell.io`
   - Accede al admin en `https://tu-app.leapcell.io/admin`

2. **Ejecuta el puente WhatsApp localmente:**
   ```bash
   cd whatsapp
   export FLASK_URL="https://tu-app.leapcell.io"
   npm start
   ```
   - Escanea el QR con tu WhatsApp
   - Los mensajes se enviarán al backend en Leapcell

3. **Vercel (OPCIONAL):** Solo si quieres webhook de WhatsApp Business API
   ```bash
   vercel
   ```
   - Configura `LEAPCELL_BACKEND_URL` en Vercel

## Lo que NO va en Vercel

- ❌ app.py (va en Leapcell)
- ❌ Panel de administración (va en Leapcell)
- ❌ Modelo GGUF (va en Leapcell)
- ❌ whatsapp/index.js (va local o en servidor con sesión persistente)

## Lo que SÍ va en Vercel (opcional)

- ✅ api/webhook.js - Solo para WhatsApp Business API webhooks

## Resumen

- **Leapcell = Todo (app.py con admin y modelo)**
- **Local = Puente WhatsApp (whatsapp/index.js)**
- **Vercel = Webhook opcional (api/webhook.js)** solo si usas WhatsApp Business API

La confusión era que yo puse app.py en Vercel, pero debe estar en Leapcell.
