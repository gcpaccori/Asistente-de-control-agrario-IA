# Servicio 3: WhatsApp Bridge (Node.js)

## 📋 Descripción
⚠️ **SERVICIO PERSISTENTE CRÍTICO**

Puente entre WhatsApp Web y el backend Flask. Mantiene sesión de WhatsApp activa 24/7.

## 🔧 Características
- Framework: Node.js + whatsapp-web.js
- Puerto: 3000
- Tipo: **PERSISTENTE (24/7)** ⚠️
- **NO PUEDE SER SERVERLESS**

## ❗ ¿Por qué DEBE ser persistente?

1. **Sesión de WhatsApp Web**: Debe mantenerse activa todo el tiempo
2. **Navegador Chromium**: Controla navegador en segundo plano
3. **Archivos de sesión**: Guarda `.wwebjs_auth/` localmente
4. **Escucha en tiempo real**: No puede "dormirse"

**SI USAS SERVERLESS (Leapcell, Vercel), NO FUNCIONARÁ** ❌

## 📦 Dependencias
```bash
npm install
```

Dependencias:
- `whatsapp-web.js`: Cliente WhatsApp Web
- `qrcode-terminal`: Genera QR en terminal
- `axios`: Cliente HTTP

## 🚀 Ejecución Local

### Requisitos
- Node.js 18+
- Chrome/Chromium instalado

### Pasos
```bash
# Instalar dependencias
npm install

# Configurar variables de entorno
export FLASK_URL=http://localhost:5000
export DEFAULT_ROLE=formulario

# Ejecutar
npm start
```

### Primera Ejecución
1. Al iniciar aparecerá un **QR en la terminal**
2. **Escanea el QR** con tu WhatsApp
3. Sesión se guarda en `.wwebjs_auth/`
4. Próximas ejecuciones no pedirán QR

## 🌐 Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `FLASK_URL` | URL del Servicio 2 (Backend) | `http://localhost:5000` |
| `DEFAULT_ROLE` | Rol por defecto (formulario/consulta/intervención) | - (opcional) |
| `PORT` | Puerto del servicio | `3000` |

## 🔄 Funcionamiento

### 1. Inicialización
```
- Carga sesión guardada (si existe)
- Si no hay sesión, genera QR
- Escaneas QR con WhatsApp
- Sesión queda guardada en .wwebjs_auth/
```

### 2. Escucha Mensajes 24/7
```
- WhatsApp envía mensaje al número
  ↓
- whatsapp-web.js detecta mensaje
  ↓
- Extrae: phone, message
  ↓
- POST a Servicio 2: /agent
  ↓
- Recibe respuesta del backend
  ↓
- Envía respuesta por WhatsApp
```

### 3. Envío de Alertas (polling)
Cada 10 segundos:
```
- GET a Servicio 2: /alerts/pending
  ↓
- Si hay alertas pendientes
  ↓
- Envía mensaje por WhatsApp
  ↓
- POST a Servicio 2: /alerts/:id/sent
```

## 🚢 Despliegue (NO EN LEAPCELL)

### ❌ Plataformas NO Compatibles
- ❌ Leapcell (serverless)
- ❌ Vercel (serverless)
- ❌ Netlify Functions (serverless)
- ❌ AWS Lambda (serverless)

### ✅ Plataformas Compatibles

## Opción 1: Railway (RECOMENDADO) 🚂

### Por qué Railway
- ✅ Soporta procesos persistentes
- ✅ Plan Hobby incluye $5 gratis/mes
- ✅ Fácil deploy desde GitHub
- ✅ Buen soporte para Node.js

### Pasos de Despliegue

