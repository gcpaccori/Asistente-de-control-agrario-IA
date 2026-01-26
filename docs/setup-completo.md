# Configuración Completa Paso a Paso

Esta guía te lleva desde cero hasta tener el sistema funcionando en Vercel.

## Pre-requisitos

- [ ] Cuenta GitHub (para alojar el código)
- [ ] Cuenta Vercel (gratis en https://vercel.com/signup)
- [ ] API key de un proveedor LLM (Grok, OpenAI, etc.)
- [ ] WhatsApp en tu teléfono

## Paso 1: Preparar el Repositorio

```bash
# Clonar el repositorio (si aún no lo has hecho)
git clone https://github.com/gcpaccori/Asistente-de-control-agrario-IA
cd Asistente-de-control-agrario-IA

# Verificar que todo está listo
python3 verify_vercel_setup.py
```

Deberías ver ✅ en todos los checks.

## Paso 2: Configurar el Modelo de Lenguaje (Parte 3)

Tienes dos opciones:

### Opción A: Usar Grok (xAI) - Recomendado

1. Ve a https://console.x.ai/
2. Crea una API key
3. Guarda la API key para el siguiente paso

### Opción B: Usar tu Propio Modelo Local

Si tienes un servidor con suficiente memoria:

```bash
# En tu servidor
pip install -r requirements.txt

# Descargar modelo
mkdir -p models
wget -O models/qwen2.5-3b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf

# Opción 1: Ejecutar model_api.py (modelo GGUF)
python3 model_api.py

# Opción 2: Ejecutar llm_adapter.py (API externa como Grok)
export MML_PROVIDER=xai
export XAI_API_KEY=tu_api_key_aqui
python3 llm_adapter.py
```

Tu API estará disponible en `http://tu-servidor:8001`

## Paso 3: Desplegar Backend en Vercel (Parte 2)

### 3.1: Instalar Vercel CLI

```bash
npm install -g vercel
```

### 3.2: Login en Vercel

```bash
vercel login
```

Sigue las instrucciones en el navegador.

### 3.3: Configurar Variables de Entorno

Antes de desplegar, configura las variables de entorno. Hay dos formas:

#### Forma A: Durante el deploy (CLI)

El CLI de Vercel te preguntará por las variables de entorno.

#### Forma B: En el Dashboard (Recomendado)

1. Ve a https://vercel.com/new
2. Importa tu repositorio de GitHub
3. En "Environment Variables", agrega:

```
MODEL_API_URL=https://api.x.ai/v1  (o tu URL del modelo)
MML_PROVIDER=xai
XAI_API_KEY=tu_api_key_aqui
XAI_MODEL=grok-4-latest
```

**IMPORTANTE:** Si usas Grok directamente desde Vercel, necesitas que `app.py` haga las llamadas a Grok. 

**ALTERNATIVA:** Si desplegaste `llm_adapter.py` en otro servidor:
```
MODEL_API_URL=https://tu-servidor.com:8001
```

### 3.4: Desplegar

```bash
# Desde la raíz del proyecto
vercel

# O para producción directamente
vercel --prod
```

Vercel te dará una URL como: `https://tu-proyecto.vercel.app`

### 3.5: Verificar

```bash
curl https://tu-proyecto.vercel.app/health
```

Deberías ver:
```json
{"status": "ok", "time": "2026-01-26T..."}
```

## Paso 4: Configurar Productores Autorizados

1. Abre tu navegador en: `https://tu-proyecto.vercel.app/admin`
2. Ve a "Productores"
3. Agrega un nuevo productor:
   - **Teléfono**: +51999999999 (formato internacional con +)
   - **Nombre**: Nombre del productor
   - **Zona**: Zona agrícola
   - **Idioma**: es (español)
   - **Cultivos**: maíz, papa, etc.
   - **Autorizado**: ✅ Sí (importante!)
   - **Rol asignado**: formulario (o el que prefieras)

## Paso 5: Configurar Puente WhatsApp (Parte 1)

### 5.1: Instalar Dependencias Node.js

```bash
cd whatsapp
npm install
```

### 5.2: Configurar URL del Backend

```bash
# En Linux/Mac
export FLASK_URL="https://tu-proyecto.vercel.app"

# En Windows (PowerShell)
$env:FLASK_URL="https://tu-proyecto.vercel.app"

# Opcional: Configurar rol por defecto
export DEFAULT_ROLE="formulario"
```

### 5.3: Iniciar el Puente WhatsApp

```bash
npm start
```

### 5.4: Escanear QR Code

1. Abre WhatsApp en tu teléfono
2. Ve a Configuración → Dispositivos vinculados
3. Toca "Vincular un dispositivo"
4. Escanea el QR que aparece en la terminal

Deberías ver: "WhatsApp bridge listo."

## Paso 6: ¡Probar el Sistema!

1. Desde otro teléfono, envía un mensaje de WhatsApp al número que vinculaste
2. El mensaje debe:
   - Llegar al puente WhatsApp
   - Enviarse a Vercel
   - Procesarse por el agente IA
   - Responder automáticamente

**Ejemplo de conversación:**
```
Usuario: Hola
Bot: ¡Hola! Soy tu asistente agrónomo. ¿En qué puedo ayudarte?

Usuario: Tengo un problema con mis plantas de tomate
Bot: Entiendo. ¿Podrías describir qué está pasando con tus plantas?
```

## Solución de Problemas

### Error: "403 Forbidden" en /agent

→ El productor no está autorizado. Ve a `/admin/producers` y marca como autorizado.

### Error: "llama-cpp-python no está instalado"

→ No configuraste `MODEL_API_URL` en Vercel. Ve a Settings → Environment Variables.

### Error: "Cannot connect to Vercel"

→ Verifica que `FLASK_URL` esté correctamente configurado en el paso 5.2.

### WhatsApp no responde

→ Verifica:
1. QR escaneado correctamente
2. Terminal del puente WhatsApp activa
3. Productor autorizado en `/admin`
4. Logs en la terminal para ver errores

## Monitoreo

### Ver logs del Backend (Vercel)

1. Ve a https://vercel.com/dashboard
2. Selecciona tu proyecto
3. Ve a "Deployments" → [último deployment] → "Functions"
4. Click en cualquier función para ver logs

### Ver logs del Puente WhatsApp

Los logs aparecen en la terminal donde ejecutaste `npm start`.

## Próximos Pasos

1. **Configurar los 3 roles** en `/admin/agents`:
   - formulario: Para recolectar información
   - consulta: Para responder preguntas
   - intervencion: Para detectar problemas críticos

2. **Personalizar prompts** según tu caso de uso

3. **Agregar más productores** autorizados

4. **Revisar formularios** en `/admin/forms`

5. **Monitorear alertas** en `/admin/alerts`

## Arquitectura Final

```
[WhatsApp] 
    ↓ (local/servidor)
[Puente Node.js]
    ↓ HTTPS
[Vercel - Flask API]
    ↓ HTTPS
[API LLM - Grok/OpenAI/Local]
```

¡Listo! Tu sistema está funcionando. 🎉

## Costos Estimados

- **Vercel**: Gratis (plan Hobby) o $20/mes (Pro)
- **Puente WhatsApp**: Gratis (tu conexión + servidor/local)
- **API LLM**: 
  - Grok: ~$5/millón de tokens
  - OpenAI: ~$10-30/millón de tokens (según modelo)
  - Local: Gratis (requiere hardware)

## Soporte

¿Problemas? Revisa:
- [Arquitectura de 3 partes](./arquitectura-3-partes.md)
- [Guía de Vercel](./vercel-deployment.md)
- [Inicio rápido](./vercel-quickstart.md)
