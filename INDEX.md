# 📚 Índice de Documentación - Arquitectura de 3 Servicios

## 🎯 Empezar Aquí

¿Primera vez? Sigue este orden:

1. **[FAQ.md](docs/FAQ.md)** ← **EMPIEZA AQUÍ**
   - Responde todas tus preguntas
   - ¿Puedo usar solo Leapcell? ¿Necesito Next.js? etc.

2. **[QUICK_START.md](QUICK_START.md)**
   - Resumen de 2 minutos
   - Checklist visual

3. **[COMO_EJECUTAR.md](COMO_EJECUTAR.md)** ← **¿Cómo ejecutar el proyecto?**
   - Comandos BUILD y START
   - Guía completa de ejecución local

4. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**
   - Guía paso a paso para desplegar
   - Configuración completa

---

## 🚀 Ejecución Rápida (Desarrollo Local)

| Documento | Descripción |
|-----------|-------------|
| [COMO_EJECUTAR.md](COMO_EJECUTAR.md) | **Guía completa de comandos BUILD y START** |
| [COMANDOS.md](COMANDOS.md) | **Referencia rápida de todos los comandos** |

### Comandos Rápidos:
```bash
# BUILD: Instalar dependencias
pip install -r requirements.txt
# o: npm run install:python
# o: make build

# START: Ejecutar servidor
python app.py
# o: npm start
# o: ./start.sh
# o: make start
```

📖 Ver [COMANDOS.md](COMANDOS.md) para tabla completa de comandos.

---

## 📖 Documentación Completa

### Conceptos y Arquitectura

| Documento | Descripción | Cuándo Leer |
|-----------|-------------|-------------|
| [docs/FAQ.md](docs/FAQ.md) | Preguntas frecuentes | Antes de empezar |
| [docs/ARQUITECTURA_DESPLIEGUE.md](docs/ARQUITECTURA_DESPLIEGUE.md) | Explicación detallada de por qué 3 servicios | Para entender el diseño |
| [docs/DIAGRAMA_ARQUITECTURA.md](docs/DIAGRAMA_ARQUITECTURA.md) | Diagramas visuales y flujos | Para visualizar |

### Guías Prácticas

| Documento | Descripción | Cuándo Leer |
|-----------|-------------|-------------|
| [QUICK_START.md](QUICK_START.md) | Inicio rápido | Para resumen ejecutivo |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Despliegue paso a paso | Al desplegar |

### Documentación por Servicio

| Servicio | README | Contenido |
|----------|--------|-----------|
| **Servicio 1** | [service-1-model/README.md](service-1-model/README.md) | Model API (Flask + LLM) |
| **Servicio 2** | [service-2-backend/README.md](service-2-backend/README.md) | Backend Principal (Flask + DB) |
| **Servicio 3** | [service-3-whatsapp/README.md](service-3-whatsapp/README.md) | WhatsApp Bridge (Node.js) |

---

## 🗂️ Estructura del Repositorio

```
.
├── README.md                      # README principal (actualizado)
├── INDEX.md                       # Este archivo (índice)
│
├── 📘 DOCUMENTACIÓN GENERAL
│   ├── QUICK_START.md            # Inicio rápido
│   └── DEPLOYMENT_GUIDE.md       # Guía de despliegue completa
│
├── 📂 docs/
│   ├── FAQ.md                    # ⭐ Preguntas y respuestas
│   ├── ARQUITECTURA_DESPLIEGUE.md # Arquitectura completa
│   ├── DIAGRAMA_ARQUITECTURA.md   # Diagramas visuales
│   ├── contrato-mml.md           # Contrato del modelo (original)
│   └── ...
│
├── 📦 SERVICIO 1: Model API
│   └── service-1-model/
│       ├── README.md             # Documentación Servicio 1
│       ├── model_api.py          # API del modelo
│       ├── requirements.txt      # Dependencias Python
│       └── .env.example          # Variables de entorno
│
├── 📦 SERVICIO 2: Backend Principal
│   └── service-2-backend/
│       ├── README.md             # Documentación Servicio 2
│       ├── app.py                # Backend Flask
│       ├── requirements.txt      # Dependencias Python
│       ├── .env.example          # Variables de entorno
│       └── templates/            # HTML del panel admin
│
├── 📦 SERVICIO 3: WhatsApp Bridge
│   └── service-3-whatsapp/
│       ├── README.md             # Documentación Servicio 3
│       ├── index.js              # Bridge WhatsApp
│       ├── package.json          # Dependencias Node.js
│       ├── .env.example          # Variables de entorno
│       └── .gitignore            # Ignorar sesiones
│
└── 📄 ARCHIVOS LEGACY (desarrollo local)
    ├── app.py                    # Backend monolito (legacy)
    ├── model_api.py              # Model API (legacy)
    ├── requirements.txt          # Dependencias (legacy)
    └── whatsapp/                 # WhatsApp original (legacy)
```

---

## 🚀 Flujo de Trabajo Recomendado

### Para Desplegar en Producción

```
1. Lee docs/FAQ.md
   ↓
2. Lee QUICK_START.md
   ↓
3. Sigue DEPLOYMENT_GUIDE.md paso a paso
   ↓
4. Consulta READMEs de cada servicio según necesites
   ↓
5. ¡Listo! 🎉
```

