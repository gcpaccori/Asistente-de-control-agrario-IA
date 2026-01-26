# Webhook de Vercel (Opcional)

Este directorio contiene un webhook opcional para Vercel que puede recibir webhooks de WhatsApp Business API.

## ⚠️ Importante

**Este webhook es OPCIONAL.** Solo necesitas esto si:
- Vas a usar WhatsApp Business API oficial (no WhatsApp Web)
- Quieres recibir webhooks de WhatsApp en Vercel

## Si usas whatsapp-web.js (actual)

NO necesitas desplegar nada en Vercel. Solo ejecuta:

```bash
cd whatsapp
export FLASK_URL="https://tu-backend-en-leapcell.io"
npm start
```

## Si migras a WhatsApp Business API

1. Despliega este webhook en Vercel:
```bash
vercel
```

2. Configura variables de entorno en Vercel:
```
LEAPCELL_BACKEND_URL=https://tu-backend-en-leapcell.io
WEBHOOK_VERIFY_TOKEN=tu_token_secreto
```

3. Configura la URL del webhook en WhatsApp Business:
```
https://tu-proyecto.vercel.app/webhook
```

## Arquitectura

```
WhatsApp Business API → Vercel Webhook → Backend Leapcell (Flask)
```

El webhook simplemente reenvía los mensajes al backend en Leapcell.
