#!/usr/bin/env python3
"""
Script para verificar que el setup está listo para Vercel.
"""
from __future__ import annotations

import sys
from pathlib import Path

def check_file_exists(path: str, description: str) -> bool:
    """Verifica que un archivo existe."""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description} no encontrado: {path}")
        return False

def check_vercel_files() -> bool:
    """Verifica archivos de configuración de Vercel."""
    print("\n=== Verificando archivos de Vercel ===")
    checks = [
        check_file_exists("vercel.json", "Configuración de Vercel"),
        check_file_exists("api/index.py", "Entry point serverless"),
        check_file_exists(".vercelignore", "Archivo .vercelignore"),
        check_file_exists("requirements.txt", "Dependencias Python"),
    ]
    return all(checks)

def check_imports() -> bool:
    """Verifica que el app se puede importar sin llama-cpp-python."""
    print("\n=== Verificando imports de Python ===")
    try:
        import flask
        print("✅ Flask instalado")
    except ImportError:
        print("❌ Flask no instalado. Ejecuta: pip install Flask")
        return False
    
    try:
        import requests
        print("✅ Requests instalado")
    except ImportError:
        print("❌ Requests no instalado. Ejecuta: pip install requests")
        return False
    
    try:
        sys.path.insert(0, str(Path.cwd()))
        from app import app as flask_app
        print("✅ app.py se puede importar sin llama-cpp-python")
        
        # Verificar que el app tiene las rutas básicas
        routes = [rule.rule for rule in flask_app.url_map.iter_rules()]
        if "/health" in routes:
            print("✅ Ruta /health encontrada")
        else:
            print("❌ Ruta /health no encontrada")
            return False
            
        if "/agent" in routes:
            print("✅ Ruta /agent encontrada")
        else:
            print("❌ Ruta /agent no encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Error al importar app.py: {e}")
        return False
    
    return True

def check_whatsapp_config() -> bool:
    """Verifica configuración del puente WhatsApp."""
    print("\n=== Verificando configuración WhatsApp ===")
    checks = [
        check_file_exists("whatsapp/package.json", "Configuración Node.js"),
        check_file_exists("whatsapp/index.js", "Script WhatsApp"),
    ]
    return all(checks)

def check_documentation() -> bool:
    """Verifica que la documentación existe."""
    print("\n=== Verificando documentación ===")
    checks = [
        check_file_exists("docs/vercel-deployment.md", "Guía de deployment"),
        check_file_exists("docs/vercel-quickstart.md", "Guía de inicio rápido"),
        check_file_exists("README.md", "README principal"),
    ]
    return all(checks)

def main():
    """Función principal."""
    print("🔍 Verificando setup para Vercel...")
    print("=" * 60)
    
    results = [
        check_vercel_files(),
        check_imports(),
        check_whatsapp_config(),
        check_documentation(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ¡Todo listo para desplegar en Vercel!")
        print("\nPróximos pasos:")
        print("1. Configura MODEL_API_URL en Vercel")
        print("2. Ejecuta: vercel")
        print("3. Lee docs/vercel-quickstart.md para más detalles")
        return 0
    else:
        print("❌ Hay problemas que necesitan ser resueltos")
        print("\nRevisa los errores arriba y corrígelos antes de desplegar")
        return 1

if __name__ == "__main__":
    sys.exit(main())
