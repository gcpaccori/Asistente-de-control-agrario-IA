# 📊 Diagrama de Arquitectura

## Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    USUARIO FINAL (WhatsApp)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ mensaje: "¿Cuándo riego?"
                             ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  SERVICIO 3: WhatsApp Bridge (Node.js)                          ┃
┃  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ┃
┃  Plataforma: Railway / Render / VPS                             ┃
┃  Tipo: PERSISTENTE 24/7 ⚠️                                      ┃
┃  Puerto: 3000                                                    ┃
┃                                                                  ┃
┃  Componentes:                                                    ┃
┃  • whatsapp-web.js (mantiene sesión activa)                     ┃
┃  • Navegador Chromium (en background)                           ┃
┃  • .wwebjs_auth/ (archivos de sesión)                          ┃
┃  • Polling de alertas cada 10s                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              │
                              │ POST /agent
                              │ {phone, message, role}
                              ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  SERVICIO 2: Backend Principal (Flask)                          ┃
┃  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ┃
┃  Plataforma: Leapcell (serverless) ✅                           ┃
┃  Puerto: 5000                                                    ┃
┃                                                                  ┃
┃  Componentes:                                                    ┃
┃  • API REST (/agent, /form/update, /alert)                     ┃
┃  • Base de datos SQLite (volumen persistente)                   ┃
┃  • Panel Admin Web (/admin)                                     ┃
┃  • Orquestador de contexto                                      ┃
┃  • Gestión de productores, formularios, alertas                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              │
                              │ POST /chat
                              │ {system, context, max_tokens}
                              ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  SERVICIO 1: Model API (Flask + LLM)                            ┃
┃  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ┃
┃  Plataforma: Leapcell (serverless) ✅                           ┃
┃  Puerto: 8001                                                    ┃
┃                                                                  ┃
┃  Componentes:                                                    ┃
┃  • llama-cpp-python                                             ┃
┃  • Modelo GGUF (Qwen 2.5B 3B, ~3-4 GB)                         ┃
┃  • Inferencia LLM                                               ┃
┃  • Respuesta JSON estructurada                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              │
                              │ JSON response
                              │ {content: "{role, respuesta_chat, ...}"}
                              ▼
                    ┌─────────────────────┐
                    │  Servicio 2         │
                    │  • Parsea JSON      │
                    │  • Actualiza DB     │
                    │  • Guarda historial │
                    └─────────┬───────────┘
                              │
                              │ JSON response
                              │ {model_output: {...}}
                              ▼
                    ┌─────────────────────┐
                    │  Servicio 3         │
                    │  • Extrae texto     │
                    │  • Envía WhatsApp   │
                    └─────────┬───────────┘
                              │
                              │ mensaje: "Debes regar mañana..."
                              ▼
                    ┌─────────────────────┐
                    │  Usuario WhatsApp   │
                    │  Recibe respuesta   │
                    └─────────────────────┘
```

## Comunicación Entre Servicios

### 1. WhatsApp → Backend
```http
POST https://backend-xxx.leapcell.dev/agent
Content-Type: application/json

{
  "phone": "51987654321@c.us",
  "message": "¿Cuándo debo regar?",
  "role": "consulta"
}

→ Response:
{
  "model_output": {
    "role": "consulta",
    "respuesta_chat": "Según tu cultivo de maíz...",
    "acciones": {...},
    "estado": {...}
  }
}
```

### 2. Backend → Model API
```http
POST https://model-api-xxx.leapcell.dev/chat
Content-Type: application/json

{
  "system": "Responde usando SOLO la información del contexto...",
  "context": {
    "mensaje": "¿Cuándo debo regar?",
    "productor": {...},
    "historial": [...]
  },
  "max_tokens": 300
}

→ Response:
{
  "content": "{\"role\":\"consulta\",\"respuesta_chat\":\"...\"}"
}
```

### 3. Backend → WhatsApp (Alertas)
```http
GET https://backend-xxx.leapcell.dev/alerts/pending

