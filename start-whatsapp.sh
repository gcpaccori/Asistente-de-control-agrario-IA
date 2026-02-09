#!/bin/bash

# Script para iniciar el WhatsApp Bridge

echo "📱 Iniciando WhatsApp Bridge..."
echo ""
echo "Este servicio conecta el sistema con WhatsApp Web"
echo "================================================"
echo ""

# Verificar que Node.js está instalado
if ! command -v node &> /dev/null
then
    echo "❌ Error: Node.js no está instalado"
    echo "Instala Node.js desde: https://nodejs.org/"
    exit 1
fi

# Cambiar al directorio de WhatsApp
if [ -d "whatsapp" ]; then
    cd whatsapp
elif [ -d "service-3-whatsapp" ]; then
    cd service-3-whatsapp
else
    echo "❌ Error: Directorio de WhatsApp no encontrado"
    exit 1
fi

# Verificar que las dependencias están instaladas
if [ ! -d "node_modules" ]; then
    echo "⚠️  Dependencias no instaladas. Instalando..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
    echo "✅ Dependencias instaladas"
    echo ""
fi

# Configurar URL del backend si no está definida
if [ -z "$FLASK_URL" ]; then
    export FLASK_URL="http://localhost:5000"
    echo "📌 Usando FLASK_URL por defecto: $FLASK_URL"
    echo ""
fi

echo "🔄 Iniciando conexión con WhatsApp Web..."
echo "📲 Escanea el código QR con tu teléfono"
echo ""

# Iniciar el servicio
npm start
