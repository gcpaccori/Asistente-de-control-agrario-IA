#!/bin/bash

# Script de inicio para el Asistente de Control Agrario IA
# Este script inicia el backend principal del sistema

echo "🚀 Iniciando Asistente de Control Agrario IA..."
echo "📍 Backend se ejecutará en: http://localhost:5000"
echo "📊 Panel de admin en: http://localhost:5000/admin"
echo ""
echo "Para detener el servidor, presiona Ctrl+C"
echo "================================================"
echo ""

# Verificar que Python está instalado
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null
then
    echo "❌ Error: Python no está instalado"
    echo "Instala Python 3.10+ desde: https://www.python.org/downloads/"
    exit 1
fi

# Usar python3 si está disponible, sino python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Verificar que las dependencias están instaladas
if ! $PYTHON_CMD -c "import flask" 2> /dev/null; then
    echo "⚠️  Dependencias no instaladas. Instalando..."
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
    echo "✅ Dependencias instaladas"
    echo ""
fi

# Iniciar el servidor
$PYTHON_CMD app.py