### Para Desarrollo Local

```
1. Lee README.md (sección "Desarrollo Local")
   ↓
2. Elige: Monolito (legacy) o 3 servicios
   ↓
3. Consulta READMEs de servicios para detalles
```

### Para Entender la Arquitectura

```
1. Lee docs/FAQ.md (respuestas directas)
   ↓
2. Lee docs/ARQUITECTURA_DESPLIEGUE.md (explicación completa)
   ↓
3. Lee docs/DIAGRAMA_ARQUITECTURA.md (visualización)
```

---

## 🔍 Búsqueda Rápida

### ¿Buscas Información Sobre...?

- **¿Por qué 3 servicios?** → [docs/ARQUITECTURA_DESPLIEGUE.md](docs/ARQUITECTURA_DESPLIEGUE.md)
- **¿Puedo usar solo Leapcell?** → [docs/FAQ.md](docs/FAQ.md)
- **¿Necesito Next.js?** → [docs/FAQ.md](docs/FAQ.md)
- **¿Cómo despliego?** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **¿Cuánto cuesta?** → [docs/ARQUITECTURA_DESPLIEGUE.md](docs/ARQUITECTURA_DESPLIEGUE.md#-costos-estimados)
- **Configurar Servicio 1** → [service-1-model/README.md](service-1-model/README.md)
- **Configurar Servicio 2** → [service-2-backend/README.md](service-2-backend/README.md)
- **Configurar WhatsApp** → [service-3-whatsapp/README.md](service-3-whatsapp/README.md)
- **Panel Admin** → [service-2-backend/README.md](service-2-backend/README.md#-endpoints)
- **Variables de entorno** → Cada `service-X/.env.example`
- **Troubleshooting** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#-troubleshooting)

---

## 📊 Resumen Visual

```
┌─────────────────────────────────────────────────────────┐
│  ARQUITECTURA DE 3 SERVICIOS                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Usuario WhatsApp                                       │
│      ↓                                                  │
│  Servicio 3 (Node.js - Railway) ⚡ Persistente         │
│      ↓                                                  │
│  Servicio 2 (Flask - Leapcell) ☁️ Serverless          │
│      ↓                                                  │
│  Servicio 1 (Flask - Leapcell) ☁️ Serverless          │
│                                                         │
│  Costo Total: ~$5-17/mes                               │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Rápido

Para verificar que tienes todo:

**Documentación:**
- [ ] Leí [docs/FAQ.md](docs/FAQ.md)
- [ ] Leí [QUICK_START.md](QUICK_START.md)
- [ ] Tengo [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) abierto

**Cuentas:**
- [ ] Cuenta en Leapcell
- [ ] Cuenta en Railway o Render

**Preparación:**
- [ ] Modelo GGUF descargado (~3-4 GB)
- [ ] Variables de entorno preparadas
- [ ] Número de WhatsApp listo

**Despliegue:**
- [ ] Servicio 1 desplegado → URL anotada
- [ ] Servicio 2 desplegado → URL anotada
- [ ] Servicio 3 desplegado → QR escaneado

**Verificación:**
- [ ] Health checks funcionan
- [ ] Panel admin accesible
- [ ] Mensaje de prueba por WhatsApp funciona

---

## 🆘 ¿Necesitas Ayuda?

1. **Revisa [docs/FAQ.md](docs/FAQ.md)** - probablemente tu pregunta ya está respondida
2. **Consulta Troubleshooting** en [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#-troubleshooting)
3. **Revisa logs** de cada servicio
4. **Verifica variables de entorno** en cada servicio

---

## 📝 Notas Importantes

### ⚠️ Advertencias Críticas

1. **NO** intentes poner Servicio 3 en serverless (Leapcell, Vercel, etc)
2. **NO** intentes "pasar la sesión" de WhatsApp entre servicios
3. **SÍ** necesitas Railway/Render/VPS para WhatsApp (persistente)
4. **SÍ** funciona con Leapcell para Servicio 1 y 2 (serverless)

### ✅ Puntos Clave

1. WhatsApp NECESITA proceso persistente 24/7
2. La arquitectura de 3 servicios es la solución correcta
3. No necesitas rehacer el frontend en Next.js
4. Tus HTML templates actuales funcionan perfectamente

---

## 🎓 Para Profundizar

Si quieres entender más a fondo:

- **Contrato del Modelo**: [docs/contrato-mml.md](docs/contrato-mml.md)
- **Flujo Real del Modelo**: [docs/flujo_real_mml.md](docs/flujo_real_mml.md)
- **WhatsApp Web API**: [whatsapp-web.js docs](https://wwebjs.dev/)
- **llama-cpp-python**: [GitHub](https://github.com/abetlen/llama-cpp-python)

---

## 🚀 ¡Éxito!

Tienes toda la documentación necesaria para:
- ✅ Entender por qué esta arquitectura
- ✅ Desplegar los 3 servicios
- ✅ Configurar todo correctamente
- ✅ Solucionar problemas comunes

**Siguiente paso**: Abre [docs/FAQ.md](docs/FAQ.md) y empieza a desplegar! 🎉
