# Asistente de control agrario IA (MVP)

MVP en Flask para orquestar un modelo de lenguaje (MML) con **tres roles** y
contrato JSON estricto, orientado a atención por WhatsApp y llenado automático
de formularios.

## 🚀 Despliegue en Producción

Este proyecto está diseñado para desplegarse como **3 servicios independientes**:

1. **Servicio 1 (Model API)**: Flask + LLM → Leapcell (serverless)
2. **Servicio 2 (Backend)**: Flask + SQLite → Leapcell (serverless)
3. **Servicio 3 (WhatsApp)**: Node.js → Railway/Render (persistente 24/7)

### 📚 Índice de Documentación

**👉 [Ver INDEX.md](INDEX.md) - Índice completo de toda la documentación**

### 📖 Guías Principales

- **❓ FAQ**: [`docs/FAQ.md`](docs/FAQ.md) ← **EMPIEZA AQUÍ** (responde todas tus preguntas)
- **🎯 Inicio Rápido**: [`QUICK_START.md`](QUICK_START.md) - Resumen ejecutivo
- **📋 Guía Completa**: [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) - Paso a paso
- **🏗️ Arquitectura**: [`docs/ARQUITECTURA_DESPLIEGUE.md`](docs/ARQUITECTURA_DESPLIEGUE.md) - Diseño detallado
- **📊 Diagramas**: [`docs/DIAGRAMA_ARQUITECTURA.md`](docs/DIAGRAMA_ARQUITECTURA.md) - Flujos visuales

### 📦 Servicios Individuales

Cada servicio tiene su propia documentación:
- [`service-1-model/README.md`](service-1-model/README.md) - Model API (LLM)
- [`service-2-backend/README.md`](service-2-backend/README.md) - Backend Principal
- [`service-3-whatsapp/README.md`](service-3-whatsapp/README.md) - WhatsApp Bridge

## Objetivo
- Recibir mensajes del productor.
- Construir contexto filtrado por rol.
- Llamar a un MML local usando el contrato JSON.
- Guardar/actualizar el formulario cuando corresponda.
- Emitir alertas cuando aplique.

## Estructura
```
.
├── app.py                    # Backend principal (legacy)
├── model_api.py             # Model API (legacy)
├── service-1-model/         # 📦 Servicio 1: Model API
├── service-2-backend/       # 📦 Servicio 2: Backend Principal
├── service-3-whatsapp/      # 📦 Servicio 3: WhatsApp Bridge
├── docs/                    # Documentación
├── DEPLOYMENT_GUIDE.md      # Guía de despliegue completa
└── QUICK_START.md          # Guía rápida
```

## 💻 Desarrollo Local

### Requisitos
- Python 3.10+
- Node.js 18+ (para el puente de WhatsApp)

### Opción 1: Archivos Legacy (Monolito)

Para desarrollo rápido usando los archivos originales:

```bash
# Instalar dependencias Python
pip install -r requirements.txt

# Ejecutar backend principal
python app.py
# Acceder a http://localhost:5000

# En otra terminal, ejecutar Model API (si quieres separado)
python model_api.py
# Acceder a http://localhost:8001

# En otra terminal, ejecutar WhatsApp (opcional)
cd whatsapp
npm install
FLASK_URL=http://localhost:5000 node index.js
```

### Opción 2: Servicios Separados (Producción-like)

Para probar la arquitectura de 3 servicios:

```bash
# Terminal 1: Servicio 1 (Model API)
cd service-1-model
pip install -r requirements.txt
python model_api.py
# → http://localhost:8001

# Terminal 2: Servicio 2 (Backend)
cd service-2-backend
pip install -r requirements.txt
MODEL_API_URL=http://localhost:8001 python app.py
# → http://localhost:5000

# Terminal 3: Servicio 3 (WhatsApp)
cd service-3-whatsapp
npm install
FLASK_URL=http://localhost:5000 node index.js
# → Escanear QR
```

