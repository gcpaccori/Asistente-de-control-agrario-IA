# 📋 Referencia Rápida de Comandos

## 🔨 BUILD (Instalar dependencias)

| Comando | Descripción |
|---------|-------------|
| `pip install -r requirements.txt` | Instalar dependencias Python |
| `npm run install:python` | Instalar dependencias Python (con npm) |
| `make build` | Instalar todas las dependencias (Makefile) |
| `make install-python` | Instalar solo dependencias Python (Makefile) |

## 🚀 START (Ejecutar servidor)

### Backend Principal (Puerto 5000)
| Comando | Descripción |
|---------|-------------|
| `python app.py` | Ejecutar directamente con Python |
| `npm start` | Ejecutar con npm |
| `./start.sh` | Ejecutar con script bash |
| `make start` | Ejecutar con Makefile |

**URLs:**
- Backend: http://localhost:5000
- Admin: http://localhost:5000/admin
- Health: http://localhost:5000/health

### Model API (Puerto 8001)
| Comando | Descripción |
|---------|-------------|
| `python model_api.py` | Ejecutar directamente con Python |
| `npm run start:model` | Ejecutar con npm |
| `./start-model.sh` | Ejecutar con script bash |
| `make start-model` | Ejecutar con Makefile |

**URLs:**
- Model API: http://localhost:8001
- Health: http://localhost:8001/health

### WhatsApp Bridge
| Comando | Descripción |
|---------|-------------|
| `cd whatsapp && npm start` | Ejecutar desde directorio whatsapp |
| `npm run start:whatsapp` | Ejecutar desde raíz con npm |
| `./start-whatsapp.sh` | Ejecutar con script bash |
| `make start-whatsapp` | Ejecutar con Makefile |

## 🧪 TEST (Pruebas)

| Comando | Descripción |
|---------|-------------|
| `python test_qwen_0.5b_integration.py` | Tests de integración |
| `npm test` | Tests con npm |
| `make test` | Tests con Makefile |
| `python validate_local_gguf.py` | Validar modelo |
| `npm run validate` | Validar modelo con npm |

## 📥 DOWNLOAD (Descargar modelo)

| Comando | Descripción |
|---------|-------------|
| `npm run download:model` | Descargar modelo con npm |
| `make download-model` | Descargar modelo con Makefile |

O manualmente:
```bash
mkdir -p models
wget -O models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

## 🧹 CLEAN (Limpiar)

| Comando | Descripción |
|---------|-------------|
| `make clean` | Limpiar archivos temporales |

## 🎯 Flujos de Trabajo Comunes

### Primera vez (instalación completa)
```bash
# Opción 1: Con npm
npm run install:all

# Opción 2: Con Makefile
make build

# Opción 3: Manual
pip install -r requirements.txt
cd whatsapp && npm install
```

### Desarrollo diario (solo backend)
```bash
# Opción 1: Script bash (recomendado)
./start.sh

# Opción 2: Con npm
npm start

# Opción 3: Con Makefile
make start

# Opción 4: Directo con Python
python app.py
```

### Desarrollo completo (3 servicios)
```bash
# Terminal 1: Model API
npm run start:model
# o: ./start-model.sh
# o: make start-model

# Terminal 2: Backend
npm run start:backend
# o: ./start.sh
# o: make start

# Terminal 3: WhatsApp
npm run start:whatsapp
# o: ./start-whatsapp.sh
# o: make start-whatsapp
```

### Testing
```bash
# Ejecutar tests
npm test
# o: make test

# Validar modelo
npm run validate
# o: make validate
```

## 🌍 Variables de Entorno

### Backend (app.py)
```bash
export DATABASE_PATH=/ruta/a/base.db
export LOCAL_MODEL_PATH=/ruta/a/modelo.gguf
export N_CTX=2048
export N_THREADS=1
```

### WhatsApp
```bash
export FLASK_URL=http://localhost:5000
```

### Model API (si separado)
```bash
export LOCAL_MODEL_PATH=/ruta/a/modelo.gguf
export N_CTX=2048
export N_THREADS=1
```

## 📂 Estructura de Servicios

```
raíz/
├── app.py              → Backend principal (puerto 5000)
├── model_api.py        → Model API (puerto 8001)
├── whatsapp/           → WhatsApp Bridge
│   └── index.js
├── service-1-model/    → Model API (alternativo)
├── service-2-backend/  → Backend (alternativo)
└── service-3-whatsapp/ → WhatsApp (alternativo)
```

## 🔧 Troubleshooting Rápido

| Error | Solución |
|-------|----------|
| "No module named 'flask'" | `pip install -r requirements.txt` |
| "No se encontró el modelo" | `npm run download:model` o descargar manualmente |
| "Address already in use" | Matar proceso: `lsof -i :5000` y `kill -9 <PID>` |
| "Node.js not found" | Instalar Node.js desde nodejs.org |
| "Python not found" | Instalar Python 3.10+ desde python.org |

## 📚 Documentación Completa

- **Cómo ejecutar:** [`COMO_EJECUTAR.md`](COMO_EJECUTAR.md)
- **Guía rápida:** [`QUICK_START.md`](QUICK_START.md)
- **Despliegue:** [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)
- **Arquitectura:** [`docs/ARQUITECTURA_DESPLIEGUE.md`](docs/ARQUITECTURA_DESPLIEGUE.md)

---

**💡 Tip:** Para ver todos los comandos disponibles con Makefile, ejecuta: `make help`
