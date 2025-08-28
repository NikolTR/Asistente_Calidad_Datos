"""
Configuraciones generales del Agente Excel IA
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Configuracion:
    """Configuraciones del sistema"""
    
    # Ollama
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    MODELO_IA = os.getenv("MODELO_IA", "llama3.1")
    
    # Aplicación
    PUERTO_APP = int(os.getenv("PUERTO_APP", "8501"))
    DIRECTORIO_DATOS = os.getenv("DIRECTORIO_DATOS", "./datos/")
    LIMITE_ARCHIVO_MB = int(os.getenv("LIMITE_ARCHIVO_MB", "50"))
    
    # Rutas
    RUTA_SUBIDOS = os.path.join(DIRECTORIO_DATOS, "subidos")
    RUTA_REPORTES = os.path.join(DIRECTORIO_DATOS, "reportes")
    
    # Análisis de datos
    COLUMNAS_MAXIMAS = 100
    FILAS_MUESTRA = 1000
    
    # Visualizaciones
    COLORES_GRAFICOS = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", 
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
    ]
    
    @classmethod
    def verificar_configuracion(cls):
        """Verifica que la configuración sea válida"""
        errores = []
        
        if not os.path.exists(cls.DIRECTORIO_DATOS):
            errores.append(f"Directorio de datos no existe: {cls.DIRECTORIO_DATOS}")
        
        if cls.LIMITE_ARCHIVO_MB <= 0:
            errores.append("El límite de archivo debe ser mayor a 0")
        
        return errores