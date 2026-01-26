# Sistema Completo de 3 Partes

Este documento resume las **3 partes del sistema** y cómo ejecutarlas.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────┐
│  Parte 1: LOCAL     │
│  WhatsApp Bridge    │
│  (Node.js)          │
└──────────┬──────────┘
           │ HTTP
           ↓
┌─────────────────────┐
│  Parte 2: VERCEL    │
│  Backend Flask      │
│  (Python Serverless)│
└──────────┬──────────┘
           │ HTTP
           ↓
┌─────────────────────┐
│  Parte 3: API       │
│  Modelo de Lenguaje │
│  (Grok/OpenAI/etc.) │
└─────────────────────┘
```

## Parte 1: Puente WhatsApp (Local/Servidor)

**Tecnología:** Node.js + whatsapp-web.js

**Ubicación:** Se ejecuta en tu máquina local o un servidor VPS

**Requisitos:**
- Node.js 18+
- Acceso a internet
- Navegador para escanear QR de WhatsApp

**Setup:**
```bash
cd whatsapp
npm install

# Configurar URL del backend (Vercel)
export FLASK_URL="https://tu-proyecto.vercel.app"

# Ejecutar
npm start
```

**¿Qué hace?**
- Recibe mensajes de WhatsApp
- Envía al backend Flask en Vercel
- Responde al usuario con la respuesta del agente IA

## Parte 2: Backend Flask (Vercel)

**Tecnología:** Python + Flask (Serverless)

**Ubicación:** Desplegado en Vercel

**Requisitos:**
- Cuenta en Vercel
- Variable de entorno `MODEL_API_URL` configurada

**Setup:**
```bash
# Instalar CLI de Vercel
npm i -g vercel

# Desplegar
vercel

# O conecta tu repo en https://vercel.com/new
```

**Variables de entorno requeridas en Vercel:**
```bash
MODEL_API_URL=https://tu-api-del-modelo.com
```

**¿Qué hace?**
- API REST para recibir mensajes
- Orquesta agentes IA con 3 roles
- Gestiona base de datos de productores
- Panel de administración web
- Endpoints: `/agent`, `/health`, `/admin`, etc.

## Parte 3: API de Modelo de Lenguaje

**Tecnología:** API externa (Grok, OpenAI, u otro)

**Ubicación:** Proveedor externo o tu propio servidor

**Opciones:**

### Opción A: Usar model_api.py (Local)

Si quieres hostear tu propio modelo:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo GGUF
mkdir -p models
wget -O models/qwen2.5-3b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf

# Ejecutar API
export LOCAL_MODEL_PATH=models/qwen2.5-3b-instruct-q4_k_m.gguf
python model_api.py
```

Luego en Vercel, configura:
```bash
MODEL_API_URL=https://tu-servidor.com:8001
```

### Opción B: Usar API comercial (Recomendado)

Usa un proveedor como:
- **Grok (xAI)**: https://console.x.ai/
- **OpenAI**: https://platform.openai.com/
- **Anthropic Claude**: https://www.anthropic.com/
- **Google Gemini**: https://ai.google.dev/

Necesitas adaptar el código para que funcione con la API específica del proveedor.

## 🚀 Flujo Completo

1. **Usuario** envía mensaje por WhatsApp
   ↓
2. **Puente WhatsApp** (Parte 1) recibe el mensaje
   ↓
3. **Backend Flask en Vercel** (Parte 2) procesa:
   - Identifica al productor
   - Determina el rol del agente
   - Construye el contexto
   ↓
4. **API de Modelo** (Parte 3) genera respuesta IA
   ↓
5. **Backend Flask** procesa la respuesta:
   - Actualiza formulario si es necesario
   - Registra en bitácora
   - Genera alertas si aplica
   ↓
6. **Puente WhatsApp** envía respuesta al usuario

## 📋 Checklist de Deployment

### ✅ Parte 1 (WhatsApp)
- [ ] Node.js instalado
- [ ] `cd whatsapp && npm install`
- [ ] Variable `FLASK_URL` configurada
- [ ] QR de WhatsApp escaneado

### ✅ Parte 2 (Vercel)
- [ ] Cuenta en Vercel creada
- [ ] Repositorio conectado
- [ ] `MODEL_API_URL` configurada en variables de entorno
- [ ] Deployment exitoso
- [ ] `/health` endpoint respondiendo

### ✅ Parte 3 (Modelo)
- [ ] API de modelo elegida
- [ ] Credenciales configuradas
- [ ] Endpoint `/chat` disponible
- [ ] Prueba de respuesta JSON exitosa

## 🧪 Verificación

Ejecuta el script de verificación:

```bash
python verify_vercel_setup.py
```

## 📚 Documentación Adicional

- [Guía de inicio rápido para Vercel](./vercel-quickstart.md)
- [Guía completa de deployment](./vercel-deployment.md)
- [Contrato MML](./contrato-mml.md)
- [README principal](../README.md)

## ❓ Preguntas Frecuentes

### ¿Puedo ejecutar todo localmente?

Sí, para desarrollo:
```bash
# Terminal 1: Backend Flask
python app.py

# Terminal 2: WhatsApp
cd whatsapp
export FLASK_URL="http://localhost:5000"
npm start

# Terminal 3 (opcional): Modelo local
python model_api.py
```

### ¿Cuánto cuesta?

- **Parte 1 (WhatsApp)**: Gratis (usa tu WhatsApp personal)
- **Parte 2 (Vercel)**: Gratis en plan Hobby
- **Parte 3 (Modelo)**: Depende del proveedor
  - Modelo local: Gratis (requiere hardware)
  - APIs comerciales: ~$0.001-0.01 por mensaje

### ¿Es seguro usar whatsapp-web.js?

Para MVP y pruebas sí. Para producción, migra a WhatsApp Business API oficial.

### ¿Puedo usar PostgreSQL en vez de SQLite?

Sí, es recomendado para producción. Necesitas modificar `app.py` para usar PostgreSQL en lugar de SQLite.

## 🆘 Soporte

Si tienes problemas:
1. Ejecuta `python verify_vercel_setup.py`
2. Revisa logs en Vercel Dashboard
3. Verifica variables de entorno
4. Consulta la documentación completa

---

**Última actualización:** 2026-01-26
