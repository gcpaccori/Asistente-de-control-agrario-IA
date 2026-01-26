# Diagrama de Arquitectura del Sistema

## Vista General

```
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO FINAL                         │
│                         (WhatsApp)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Mensajes
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    PARTE 1: PUENTE LOCAL                      │
│                                                               │
│  Tecnología: Node.js + whatsapp-web.js                       │
│  Ubicación:  Tu máquina local o servidor VPS                 │
│  Puerto:     -                                                │
│  Archivos:   whatsapp/index.js, whatsapp/package.json        │
│                                                               │
│  ┌─────────────────────────────────────────────────┐         │
│  │  • Recibe mensajes de WhatsApp                  │         │
│  │  • Envía al backend Flask en Vercel             │         │
│  │  • Devuelve respuestas al usuario               │         │
│  │  • Gestiona sesión de WhatsApp                  │         │
│  └─────────────────────────────────────────────────┘         │
│                                                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS (POST /agent)
                         │ FLASK_URL env var
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 PARTE 2: BACKEND EN VERCEL                    │
│                                                               │
│  Tecnología: Python + Flask (Serverless)                     │
│  Ubicación:  Vercel Cloud                                    │
│  URL:        https://tu-proyecto.vercel.app                  │
│  Archivos:   api/index.py, app.py, templates/               │
│                                                               │
│  ┌─────────────────────────────────────────────────┐         │
│  │  ENDPOINTS:                                      │         │
│  │  • POST /agent       - Procesar mensajes        │         │
│  │  • GET  /health      - Health check             │         │
│  │  • GET  /admin       - Panel de administración  │         │
│  │  • POST /form/update - Actualizar formularios   │         │
│  │  • POST /alert       - Crear alertas            │         │
│  │                                                  │         │
│  │  COMPONENTES:                                    │         │
│  │  • Orquestador de agentes (3 roles)            │         │
│  │  • Base de datos SQLite                         │         │
│  │  • Gestión de contexto                          │         │
│  │  • Sistema de bitácoras                         │         │
│  │  • Gestión de alertas                           │         │
│  └─────────────────────────────────────────────────┘         │
│                                                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS (POST /chat)
                         │ MODEL_API_URL env var
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              PARTE 3: API DE MODELO DE LENGUAJE               │
│                                                               │
│  Opciones:                                                    │
│  ┌──────────────────────────────────────────────┐            │
│  │ A) API Comercial (Recomendado)              │            │
│  │    • Grok (xAI)                              │            │
│  │    • OpenAI (GPT-4)                          │            │
│  │    • Anthropic (Claude)                      │            │
│  │    • Google (Gemini)                         │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │ B) Modelo Local (Desarrollo)                 │            │
│  │    • llm_adapter.py (API wrapper)            │            │
│  │    • model_api.py (GGUF local)               │            │
│  │    Tu servidor: http://servidor:8001         │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  Endpoint requerido: POST /chat                              │
│  ┌─────────────────────────────────────────────────┐         │
│  │  Request:                                        │         │
│  │  {                                               │         │
│  │    "system": "prompt del sistema",              │         │
│  │    "context": {...},                            │         │
│  │    "max_tokens": 300                            │         │
│  │  }                                               │         │
│  │                                                  │         │
│  │  Response:                                       │         │
│  │  {                                               │         │
│  │    "content": "JSON con respuesta"              │         │
│  │  }                                               │         │
│  └─────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Flujo de Mensajes Detallado

```
1. Usuario envía mensaje por WhatsApp
   "Hola, necesito ayuda con mis plantas"
                │
                ↓
2. Puente WhatsApp recibe mensaje
   phone: +51999999999
   message: "Hola, necesito ayuda con mis plantas"
                │
                ↓
3. Puente envía a Vercel (POST /agent)
   {
     "phone": "+51999999999",
     "message": "Hola, necesito ayuda con mis plantas",
     "role": "formulario"  // opcional
   }
                │
                ↓
4. Backend Flask en Vercel procesa:
   a) Valida que el productor esté autorizado
   b) Determina el rol del agente
   c) Construye contexto con:
      - Historial reciente
      - Estado del formulario
      - Tareas activas
      - Bitácoras diarias
   d) Llama a API del modelo
                │
                ↓
5. API del Modelo genera respuesta
   Input: system prompt + context
   Output: JSON con:
   {
     "role": "formulario",
     "respuesta_chat": "¡Hola! Estoy aquí para ayudarte...",
     "acciones": {
       "actualizar_formulario": {...},
       "log": "Productor inició conversación",
       "alerta": null
     },
     "estado": {
       "formulario_completo": false,
       "confianza": 0.9
     }
   }
                │
                ↓
6. Backend Flask procesa respuesta:
   a) Actualiza formulario si es necesario
   b) Registra en bitácora
   c) Crea alertas si aplica
   d) Guarda mensaje en historial
                │
                ↓
