# Asistente de control agrario IA (MVP)

MVP en Flask para orquestar un modelo de lenguaje (MML) con **tres roles** y
contrato JSON estricto, orientado a atención por WhatsApp y llenado automático
de formularios.

> **🚀 Nuevo:** Sistema listo para deployment en Vercel con Node.js
> 
> El sistema ahora está configurado en **3 partes**:
> 1. **Puente WhatsApp** (Node.js, local)
> 2. **Backend Flask** (Python, Vercel)
> 3. **API de Modelo** (externa o local)
>
> 📖 Lee la [Guía de Arquitectura de 3 Partes](docs/arquitectura-3-partes.md) para entender el sistema completo.

## Objetivo
- Recibir mensajes del productor.
- Construir contexto filtrado por rol.
- Llamar a un MML local usando el contrato JSON.
- Guardar/actualizar el formulario cuando corresponda.
- Emitir alertas cuando aplique.

## Estructura
```
.
├── app.py
├── docs
│   └── contrato-mml.md
└── requirements.txt
```

## Requisitos
- Python 3.10+
- Node.js 18+ (solo si usas el puente de WhatsApp)

Instalación:
```bash
pip install -r requirements.txt
```

## Ejecutar
```bash
python app.py
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

## Deployment en Vercel

Para desplegar el sistema en Vercel con Node.js y una API externa de modelo de lenguaje, consulta la guía completa en:

**[docs/vercel-deployment.md](docs/vercel-deployment.md)**

La guía incluye:
- Configuración paso a paso
- Variables de entorno requeridas
- Integración con el puente WhatsApp
- Solución de problemas comunes

## Nota
El archivo `docs/contrato-mml.md` contiene el contrato completo MML ↔ Flask
para los tres roles (formulario, consulta, intervención).
