# Contrato MML ↔ Flask (roles A/B/C)

Este contrato define la **entrada** y **salida** del modelo de lenguaje (MML)
en tres roles: `formulario`, `consulta` e `intervencion`.

## Principios
- El MML **no** llama APIs ni bases de datos directamente.
- El MML **solo** devuelve JSON estricto.
- Flask **orquesta**: prepara contexto, interpreta JSON y persiste datos.
- El MML **no inventa** datos que no estén en el contexto.

---

## Entrada al MML (desde Flask)
### Campos base
```json
{
  "role": "formulario | consulta | intervencion",
  "producer": {
    "id": 123,
    "phone": "+519XXXXXXXX",
    "zone": "Cusco - San Sebastián",
    "preferred_language": "es",
    "main_crops": ["papa", "maiz"]
  },
  "form_state": {
    "cultivo": null,
    "sintoma": "hojas amarillas",
    "inicio_problema": null,
    "foto_recibida": false
  },
  "recent_chat": [
    "U: mi papa esta amarilla",
    "A: ¿Desde cuándo lo notas?",
    "U: hace 3 dias"
  ],
  "weekly_summary": "7d: papa—amarillamiento (2 veces), riego AM recomendado, sin mejora reportada.",
  "last_user_message": "hace 3 dias"
}
```

### Qué enviar por rol
- **formulario**: `producer`, `form_state`, `recent_chat`, `last_user_message`.
- **consulta**: `producer`, `weekly_summary`, `recent_chat` (corto), `last_user_message`.
- **intervencion**: `producer`, `weekly_summary` (o eventos 7d) y `last_user_message` opcional.

---

## Salida del MML (a Flask)
### Estructura base (siempre igual)
```json
{
  "role": "formulario | consulta | intervencion",
  "respuesta_chat": "Texto para enviar al productor.",
  "acciones": {
    "actualizar_formulario": {},
    "alerta": null,
    "log": null
  },
  "estado": {
    "formulario_completo": false,
    "confianza": 0.0
  }
}
```

---

## Rol: formulario
### Objetivo
Extraer información faltante y completar el formulario conversando.

### Ejemplo de salida
```json
{
  "role": "formulario",
  "respuesta_chat": "¿Desde cuándo notas ese problema en el cultivo?",
  "acciones": {
    "actualizar_formulario": {
      "cultivo": "maiz",
      "sintoma": "hojas amarillas",
      "inicio_problema": "hace 3 dias"
    },
    "alerta": null,
    "log": "Identificado cultivo y sintoma"
  },
  "estado": {
    "formulario_completo": false,
    "confianza": 0.62
  }
}
```

### Reglas
- `actualizar_formulario` **solo** contiene campos nuevos.
- No borrar datos previos.
- `formulario_completo = true` cuando no falte nada.

---

## Rol: consulta
### Objetivo
Responder usando **solo** el contexto conocido del productor.

### Ejemplo de salida
```json
{
  "role": "consulta",
  "respuesta_chat": "Según lo registrado esta semana, el estrés hídrico puede mejorar aumentando el riego por la mañana.",
  "acciones": {
    "actualizar_formulario": {},
    "alerta": null,
    "log": "Respuesta basada en historial semanal"
  },
  "estado": {
    "formulario_completo": true,
    "confianza": 0.84
  }
}
```

---

## Rol: intervencion
### Objetivo
Detectar persistencia o riesgo y generar alerta.

### Ejemplo de salida
```json
{
  "role": "intervencion",
  "respuesta_chat": "El problema se ha repetido varios días. Es importante revisar hoy el riego o coordinar asistencia técnica.",
  "acciones": {
    "actualizar_formulario": {},
    "alerta": {
      "nivel": "alto",
      "motivo": "Problema persistente 7 dias",
      "accion_recomendada": "Contacto técnico"
    },
    "log": "Activada alerta por persistencia"
  },
  "estado": {
    "formulario_completo": true,
    "confianza": 0.91
  }
}
```

---

## Errores / contexto insuficiente
Si el MML no tiene suficiente información:
```json
{
  "role": "formulario",
  "respuesta_chat": "Necesito un poco más de información para ayudarte.",
  "acciones": {
    "actualizar_formulario": {},
    "alerta": null,
    "log": "Contexto insuficiente"
  },
  "estado": {
    "formulario_completo": false,
    "confianza": 0.3
  }
}
```
