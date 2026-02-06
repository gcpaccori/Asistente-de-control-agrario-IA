#!/bin/bash
# 1. Instalar herramientas de sistema necesarias para compilar Qwen
apt-get update && apt-get install -y cmake build-essential gcc g++

# 2. Instalar Gunicorn (el servidor web) explícitamente
pip install gunicorn

# 3. Instalar las dependencias de tu proyecto
pip install -r requirements.txt
