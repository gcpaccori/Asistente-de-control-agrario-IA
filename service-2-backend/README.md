# Servicio 2: Backend Principal (Flask)

## 📋 Descripción
Backend principal con lógica de negocio, base de datos SQLite y panel de administración web.

## 🔧 Características
- Framework: Flask
- Base de datos: SQLite
- Puerto: 5000
- Tipo: **Serverless OK** ✅
- Panel Admin: `/admin`

## 📦 Dependencias
```bash
pip install -r requirements.txt
```

## 🚀 Ejecución Local
```bash
# Configurar variables de entorno
export MODEL_API_URL=http://localhost:8001
export DATABASE_PATH=./instance/app.db
export DEFAULT_TIMEZONE=America/Lima
export DAILY_CHECKIN_HOUR=8

# Ejecutar
python app.py
```

El servicio estará disponible en `http://localhost:5000`
Panel admin en `http://localhost:5000/admin`

## 🌐 Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `MODEL_API_URL` | URL del Servicio 1 (Model API) | - (requerido) |
| `DATABASE_PATH` | Ruta a base de datos SQLite | `./instance/app.db` |
| `DEFAULT_TIMEZONE` | Zona horaria | `America/Lima` |
| `DAILY_CHECKIN_HOUR` | Hora de check-in diario | `8` |
| `PORT` | Puerto del servicio | `5000` |

## 📡 Endpoints

### GET /health
Health check del servicio.

### POST /agent
Endpoint principal para procesar mensajes.

**Request:**
```json
{
  "phone": "51987654321@c.us",
  "message": "Hola, ¿cuándo debo regar?",
  "role": "consulta"
}
```

**Response:**
```json
{
  "model_output": {
    "role": "consulta",
    "respuesta_chat": "Según tu cultivo...",
    "acciones": {...},
    "estado": {...}
  }
}
```

### GET /admin
Panel de administración web.

Funcionalidades:
- Activar/desactivar agentes (3 roles)
- Editar prompts y configuración
- Revisar formularios generados
- Gestionar alertas
- Registrar productores autorizados
- Ver historial por productor

### POST /form/update
Actualizar formulario de productor.

### POST /alert
Crear nueva alerta.

### GET /alerts/pending
Obtener alertas pendientes de envío.

### POST /alerts/:id/sent
Marcar alerta como enviada.

## 🗄️ Base de Datos

### Estructura
La base de datos SQLite incluye tablas para:
- **producers**: Productores autorizados
- **conversations**: Historial de mensajes
- **forms**: Formularios por productor
- **form_logs**: Bitácora diaria
- **tasks**: Tareas y su avance
- **alerts**: Alertas de intervención
- **agent_configs**: Configuración de agentes

### Inicialización
La base de datos se crea automáticamente al iniciar el servicio por primera vez.

## 🚢 Despliegue en Leapcell

### Paso 1: Crear Proyecto
1. Ir a [Leapcell](https://leapcell.io)
2. New Project → Connect GitHub
3. Seleccionar este repositorio
4. Root Directory: `service-2-backend`

### Paso 2: Configuración
```
Build Command: pip install -r requirements.txt
Start Command: python app.py
Port: 5000
```

### Paso 3: Variables de Entorno
⚠️ **IMPORTANTE**: Configurar `MODEL_API_URL` con la URL del Servicio 1

En el panel de Leapcell:
```
MODEL_API_URL=https://tu-servicio-1.leapcell.dev
DATABASE_PATH=/app/instance/app.db
DEFAULT_TIMEZONE=America/Lima
DAILY_CHECKIN_HOUR=8
```

### Paso 4: Configurar Volumen Persistente
⚠️ **CRÍTICO**: SQLite necesita volumen persistente

1. En Leapcell, ir a "Storage" o "Volumes"
2. Crear volumen persistente
3. Montar en: `/app/instance`
4. Esto persistirá la base de datos entre deploys

### Paso 5: Deploy
1. Click en Deploy
2. Esperar build
3. Verificar logs de inicialización
4. Anotar URL: `https://tu-servicio-2.leapcell.dev`

### Paso 6: Configurar Panel Admin
1. Acceder a `https://tu-servicio-2.leapcell.dev/admin`
2. Configurar agentes (roles: formulario, consulta, intervención)
3. Agregar productores autorizados
4. Ajustar prompts según necesidad

### Paso 7: Probar
```bash
# Health check
curl https://tu-servicio-2.leapcell.dev/health

# Probar endpoint /agent (debe tener productor autorizado)
curl -X POST https://tu-servicio-2.leapcell.dev/agent \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "51987654321@c.us",
    "message": "Hola",
    "role": "consulta"
  }'
```

## 🔗 Integración con Otros Servicios

### Con Servicio 1 (Model API)
Este servicio llama al Servicio 1 para inferencia del modelo.
```
Servicio 2 → POST /chat → Servicio 1
```

### Con Servicio 3 (WhatsApp)
El Servicio 3 llama a este servicio para procesar mensajes.
```
Servicio 3 → POST /agent → Servicio 2
```

## ⚠️ Consideraciones de Seguridad

### Autenticación
Actualmente el panel `/admin` no tiene autenticación.

**Recomendaciones para producción:**
1. Agregar autenticación básica
2. Usar variables de entorno para credenciales
3. Implementar JWT o session-based auth

### Productores Autorizados
Solo productores marcados como `allowed=1` pueden usar el servicio.
Configurar en `/admin/producers`.

### Rate Limiting
Considerar agregar rate limiting para evitar abuso:
```python
from flask_limiter import Limiter
```

## 📊 Monitoreo

### Logs
- Ver logs en panel de Leapcell
- Revisar errores de conexión con Servicio 1
- Monitorear tiempo de respuesta

### Métricas
- Número de mensajes procesados
- Formularios completados
- Alertas generadas
- Check-ins diarios

## 🐛 Troubleshooting

### Error: "Cannot connect to Model API"
- Verificar `MODEL_API_URL`
- Asegurar que Servicio 1 está desplegado
- Probar health check del Servicio 1

### Error: "Database locked"
- Normal en SQLite con alta concurrencia
- Considerar migrar a PostgreSQL si es frecuente

### Base de datos se resetea
- Verificar que volumen persistente está montado correctamente
- Path debe ser `/app/instance` para `app.db`

### Panel /admin no carga
- Verificar que carpeta `templates/` existe
- Ver logs para errores de template rendering

### Productor no autorizado (403)
- Ir a `/admin/producers`
- Agregar productor con `allowed=1`
- Verificar que el phone match exactamente

## 🔄 Flujo de Procesamiento

```
1. Recibe POST /agent
   ↓
2. Verifica si productor está autorizado
   ↓
3. Construye contexto (historial, formulario, etc)
   ↓
4. Llama a Servicio 1 (Model API)
   ↓
5. Procesa respuesta del modelo
   ↓
6. Actualiza base de datos (formulario, logs, etc)
   ↓
7. Devuelve respuesta al cliente
```

## 📚 Referencias
- [Flask docs](https://flask.palletsprojects.com/)
- [SQLite docs](https://www.sqlite.org/docs.html)
- [Leapcell docs](https://docs.leapcell.io)