7. Backend devuelve respuesta al Puente
   {
     "model_output": {
       "respuesta_chat": "¡Hola! Estoy aquí para ayudarte..."
     }
   }
                │
                ↓
8. Puente WhatsApp envía respuesta al usuario
   "¡Hola! Estoy aquí para ayudarte..."
```

## Base de Datos (SQLite)

```
┌─────────────────────────────────────────────────────────────┐
│                    instance/app.db (SQLite)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Tablas:                                                      │
│  ┌────────────────────────────────────────────┐              │
│  │ producers                                  │              │
│  │  - id, phone, name, zone, allowed, ...    │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  ┌────────────────────────────────────────────┐              │
│  │ forms                                      │              │
│  │  - id, producer_id, data (JSON), ...      │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  ┌────────────────────────────────────────────┐              │
│  │ chat_history                               │              │
│  │  - id, producer_id, role, message, ...    │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  ┌────────────────────────────────────────────┐              │
│  │ alerts                                     │              │
│  │  - id, producer_id, message, status, ...  │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  ┌────────────────────────────────────────────┐              │
│  │ daily_logs                                 │              │
│  │  - id, producer_id, date, activities, ... │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  ┌────────────────────────────────────────────┐              │
│  │ tasks                                      │              │
│  │  - id, producer_id, title, status, ...    │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Sistema de 3 Roles

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTES CON ROLES                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Rol 1: FORMULARIO                                           │
│  ┌────────────────────────────────────────────┐              │
│  │ • Recolecta información del productor      │              │
│  │ • Hace preguntas naturales                 │              │
│  │ • Completa formulario paso a paso          │              │
│  │ • Registra bitácora diaria                 │              │
│  │ • Actualiza tareas                         │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  Rol 2: CONSULTA                                             │
│  ┌────────────────────────────────────────────┐              │
│  │ • Responde preguntas técnicas              │              │
│  │ • Usa información del contexto             │              │
│  │ • Pide aclaraciones cuando es necesario    │              │
│  │ • Orienta al productor                     │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
│  Rol 3: INTERVENCIÓN                                         │
│  ┌────────────────────────────────────────────┐              │
│  │ • Analiza problemas persistentes           │              │
│  │ • Detecta riesgos                          │              │
│  │ • Genera alertas para técnicos             │              │
│  │ • Escala casos críticos                    │              │
│  └────────────────────────────────────────────┘              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Variables de Entorno

```
┌──────────────────────────────────────────────────────┐
│  PARTE 1 (Puente WhatsApp)                           │
├──────────────────────────────────────────────────────┤
│  FLASK_URL=https://tu-proyecto.vercel.app            │
│  DEFAULT_ROLE=formulario  (opcional)                 │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  PARTE 2 (Backend Vercel)                            │
├──────────────────────────────────────────────────────┤
│  MODEL_API_URL=https://api.x.ai/v1  (REQUERIDO)     │
│  MML_PROVIDER=xai                                    │
│  XAI_API_KEY=tu_api_key_aqui                         │
│  XAI_MODEL=grok-4-latest                             │
│  DEFAULT_TIMEZONE=America/Lima                       │
│  DAILY_CHECKIN_HOUR=8                                │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  PARTE 3 (Modelo Local - Opcional)                   │
├──────────────────────────────────────────────────────┤
│  LOCAL_MODEL_PATH=models/qwen2.5-3b-...gguf         │
│  N_CTX=2048                                          │
│  N_THREADS=1                                         │
│  MML_PROVIDER=xai  (si usas llm_adapter.py)         │
│  XAI_API_KEY=...                                     │
└──────────────────────────────────────────────────────┘
```

## Archivos Importantes

```
Asistente-de-control-agrario-IA/
│
├── api/
│   └── index.py              # Entry point para Vercel
│
├── app.py                    # Backend Flask principal
├── model_api.py              # API para modelo GGUF local
├── llm_adapter.py            # Adaptador para APIs comerciales
├── verify_vercel_setup.py   # Script de verificación
│
├── whatsapp/
│   ├── index.js              # Puente WhatsApp
│   └── package.json          # Dependencias Node.js
│
├── templates/                # Templates HTML para /admin
│   ├── dashboard.html
│   ├── producers.html
│   └── ...
│
├── docs/
│   ├── setup-completo.md         # Guía completa de setup
│   ├── arquitectura-3-partes.md  # Explicación de arquitectura
│   ├── vercel-deployment.md      # Guía detallada de Vercel
│   ├── vercel-quickstart.md      # Inicio rápido
│   ├── diagrama-arquitectura.md  # Este archivo
│   └── contrato-mml.md           # Contrato JSON del modelo
│
├── vercel.json               # Configuración de Vercel
├── .vercelignore            # Archivos a ignorar
├── requirements.txt          # Dependencias Python
├── .env.example             # Ejemplo de variables de entorno
└── README.md                # Documentación principal
```

---

**Última actualización:** 2026-01-26
