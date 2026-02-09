# Makefile para Asistente de Control Agrario IA
# Comandos de conveniencia para desarrollo local

.PHONY: help build start start-backend start-model start-whatsapp install-python install-whatsapp install-all test validate download-model clean

# Comando por defecto
help:
	@echo "🌾 Asistente de Control Agrario IA - Comandos Disponibles"
	@echo ""
	@echo "BUILD (Instalar dependencias):"
	@echo "  make build              Instala todas las dependencias (Python + Node.js)"
	@echo "  make install-python     Instala solo dependencias Python"
	@echo "  make install-whatsapp   Instala solo dependencias Node.js"
	@echo ""
	@echo "START (Ejecutar servicios):"
	@echo "  make start             Inicia el backend principal (puerto 5000)"
	@echo "  make start-backend     Alias de 'make start'"
	@echo "  make start-model       Inicia el Model API (puerto 8001)"
	@echo "  make start-whatsapp    Inicia el WhatsApp Bridge"
	@echo ""
	@echo "OTROS:"
	@echo "  make test              Ejecuta tests de integración"
	@echo "  make validate          Valida la carga del modelo"
	@echo "  make download-model    Descarga el modelo Qwen 0.5B"
	@echo "  make clean             Limpia archivos temporales"
	@echo ""
	@echo "EJEMPLOS:"
	@echo "  make build && make start    # Instalar y ejecutar"
	@echo "  ./start.sh                  # Ejecutar con script bash"
	@echo "  npm start                   # Ejecutar con npm"
	@echo ""

# BUILD: Instalar dependencias
build: install-all

install-all: install-python install-whatsapp
	@echo "✅ Todas las dependencias instaladas"

install-python:
	@echo "📦 Instalando dependencias Python..."
	pip install -r requirements.txt
	@echo "✅ Dependencias Python instaladas"

install-whatsapp:
	@echo "📦 Instalando dependencias Node.js para WhatsApp..."
	cd whatsapp && npm install
	@echo "✅ Dependencias Node.js instaladas"

# START: Ejecutar servicios
start: start-backend

start-backend:
	@echo "🚀 Iniciando backend principal..."
	@echo "📍 Backend: http://localhost:5000"
	@echo "📊 Admin: http://localhost:5000/admin"
	python app.py

start-model:
	@echo "🤖 Iniciando Model API..."
	@echo "📍 Model API: http://localhost:8001"
	python model_api.py

start-whatsapp:
	@echo "📱 Iniciando WhatsApp Bridge..."
	cd whatsapp && FLASK_URL=http://localhost:5000 npm start

# TEST: Pruebas
test:
	@echo "🧪 Ejecutando tests de integración..."
	python test_qwen_0.5b_integration.py

validate:
	@echo "🔍 Validando modelo..."
	python validate_local_gguf.py

# DOWNLOAD: Descargar modelo
download-model:
	@echo "⬇️  Descargando modelo Qwen 0.5B..."
	@mkdir -p models
	wget -O models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
		https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
	@echo "✅ Modelo descargado"

# CLEAN: Limpiar archivos temporales
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	@echo "✅ Limpieza completada"
