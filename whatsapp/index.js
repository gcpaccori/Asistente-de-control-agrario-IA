import axios from "axios";
import qrcode from "qrcode-terminal";
import { Client, LocalAuth } from "whatsapp-web.js";

const FLASK_URL = process.env.FLASK_URL ?? "http://localhost:5000";
const DEFAULT_ROLE = process.env.DEFAULT_ROLE ?? "formulario";

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
      role: DEFAULT_ROLE,
      phone: message.from,
      message: message.body ?? "",
    };

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
