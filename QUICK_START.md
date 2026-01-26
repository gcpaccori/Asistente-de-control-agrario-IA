# 🚀 Guía Rápida de Inicio

## ¿Qué necesito desplegar?

Este proyecto tiene **3 servicios** que deben desplegarse en diferentes plataformas:

```
📦 Servicio 1: Model API (Flask + LLM)
   └─ Desplegar en: Leapcell (serverless OK)
   └─ Propósito: Inferencia del modelo de IA

📦 Servicio 2: Backend Principal (Flask + SQLite)
   └─ Desplegar en: Leapcell (serverless OK)
   └─ Propósito: API, base de datos, panel admin

📦 Servicio 3: WhatsApp Bridge (Node.js)
   └─ Desplegar en: Railway o Render (DEBE ser persistente)
   └─ Propósito: Conexión con WhatsApp Web
```

## ⚡ Inicio Rápido

### Opción 1: Solo quiero entender la arquitectura
Lee: `docs/ARQUITECTURA_DESPLIEGUE.md`

### Opción 2: Quiero desplegar paso a paso
Sigue: `DEPLOYMENT_GUIDE.md`

### Opción 3: Quiero ver detalles técnicos de cada servicio
- Servicio 1: `service-1-model/README.md`
- Servicio 2: `service-2-backend/README.md`
- Servicio 3: `service-3-whatsapp/README.md`

## 🎯 Respuestas Rápidas

### ¿Puedo usar solo Leapcell para todo?
**NO**. Leapcell es serverless y WhatsApp necesita proceso persistente 24/7.

### ¿Necesito crear un frontend en Next.js?
**NO**. El frontend ya está hecho en Flask (templates HTML en Servicio 2).

### ¿Puedo pasar la sesión de WhatsApp entre servicios?
**NO**. La sesión vive en el proceso Node persistente.

### ¿Qué plataforma uso para WhatsApp?
**Railway** (recomendado, $5/mes) o **Render** ($7/mes) o un **VPS**.

### ¿Cuánto cuesta todo?
Entre **$5-15/mes** dependiendo de los planes que elijas.

## 📋 Checklist de Despliegue

```
[ ] 1. Descargar modelo GGUF (~3-4 GB)
[ ] 2. Crear cuenta en Leapcell
[ ] 3. Desplegar Servicio 1 en Leapcell → Anotar URL
[ ] 4. Desplegar Servicio 2 en Leapcell → Anotar URL
[ ] 5. Crear cuenta en Railway o Render
[ ] 6. Desplegar Servicio 3 en Railway/Render
[ ] 7. Escanear QR de WhatsApp
[ ] 8. Configurar productores en /admin
[ ] 9. Probar enviando mensaje por WhatsApp
[ ] 10. ¡Funciona! 🎉
```

## 🆘 ¿Problemas?

1. **Servicio 1 no carga**: Verificar que modelo GGUF está disponible
2. **Servicio 2 no conecta a Servicio 1**: Verificar `MODEL_API_URL`
3. **Servicio 3 no conecta a Servicio 2**: Verificar `FLASK_URL`
4. **WhatsApp no responde**: Verificar productor autorizado en `/admin/producers`
5. **QR no aparece**: Ver logs, considerar webhook o desplegar en VPS

## 🎓 Para Entender Más

- **¿Por qué 3 servicios?**: Separación de responsabilidades y escalabilidad
- **¿Por qué no serverless para WhatsApp?**: Necesita mantener sesión activa
- **¿Alternativas a Railway?**: Render, Fly.io, VPS (DigitalOcean, etc)

## 📞 Flujo de un Mensaje

```
Usuario (WhatsApp)
   ↓
Servicio 3 (Node.js persistente en Railway)
   ↓ HTTP POST
Servicio 2 (Flask backend en Leapcell)
   ↓ HTTP POST
Servicio 1 (Model API en Leapcell)
   ↓ respuesta JSON
Servicio 2 (procesa y guarda en DB)
   ↓ respuesta JSON
Servicio 3 (extrae texto)
   ↓ mensaje WhatsApp
Usuario (recibe respuesta)
```

## ✅ Conclusión

- **SÍ** puedes usar Leapcell para Servicios 1 y 2
- **NO** puedes usar Leapcell para Servicio 3
- **SÍ** necesitas Railway/Render/VPS para WhatsApp
- **NO** necesitas crear frontend nuevo en Next.js

Para más detalles, lee `DEPLOYMENT_GUIDE.md` 🚀
