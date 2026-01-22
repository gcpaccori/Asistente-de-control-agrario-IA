# Asistente de control agrario IA (MVP)

MVP en Flask para orquestar un modelo de lenguaje (MML) con **tres roles** y
contrato JSON estricto, orientado a atención por WhatsApp y llenado automático
de formularios.

## Objetivo
- Recibir mensajes del productor.
- Construir contexto filtrado por rol.
- Llamar a un MML externo (Groq u otro) usando el contrato JSON.
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

## Modelo (xAI)
El servidor se integra con xAI a través del contrato JSON.

Puedes usar variables de entorno o un archivo `.env` en la raíz del proyecto.

**Opción 1: variables de entorno (xAI)**
```bash
export MML_PROVIDER=xai
export XAI_API_KEY="tu_api_key"
export XAI_MODEL="grok-4-latest"
python app.py
```

**Opción 2: archivo .env**
Copia `.env.example` a `.env` y reemplaza los valores:
```bash
cp .env.example .env
python app.py
```

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
