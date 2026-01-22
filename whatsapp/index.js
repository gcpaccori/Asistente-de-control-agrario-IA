import axios from "axios";
import qrcode from "qrcode-terminal";
import { Client, LocalAuth } from "whatsapp-web.js";

const FLASK_URL = process.env.FLASK_URL ?? "http://localhost:5000";
const DEFAULT_ROLE = process.env.DEFAULT_ROLE;

const client = new Client({
  authStrategy: new LocalAuth(),
});

client.on("qr", (qr) => {
  qrcode.generate(qr, { small: true });
  console.log("Escanea el QR con tu WhatsApp para iniciar sesión.");
});

client.on("ready", () => {
  console.log("WhatsApp bridge listo.");
});

client.on("message", async (message) => {
  try {
    const payload = {
      phone: message.from,
      message: message.body ?? "",
    };
    if (DEFAULT_ROLE) {
      payload.role = DEFAULT_ROLE;
    }

    const response = await axios.post(`${FLASK_URL}/agent`, payload, {
      timeout: 15000,
    });
    const modelOutput = response.data.model_output;
    const reply = modelOutput?.respuesta_chat ?? "No pude procesar el mensaje.";

    await message.reply(reply);
  } catch (error) {
    console.error("Error al procesar mensaje:", error?.message ?? error);
    await message.reply("Ocurrió un error. Intenta más tarde.");
  }
});

client.initialize();

setInterval(async () => {
  try {
    const response = await axios.get(`${FLASK_URL}/alerts/pending`, { timeout: 10000 });
    const alerts = response.data.alerts ?? [];
    for (const alert of alerts) {
      const text =
        alert.message ||
        `Alerta ${alert.level}: ${alert.reason}. Acción: ${alert.action}`;
      await client.sendMessage(alert.phone, text);
      await axios.post(`${FLASK_URL}/alerts/${alert.id}/sent`, null, { timeout: 10000 });
    }
  } catch (error) {
    console.error("Error enviando alertas:", error?.message ?? error);
  }
}, 10000);
