#!/bin/bash

# Script para iniciar el Model API (servicio de inferencia del modelo)

echo "🤖 Iniciando Model API..."
echo "📍 Model API se ejecutará en: http://localhost:8001"
echo ""
echo "Para detener el servidor, presiona Ctrl+C"
echo "================================================"
echo ""

# Verificar que Python está instalado
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null
then
    echo "❌ Error: Python no está instalado"
    exit 1
fi

# Usar python3 si está disponible, sino python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Verificar que el modelo existe
if [ ! -f "models/qwen2.5-0.5b-instruct-q4_k_m.gguf" ]; then
    echo "⚠️  Modelo no encontrado en models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    echo ""
    echo "Descarga el modelo con:"
    echo "  mkdir -p models"
    echo "  wget -O models/qwen2.5-0.5b-instruct-q4_k_m.gguf \\"
    echo "    https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
    echo ""
    echo "El servidor puede iniciarse sin el modelo, pero no funcionará la inferencia de IA."
    echo "Presiona Enter para continuar de todos modos o Ctrl+C para cancelar..."
    read
fi

# Iniciar el servidor
$PYTHON_CMD model_api.py
