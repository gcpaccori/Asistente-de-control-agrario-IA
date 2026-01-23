# Pruebas locales GGUF (Qwen2.5-3B-Instruct Q4_K_M)

Estas pruebas se ejecutaron con `llama-cpp-python` en CPU (n_ctx=2048, n_threads=4).

## Rol: system

### system_json_confirm

**Salida:**

```
{"role": "system", "ok": true}
```

### system_si_no

**Salida:**

```
SI
```

### system_json_list

**Salida:**

```
{"tareas": ["Recopilar datos de la tierra", "Planificar y ejecutar la obra", "Monitorizar y gestionar el proyecto"]}
```

## Rol: assistant

### assistant_json_confirm

**Salida:**

```
{"role": "assistant", "ok": true}
```

### assistant_context

**Salida:**

```
"Se ha producido una sequía en el campo, recomendamos buscar soluciones para la agricultura."
```

### assistant_json_action

**Salida:**

```
{"accion": "tratamiento", "prioridad": 5}
```

## Rol: user

### user_single_sentence

**Salida:**

```
Un modelo GGUF es un tipo de modelo de aprendizaje automático que se basa en la generación de imágenes.
```

### user_json_extract

**Salida:**

```
{ "clavesconsulta": "necesito riego", "cultivo": "maíz" }
```

### user_bullets

**Salida:**

```
1. **Identifica el producto**: Se debe identificar el tipo de producto que se desea registrar, como una marca, un producto específico, o un servicio.

2. **Define el producto**: Se debe definir el nombre, la marca, el modelo, el modelo de fabricación, y cualquier otros detalles relevantes sobre el producto.

3. **Define el precio**: Se debe definir el precio del producto, si es una marca, un producto específico, o un
```
