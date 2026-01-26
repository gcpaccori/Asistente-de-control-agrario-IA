# ✅ Checklist de Deployment

Usa esta lista para verificar que todo está configurado correctamente.

## Pre-Deployment

- [ ] He leído `RESUMEN-VERCEL.md`
- [ ] He ejecutado `python verify_vercel_setup.py` exitosamente
- [ ] Tengo cuenta en Vercel
- [ ] Tengo API key de Grok/OpenAI u otro proveedor LLM

## Configuración Vercel

- [ ] He instalado Vercel CLI: `npm install -g vercel`
- [ ] He hecho login: `vercel login`
- [ ] He configurado variables de entorno en Vercel Dashboard:
  - [ ] `MODEL_API_URL`
  - [ ] `MML_PROVIDER` (opcional)
  - [ ] `XAI_API_KEY` (opcional, si usas Grok)
  - [ ] `XAI_MODEL` (opcional, si usas Grok)

## Deployment

- [ ] He ejecutado `vercel` o `vercel --prod`
- [ ] El deployment fue exitoso
- [ ] He probado el endpoint `/health`: `curl https://mi-proyecto.vercel.app/health`
- [ ] La respuesta de `/health` es correcta: `{"status": "ok", "time": "..."}`

## Configuración WhatsApp

- [ ] He instalado dependencias: `cd whatsapp && npm install`
- [ ] He configurado `FLASK_URL` con mi URL de Vercel
- [ ] He ejecutado `npm start` en el directorio whatsapp
- [ ] He escaneado el QR code con WhatsApp
- [ ] Veo el mensaje "WhatsApp bridge listo."

## Configuración Backend

- [ ] He accedido al panel admin: `https://mi-proyecto.vercel.app/admin`
- [ ] He creado al menos un productor autorizado
- [ ] He verificado los 3 roles de agentes en `/admin/agents`:
  - [ ] Rol: formulario
  - [ ] Rol: consulta
  - [ ] Rol: intervención

## Prueba End-to-End

- [ ] He enviado un mensaje de prueba por WhatsApp
- [ ] El bot ha respondido
- [ ] He verificado en `/admin/producers` que se registró el mensaje
- [ ] He verificado los logs en Vercel Dashboard

## Monitoreo

- [ ] Sé cómo acceder a logs en Vercel: Dashboard → Deployments → Functions
- [ ] Sé cómo ver logs del puente WhatsApp: terminal donde ejecuté `npm start`
- [ ] He configurado alertas en Vercel (opcional)

## Documentación Leída

- [ ] `RESUMEN-VERCEL.md` - Resumen de cambios
- [ ] `docs/setup-completo.md` - Guía paso a paso
- [ ] `docs/arquitectura-3-partes.md` - Entiendo las 3 partes del sistema

## Opcional (Recomendado para Producción)

- [ ] He considerado migrar a PostgreSQL en lugar de SQLite
- [ ] He configurado un dominio personalizado en Vercel
- [ ] He revisado límites del plan gratuito de Vercel
- [ ] He configurado backups de la base de datos
- [ ] He considerado migrar a WhatsApp Business API oficial

## Troubleshooting

Si algo no funciona:

1. [ ] He ejecutado `python verify_vercel_setup.py`
2. [ ] He revisado logs en Vercel Dashboard
3. [ ] He revisado logs del puente WhatsApp en la terminal
4. [ ] He consultado la sección de troubleshooting en `docs/setup-completo.md`
5. [ ] He verificado que el productor está autorizado en `/admin/producers`

## Siguiente Nivel

- [ ] He personalizado los prompts de los agentes
- [ ] He agregado múltiples productores
- [ ] He configurado tipos de logs personalizados
- [ ] He creado plantillas de planes agronómicos
- [ ] He explorado el panel de administración completo

---

**Fecha:** _________________

**Notas:**

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