→ Response:
{
  "alerts": [
    {
      "id": 1,
      "phone": "51987654321@c.us",
      "message": "Alerta: Posible plaga detectada",
      "level": "alta"
    }
  ]
}

POST https://backend-xxx.leapcell.dev/alerts/1/sent
```

## Ventajas de esta Arquitectura

### ✅ Separación de Responsabilidades
- **Servicio 1**: Solo inferencia LLM (puede cambiar modelo sin afectar otros)
- **Servicio 2**: Lógica de negocio y datos (puede escalar independiente)
- **Servicio 3**: Solo comunicación WhatsApp (fácil reemplazar con Telegram, etc)

### ✅ Escalabilidad
- Servicio 1 y 2 escalan automáticamente (serverless)
- Servicio 3 puede replicarse para múltiples números

### ✅ Costos Optimizados
- Serverless = paga por uso (Servicio 1 y 2)
- Persistente solo donde es necesario (Servicio 3)

### ✅ Mantenibilidad
- Cada servicio es independiente
- Se pueden actualizar/desplegar por separado
- Fácil debug (logs por servicio)

## Limitaciones y Consideraciones

### ⚠️ Cold Starts
- **Servicio 1**: Primera request puede tardar 5-30s (carga modelo)
- **Solución**: Keep-alive o usar instancia persistente

### ⚠️ Tamaño del Modelo
- Modelo GGUF ocupa 3-4 GB
- Requiere mínimo 2 GB RAM para inferencia
- Considerar modelos más pequeños si hay problemas

### ⚠️ SQLite en Serverless
- Funciona con volumen persistente
- Con alta concurrencia puede haber locks
- Migrar a PostgreSQL si crece

### ⚠️ WhatsApp No Oficial
- whatsapp-web.js puede violar TOS
- Para producción seria: WhatsApp Business API

## Alternativas de Plataforma

| Servicio | Plataforma Primaria | Alternativas |
|----------|---------------------|--------------|
| Servicio 1 | Leapcell | Railway, Render, Fly.io |
| Servicio 2 | Leapcell | Railway, Render, Heroku |
| Servicio 3 | Railway | Render, Fly.io, VPS, DigitalOcean |

## Resumen Visual de Despliegue

```
┌─────────────────────────────────────────────────────────────┐
│  PLATAFORMAS DE DESPLIEGUE                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔵 LEAPCELL (Serverless)                                  │
│     ├─ Servicio 1: Model API                               │
│     │  URL: https://model-api-xxx.leapcell.dev            │
│     │  RAM: 2-4 GB                                         │
│     │  Storage: Volumen 5 GB (modelo GGUF)                │
│     │                                                       │
│     └─ Servicio 2: Backend                                 │
│        URL: https://backend-xxx.leapcell.dev               │
│        RAM: 512 MB - 1 GB                                  │
│        Storage: Volumen 1 GB (SQLite)                      │
│                                                             │
│  🟣 RAILWAY (Persistente)                                  │
│     └─ Servicio 3: WhatsApp                                │
│        URL: https://whatsapp-xxx.railway.app               │
│        RAM: 512 MB                                         │
│        Storage: 1 GB (.wwebjs_auth/)                      │
│        Uptime: 24/7 ⚠️                                     │
│                                                             │
│  💰 COSTO TOTAL: ~$5-15/mes                                │
└─────────────────────────────────────────────────────────────┘
```

## Próximos Pasos

1. ✅ Seguir `DEPLOYMENT_GUIDE.md` paso a paso
2. ✅ Desplegar en orden: Servicio 1 → 2 → 3
3. ✅ Probar cada servicio independientemente
4. ✅ Configurar productores en panel admin
5. ✅ Escanear QR de WhatsApp
6. ✅ Enviar mensaje de prueba
7. ✅ Monitorear logs y métricas

¡Tu arquitectura de 3 servicios estará funcionando! 🚀
