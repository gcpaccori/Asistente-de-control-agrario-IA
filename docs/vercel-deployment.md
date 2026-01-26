# Guía de Deployment en Vercel

Esta guía explica cómo desplegar el sistema completo en Vercel.

## Arquitectura del Sistema

El sistema tiene **tres partes**:

1. **Backend Flask (Python)** - `app.py`
   - API principal del sistema
   - Gestión de base de datos SQLite
   - Orquestación de agentes con roles
   - Panel de administración web

2. **Puente WhatsApp (Node.js)** - `whatsapp/`
   - Servicio Node.js para integración con WhatsApp
   - Se ejecuta localmente o en un servidor separado
   - Se conecta con el backend Flask

3. **Modelo de Lenguaje (LLM)**
   - Opción A: Modelo local GGUF (solo para desarrollo local)
   - Opción B: API externa (requerido para Vercel)

## Deployment en Vercel

### Prerequisitos

1. Cuenta en Vercel (https://vercel.com)
2. Acceso a una API de modelo de lenguaje (Grok, OpenAI, etc.)
3. Repositorio Git conectado a Vercel

### Paso 1: Configurar Variables de Entorno en Vercel

En el dashboard de Vercel, configura las siguientes variables de entorno:

```bash
# REQUERIDO: URL de la API del modelo de lenguaje
MODEL_API_URL=https://tu-modelo-api.com

# OPCIONAL: Configuración del modelo (si usas una API externa)
MML_PROVIDER=xai
XAI_API_KEY=tu_api_key_aqui
XAI_MODEL=grok-4-latest

# OPCIONAL: Zona horaria por defecto
DEFAULT_TIMEZONE=America/Lima

# OPCIONAL: Configuración de check-in diario
DAILY_CHECKIN_HOUR=8
```

**IMPORTANTE**: No configures `LOCAL_MODEL_PATH`, `N_CTX`, o `N_THREADS` en Vercel, ya que no se usan modelos locales en el deployment.

### Paso 2: Desplegar en Vercel

#### Opción A: Desde el CLI de Vercel

```bash
# Instalar Vercel CLI
npm i -g vercel

# Desplegar
cd /ruta/a/tu/proyecto
vercel
```

#### Opción B: Desde el Dashboard de Vercel

1. Ve a https://vercel.com/dashboard
2. Click en "Import Project"
3. Selecciona tu repositorio de GitHub
4. Vercel detectará automáticamente la configuración de Python
5. Click en "Deploy"

### Paso 3: Verificar el Deployment

Una vez desplegado, verifica que funciona:

```bash
# Verifica la salud del servicio
curl https://tu-proyecto.vercel.app/health

# Debería responder:
# {"status": "ok"}
```

### Paso 4: Configurar el Puente WhatsApp

El puente WhatsApp se ejecuta **localmente** o en un servidor separado (no en Vercel).

1. En tu máquina local o servidor, configura la variable de entorno:

```bash
export FLASK_URL="https://tu-proyecto.vercel.app"
```

2. Ejecuta el puente WhatsApp:

```bash
cd whatsapp
npm install
npm start
```

3. Escanea el código QR con WhatsApp

## Configuración de la Base de Datos

Vercel serverless functions tienen un sistema de archivos efímero. Para persistir datos, considera:

### Opción A: SQLite en Vercel (limitado)
- Los datos persisten entre invocaciones en el mismo "cold start"
- Se pierden cuando la función se reinicia
- Útil para desarrollo/pruebas

### Opción B: Base de Datos Externa (recomendado para producción)
- PostgreSQL (Vercel Postgres, Supabase, Railway)
- MySQL (PlanetScale)
- MongoDB Atlas

Para migrar a PostgreSQL:
1. Instala psycopg2: `pip install psycopg2-binary`
2. Actualiza `app.py` para usar PostgreSQL en lugar de SQLite
3. Configura `DATABASE_URL` en variables de entorno de Vercel

## Estructura de Archivos para Vercel

```
.
├── api/
│   └── index.py          # Entry point para Vercel serverless
├── app.py                # Aplicación Flask principal
├── requirements.txt      # Dependencias Python
├── vercel.json           # Configuración de Vercel
├── .vercelignore        # Archivos a ignorar en deployment
├── whatsapp/            # Puente WhatsApp (no se despliega en Vercel)
│   ├── index.js
│   └── package.json
└── templates/           # Templates HTML de Flask
```

## API del Modelo de Lenguaje

Para Vercel, debes usar una API externa de modelo de lenguaje. El sistema espera:

**Endpoint:** `POST /chat`

**Request:**
```json
{
  "system": "prompt del sistema",
  "context": {
    "mensaje": "contenido",
    "productor": {...}
  },
  "max_tokens": 300
}
```

**Response:**
```json
{
  "content": "{\"role\":\"formulario\",\"respuesta_chat\":\"...\", ...}"
}
```

## Limitaciones en Vercel

1. **No se pueden usar modelos GGUF locales** - Las serverless functions de Vercel tienen límites de memoria y CPU
2. **Sistema de archivos efímero** - Los archivos no persisten entre invocaciones
3. **Timeout de 10 segundos** (plan gratuito) o 60 segundos (plan pro)
4. **Tamaño de deployment limitado** - Máximo 50MB comprimido

## Troubleshooting

### Error: "llama-cpp-python no está instalado"
- Asegúrate de configurar `MODEL_API_URL` en las variables de entorno de Vercel
- El sistema detectará automáticamente que debe usar la API en lugar del modelo local

### Error: "Database is locked"
- SQLite no es ideal para serverless functions concurrentes
- Considera migrar a PostgreSQL para producción

### Error: "Timeout"
- Las llamadas al modelo de lenguaje deben completarse en menos de 60 segundos
- Ajusta `max_tokens` para respuestas más rápidas

## Desarrollo Local vs Producción

### Desarrollo Local
```bash
# Usar modelo GGUF local
python app.py

# O usar API externa
export MODEL_API_URL="https://tu-api.com"
python app.py
```

### Producción en Vercel
```bash
# Siempre usa API externa
# Configura MODEL_API_URL en variables de entorno de Vercel
vercel deploy --prod
```

## Monitoreo

Vercel proporciona:
- Logs en tiempo real
- Métricas de uso
- Alertas de errores

Accede al dashboard: https://vercel.com/dashboard

## Costos

- **Plan Hobby**: Gratis para proyectos personales
- **Plan Pro**: $20/mes para uso comercial
- Ten en cuenta los costos de la API del modelo de lenguaje

## Próximos Pasos

1. [ ] Desplegar en Vercel
2. [ ] Configurar variables de entorno
3. [ ] Probar el endpoint `/health`
4. [ ] Conectar el puente WhatsApp
5. [ ] Probar el flujo completo
6. [ ] Considerar migración a PostgreSQL para producción

## Soporte

Para más información:
- Documentación de Vercel: https://vercel.com/docs
- Repositorio del proyecto: GitHub
