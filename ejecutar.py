#!/usr/bin/env python3
"""
Script principal para ejecutar el Agente Excel IA
"""
import os
import sys
import subprocess
from pathlib import Path

def verificar_ollama():
    """Verifica si Ollama está ejecutándose"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def crear_directorios():
    """Crea los directorios necesarios"""
    directorios = [
        "datos/subidos",
        "datos/reportes"
    ]
    
    for directorio in directorios:
        Path(directorio).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {directorio}")

def main():
    print("🚀 Iniciando Agente Excel IA...")
    
    # Crear directorios necesarios
    crear_directorios()
    
    # Verificar Ollama
    if not verificar_ollama():
        print("❌ Error: Ollama no está ejecutándose")
        print("💡 Inicia Ollama primero con: ollama serve")
        print("💡 Y descarga el modelo con: ollama pull llama3.1")
        sys.exit(1)
    
    print("✅ Ollama está ejecutándose")
    
    # Ejecutar Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/main.py", 
            "--server.port=8501",
            "--server.headless=true"
        ])
    except KeyboardInterrupt:
        print("\n👋 Agente Excel IA terminado")

if __name__ == "__main__":
    main()