#### 1. Crear Cuenta
1. Ir a [Railway.app](https://railway.app)
2. Crear cuenta (con GitHub)

#### 2. Nuevo Proyecto
1. Dashboard → New Project
2. Deploy from GitHub repo
3. Seleccionar tu repositorio
4. Root directory: `service-3-whatsapp`

#### 3. Configuración Automática
Railway detecta automáticamente:
- `package.json`
- Build: `npm install`
- Start: `npm start`

#### 4. Variables de Entorno
En Settings → Variables:
```
FLASK_URL=https://tu-servicio-2.leapcell.dev
DEFAULT_ROLE=formulario
```

⚠️ **IMPORTANTE**: Usar URL pública del Servicio 2

#### 5. Deploy
1. Click Deploy
2. Ver logs en tiempo real
3. Esperar a que aparezca: "Escanea el QR..."

#### 6. Escanear QR
**Problema**: Railway no muestra QR en UI

**Soluciones:**
1. **Ver logs** (puede que se muestre mal)
2. **Usar webhook** para recibir QR
3. **SSH al contenedor** (si Railway lo permite)

**Mejor opción**: Modificar `index.js` para enviar QR por HTTP:
```javascript
client.on("qr", (qr) => {
  // Enviar QR a endpoint temporal
  axios.post("https://tu-url-temp/qr", { qr });
});
```

#### 7. Monitoreo
- Ver logs: Railway dashboard
- Restart si se cae (Railway auto-restart)
- Sesión persiste en volumen

### Costos Railway
- Plan Hobby: $5/mes incluidos gratis
- Uso promedio: ~$2-3/mes
- Si excedes: $0.000231/min ($10/mes aprox)

---

## Opción 2: Render.com 🎨

### Por qué Render
- ✅ Plan gratuito disponible
- ⚠️ Se duerme después de 15 min (plan free)
- ✅ Plan pagado: $7/mes sin sleep

### Pasos de Despliegue

#### 1. Crear Cuenta
1. Ir a [Render.com](https://render.com)
2. Crear cuenta (con GitHub)

#### 2. Nuevo Web Service
1. Dashboard → New → Web Service
2. Connect GitHub repository
3. Root directory: `service-3-whatsapp`

#### 3. Configuración
```
Name: whatsapp-bridge
Environment: Node
Build Command: npm install
Start Command: npm start
```

⚠️ **Importante**: Seleccionar **Web Service** (no Background Worker)

#### 4. Plan
- **Free**: Se duerme después de 15 min de inactividad
  - NO recomendado para producción
  - OK para pruebas
- **Starter ($7/mes)**: No se duerme
  - Recomendado para producción

#### 5. Variables de Entorno
```
FLASK_URL=https://tu-servicio-2.leapcell.dev
DEFAULT_ROLE=formulario
```

#### 6. Deploy y QR
Mismo problema que Railway con el QR.
Ver logs o modificar código para capturar QR.

### Costos Render
- Plan Free: $0 (se duerme)
- Plan Starter: $7/mes

---

## Opción 3: Fly.io 🪰

### Por qué Fly.io
- ✅ Buen free tier
- ✅ Persistencia garantizada
- ⚠️ Requiere Dockerfile

### Pasos de Despliegue

#### 1. Instalar CLI
```bash
curl -L https://fly.io/install.sh | sh
```

#### 2. Login
```bash
flyctl auth login
```

#### 3. Crear App
```bash
cd service-3-whatsapp
flyctl launch
```

Responder:
- App name: whatsapp-bridge-xxx
- Region: elegir más cercana
- Database: No
- Deploy: Yes

#### 4. Configurar Secretos
```bash
flyctl secrets set FLASK_URL=https://tu-servicio-2.leapcell.dev
flyctl secrets set DEFAULT_ROLE=formulario
```

#### 5. Deploy
```bash
flyctl deploy
```

#### 6. Ver Logs
```bash
flyctl logs
```

#### 7. Escanear QR
Mismo problema de visualización. Considerar endpoint temporal.

### Costos Fly.io
- Free tier: ~$5/mes incluido
- Uso promedio: $3-5/mes

---

## Opción 4: VPS (DigitalOcean, Linode, etc) 🖥️

### Por qué VPS
- ✅ Control total
- ✅ No hay sorpresas de facturación
- ⚠️ Requiere configuración manual
- ⚠️ Debes mantener el servidor

### Requisitos
- Ubuntu 20.04+ o Debian
- 1 GB RAM mínimo
- 10 GB storage

### Pasos de Despliegue

#### 1. Conectar por SSH
```bash
ssh root@tu-ip-servidor
```

#### 2. Instalar Node.js
```bash
# Agregar repositorio de NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Instalar Node.js
sudo apt-get install -y nodejs

# Verificar
node --version  # debe ser v18+
npm --version
```

#### 3. Instalar Git
```bash
sudo apt-get install -y git
```

#### 4. Clonar Repositorio
```bash
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo/service-3-whatsapp
```

#### 5. Instalar Dependencias
```bash
npm install
```

#### 6. Configurar Variables de Entorno
```bash
nano .env
```

Agregar:
```
FLASK_URL=https://tu-servicio-2.leapcell.dev
DEFAULT_ROLE=formulario
```

#### 7. Instalar PM2 (Process Manager)
```bash
npm install -g pm2
```

#### 8. Iniciar con PM2
```bash
pm2 start index.js --name whatsapp-bridge
```

#### 9. Escanear QR
```bash
pm2 logs whatsapp-bridge
```

Aparecerá el QR en los logs. Escanear con WhatsApp.

#### 10. Configurar Auto-start
```bash
# Guardar configuración PM2
pm2 save

# Configurar inicio automático
pm2 startup
# Copiar y ejecutar el comando que muestra
```

#### 11. Comandos Útiles
```bash
# Ver logs
pm2 logs whatsapp-bridge

# Reiniciar
pm2 restart whatsapp-bridge

# Detener
pm2 stop whatsapp-bridge

# Ver estado
pm2 status
```

### Costos VPS
- DigitalOcean: $6/mes (1GB RAM)
- Linode: $5/mes (1GB RAM)
- Vultr: $5/mes (1GB RAM)

---

## 📱 Uso de WhatsApp

### Escanear QR
1. Abrir WhatsApp en tu teléfono
2. Ir a: Configuración → Dispositivos vinculados
3. Vincular dispositivo
4. Escanear QR que aparece en los logs

### Sesión Persistente
- Sesión se guarda en `.wwebjs_auth/`
- Solo necesitas escanear QR una vez
- Si borras `.wwebjs_auth/`, deberás escanear de nuevo

### Cerrar Sesión
Para cerrar sesión (ej: cambiar de número):
```bash
# Detener servicio
pm2 stop whatsapp-bridge  # o Railway/Render

# Borrar carpeta de sesión
rm -rf .wwebjs_auth/

# Reiniciar servicio
pm2 start whatsapp-bridge
# Se generará nuevo QR
```

## 🔧 Configuración Avanzada

### Múltiples Roles
Si quieres que diferentes números usen diferentes roles:

Modificar `index.js`:
```javascript
const ROLE_MAP = {
  "51987654321@c.us": "formulario",
  "51912345678@c.us": "consulta",
};

client.on("message", async (message) => {
  const role = ROLE_MAP[message.from] || DEFAULT_ROLE || "formulario";
  // ...
});
```

### Webhook para QR
Para recibir QR por HTTP (útil en Railway/Render):

```javascript
client.on("qr", async (qr) => {
  qrcode.generate(qr, { small: true });
  
  // Enviar QR a endpoint temporal
  try {
    await axios.post("https://webhook.site/tu-uuid", { qr });
  } catch (err) {
    console.error("Error enviando QR:", err);
  }
});
```

## 📊 Monitoreo

### Logs
- Railway/Render: Ver en dashboard
- VPS: `pm2 logs whatsapp-bridge`

### Estado
- Verificar que "WhatsApp bridge listo" aparece en logs
- Enviar mensaje de prueba

### Alertas
Configurar alertas si el servicio se cae:
- PM2: `pm2 install pm2-server-monit`
- UptimeRobot: Monitorear endpoint

## 🐛 Troubleshooting

### QR no aparece
- Ver logs completos
- Asegurar que Chromium está instalado
- En algunos entornos necesita dependencias extras:
```bash
sudo apt-get install -y \
  chromium-browser \
  chromium-codecs-ffmpeg
```

### "Session closed"
- Sesión fue cerrada desde WhatsApp
- Borrar `.wwebjs_auth/` y reiniciar
- Escanear nuevo QR

### Mensajes no se envían
- Verificar FLASK_URL
- Ver logs para errores de conexión
- Probar health check del Servicio 2

### Servicio se reinicia constantemente
- Ver logs para errores
- Verificar memoria (puede quedarse sin RAM)
- Aumentar recursos en plataforma

### "Cannot connect to backend"
- Verificar que Servicio 2 está desplegado
- Verificar FLASK_URL (debe ser pública)
- Probar con curl desde el servicio

## ⚠️ Advertencias Importantes

### WhatsApp TOS
- whatsapp-web.js NO es oficial
- Puede violar términos de servicio de WhatsApp
- Para producción seria: **WhatsApp Business API**

### Rate Limiting
- WhatsApp puede bloquear por spam
- Implementar delays entre mensajes
- No enviar más de 1 mensaje/segundo

### Backup de Sesión
- Hacer backup de `.wwebjs_auth/`
- Si se pierde, debes escanear QR de nuevo

## 🚀 Próximos Pasos

Una vez desplegado:
1. Escanear QR
2. Enviar mensaje de prueba al número
3. Verificar respuesta
4. Revisar logs en Servicio 2 y 3
5. Configurar productores en `/admin`

## 📚 Referencias
- [whatsapp-web.js docs](https://wwebjs.dev/)
- [Railway docs](https://docs.railway.app/)
- [Render docs](https://render.com/docs)
- [Fly.io docs](https://fly.io/docs/)
- [PM2 docs](https://pm2.keymetrics.io/)
