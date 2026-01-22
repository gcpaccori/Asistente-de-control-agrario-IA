# Asistente de control agrario IA (MVP)

MVP en Flask para orquestar un modelo de lenguaje (MML) con **tres roles** y
contrato JSON estricto, orientado a atención por WhatsApp y llenado automático
de formularios.

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

## Modelo local (GGUF)
Para pruebas locales en CPU usamos `llama-cpp-python` con un modelo GGUF
cuantizado. Descarga el modelo y valida la carga con el script incluido:

```bash
pip install -r requirements.txt
mkdir -p models
wget -O models/qwen2.5-0.5b-instruct-q4_k_m.gguf \\
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
python validate_local_gguf.py
```

Las salidas de pruebas adicionales (3 por rol) se registran en:
`docs/pruebas_gguf_locales.md`.

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
