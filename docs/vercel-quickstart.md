# Inicio Rápido - Deployment en Vercel

Esta guía rápida te ayuda a desplegar el sistema en Vercel en menos de 10 minutos.

## ¿Qué necesitas?

1. ✅ Cuenta en Vercel (gratis): https://vercel.com/signup
2. ✅ Tu repositorio GitHub conectado a Vercel
3. ✅ API de modelo de lenguaje (Grok, OpenAI, u otro proveedor)

## Pasos Rápidos

### 1. Conecta tu repositorio a Vercel

```bash
# Desde la línea de comandos (opción A)
npm i -g vercel
vercel login
vercel

# O desde el navegador (opción B)
# Ve a https://vercel.com/new
# Importa tu repositorio de GitHub
```

### 2. Configura las variables de entorno

En Vercel Dashboard → Settings → Environment Variables, agrega:

```
MODEL_API_URL=https://tu-api-del-modelo.com
```

**Opcional:** Si usas un proveedor específico como Grok:

```
MML_PROVIDER=xai
XAI_API_KEY=tu_api_key_aqui
XAI_MODEL=grok-4-latest
```

### 3. Despliega

Vercel desplegará automáticamente tu proyecto. ¡Eso es todo!

### 4. Verifica que funciona

```bash
# Reemplaza con tu URL de Vercel
curl https://tu-proyecto.vercel.app/health
```

Deberías ver:
```json
{"status": "ok", "time": "2026-..."}
```

### 5. Conecta WhatsApp

En tu máquina local:

```bash
cd whatsapp
export FLASK_URL="https://tu-proyecto.vercel.app"
npm install
npm start
```

Escanea el QR con WhatsApp y ¡listo!

## Archivos Importantes

- ✅ `vercel.json` - Configuración de Vercel (ya creado)
- ✅ `api/index.py` - Entry point serverless (ya creado)
- ✅ `.vercelignore` - Archivos a ignorar (ya creado)
- ✅ `requirements.txt` - Dependencias Python

## ¿Problemas?

### "llama-cpp-python no está instalado"
→ Configura `MODEL_API_URL` en las variables de entorno de Vercel

### "Cannot find module"
→ Asegúrate de que `requirements.txt` tenga Flask y requests

### "Timeout"
→ Tu API de modelo está tardando mucho. Intenta reducir `max_tokens`

## Siguiente: Usar el Sistema

1. Ve al panel de admin: `https://tu-proyecto.vercel.app/admin`
2. Registra productores autorizados
3. Configura los 3 roles (formulario, consulta, intervención)
4. ¡Comienza a recibir mensajes por WhatsApp!

## Documentación Completa

Para más detalles: [docs/vercel-deployment.md](./vercel-deployment.md)

---

**¿Necesitas ayuda?** Revisa los logs en Vercel Dashboard → Deployments → [tu deployment] → Functions
