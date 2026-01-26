/**
 * Vercel Serverless Function - WhatsApp Webhook Handler
 * 
 * Este servicio recibe webhooks de WhatsApp Business API y los reenvía
 * al backend Flask en Leapcell.
 * 
 * Variables de entorno requeridas en Vercel:
 * - LEAPCELL_BACKEND_URL: URL del backend Flask (ej: https://tu-app.leapcell.io)
 * - WEBHOOK_VERIFY_TOKEN: Token para verificar webhooks de WhatsApp (opcional)
 */

export default async function handler(req, res) {
  const LEAPCELL_BACKEND_URL = process.env.LEAPCELL_BACKEND_URL;
  const WEBHOOK_VERIFY_TOKEN = process.env.WEBHOOK_VERIFY_TOKEN || 'default_token';

  // Verificación de webhook (GET request de WhatsApp)
  if (req.method === 'GET') {
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];

    if (mode === 'subscribe' && token === WEBHOOK_VERIFY_TOKEN) {
      console.log('Webhook verified');
      return res.status(200).send(challenge);
    } else {
      return res.status(403).send('Forbidden');
    }
  }

  // Manejo de mensajes de WhatsApp (POST request)
  if (req.method === 'POST') {
    try {
      const body = req.body;
      
      // Log para debugging
      console.log('Webhook received:', JSON.stringify(body, null, 2));

      // Verificar que hay un backend configurado
      if (!LEAPCELL_BACKEND_URL) {
        console.error('LEAPCELL_BACKEND_URL not configured');
        return res.status(500).json({ error: 'Backend URL not configured' });
      }

      // Extraer información del mensaje de WhatsApp
      if (body.entry && body.entry[0]?.changes?.[0]?.value?.messages?.[0]) {
        const message = body.entry[0].changes[0].value.messages[0];
        const phone = message.from;
        const messageText = message.text?.body || '';

        // Preparar payload para el backend de Leapcell
        const payload = {
          phone: phone,
          message: messageText,
          role: process.env.DEFAULT_ROLE || 'formulario'
        };

        // Enviar al backend de Leapcell
        const response = await fetch(`${LEAPCELL_BACKEND_URL}/agent`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`Backend responded with ${response.status}`);
        }

        const data = await response.json();
        console.log('Backend response:', data);

        // Responder a WhatsApp con la respuesta del agente
        // Nota: Para enviar la respuesta de vuelta, necesitas usar la API de WhatsApp Business
        // Este es un ejemplo básico. Necesitarás adaptarlo según tu configuración.
        
        return res.status(200).json({ 
          success: true, 
          message: 'Message forwarded to backend',
          agent_response: data.model_output?.respuesta_chat
        });
      }

      // Si no hay mensaje, solo confirmar recepción
      return res.status(200).json({ success: true, message: 'Event received' });

    } catch (error) {
      console.error('Error processing webhook:', error);
      return res.status(500).json({ 
        error: 'Internal server error', 
        message: error.message 
      });
    }
  }

  // Método no soportado
  return res.status(405).json({ error: 'Method not allowed' });
}