## Base de datos y panel visual
Se usa SQLite en `instance/app.db` y una interfaz web básica en:

```
http://localhost:5000/admin
```

Desde el panel puedes:
- Activar/desactivar agentes (3 roles).
- Editar prompts y tokens máximos.
- Revisar formularios generados y actualizar su estado.
- Revisar alertas de intervención y cerrar casos.
- Registrar productores autorizados y asignar roles por productor.
- Ver historial y análisis reciente por productor.

## Contrato MML (JSON)
El contrato completo está en `docs/contrato-mml.md`.

## Modelo local (GGUF)
Para pruebas locales en CPU usamos `llama-cpp-python` con un modelo GGUF
cuantizado. Descarga el modelo y valida la carga con el script incluido:

```bash
pip install -r requirements.txt
mkdir -p models
wget -O models/qwen2.5-3b-instruct-q4_k_m.gguf \\
  https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
N_CTX=2048 N_THREADS=1 python validate_local_gguf.py
```

Si despliegas con 2 GB de RAM y 1 CPU, un contexto de 2048 tokens suele ser un
punto de partida razonable. Puedes ajustar el contexto con `N_CTX` y el número
de hilos con `N_THREADS` según tu capacidad.

## Contrato JSON y conversación (aclaración)
El **contrato JSON** es el formato estrictamente esperado entre el servidor y
el MML: se envía un conjunto de mensajes con rol (`system`, `assistant`, `user`)
y el modelo debe devolver un JSON válido según el rol y la tarea. El detalle
completo está en `docs/contrato-mml.md`, pero en resumen:

- **system**: define reglas y formato de salida (por ejemplo, “responde solo
  JSON con claves específicas”). Esto restringe la salida y reduce la
  “libertad” del modelo para asegurar consistencia.
- **assistant**: permite agregar contexto previo (p. ej., estado del productor,
  formulario, alertas) y pide al modelo responder dentro del contrato.
- **user**: contiene la consulta real del productor o la instrucción que se
  quiere resolver.

### ¿Hasta qué punto “conversa” el modelo?
El modelo sí puede tener una conversación fluida **si el contrato lo permite**.
Cuando el `system` exige JSON estricto, la respuesta se limita a ese formato y
no a texto libre. Para una conversación más natural, puedes relajar el contrato
en el `system` (por ejemplo, “responde en lenguaje natural”) o crear un modo de
chat sin JSON para ciertos flujos.

### Libertad de expresión recomendada
- **Alta libertad** (conversación real): `system` pide lenguaje natural y solo
  acota tono/longitud. Útil para orientación general o mensajes al productor.
- **Media libertad**: `system` pide estructura (p. ej., bullets o campos) pero
  permite frases naturales dentro de cada campo.
- **Baja libertad** (contrato estricto): `system` exige JSON exacto. Útil para
  automatizar formularios y decisiones, pero menos “conversacional”.

## WhatsApp (puente inicial)
Incluye un puente mínimo con `whatsapp-web.js` que usa tu sesión abierta en el
navegador. Esto es solo para el MVP; puede violar términos del servicio.
Recomendación: migrar a WhatsApp Business API cuando tengas presupuesto.

```bash
cd whatsapp
npm install
FLASK_URL="http://localhost:5000" node index.js
```

Para que un productor sea atendido, debes marcarlo como **autorizado** en
`/admin/producers`. Si no está autorizado, el endpoint `/agent` devuelve `403`.

## Endpoints principales
### `POST /agent`
Recibe un mensaje y un rol, construye el contexto y devuelve el JSON que debe
enviar el MML. El cliente WhatsApp debe usar `respuesta_chat` para responder
al productor.

### `POST /form/update`
Actualiza el estado del formulario del productor.

### `POST /alert`
Crea una alerta (para intervención técnica).

### `GET /health`
Salud del servicio.

## Nota
El archivo `docs/contrato-mml.md` contiene el contrato completo MML ↔ Flask
para los tres roles (formulario, consulta, intervención).
