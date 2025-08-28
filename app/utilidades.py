"""
Funciones auxiliares para el Agente Excel IA
"""
import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

def validar_archivo_excel(archivo) -> Dict[str, Any]:
    """
    Valida si el archivo subido es un Excel válido
    
    Args:
        archivo: Archivo subido por Streamlit
    
    Returns:
        Dict con información de validación
    """
    resultado = {
        "valido": False,
        "error": None,
        "extension": None,
        "tamaño_mb": 0
    }
    
    try:
        # Verificar extensión
        nombre = archivo.name.lower()
        extensiones_validas = ['.xlsx', '.xls', '.xlsm', '.csv']
        
        extension = None
        for ext in extensiones_validas:
            if nombre.endswith(ext):
                extension = ext
                break
        
        if not extension:
            resultado["error"] = "Archivo debe ser Excel (.xlsx, .xls, .xlsm, .csv)"
            return resultado
        
        # Verificar tamaño
        tamaño_bytes = len(archivo.getvalue())
        tamaño_mb = tamaño_bytes / (1024 * 1024)
        
        if tamaño_mb > 100:  # Límite de 100MB
            resultado["error"] = f"Archivo muy grande: {tamaño_mb:.1f}MB (máximo 100MB)"
            return resultado
        
        resultado.update({
            "valido": True,
            "extension": extension,
            "tamaño_mb": tamaño_mb
        })
        
    except Exception as e:
        resultado["error"] = f"Error al validar archivo: {str(e)}"
    
    return resultado

def cargar_excel_completo(archivo) -> Dict[str, Any]:
    """
    Carga un archivo Excel completo con todas sus hojas
    
    Args:
        archivo: Archivo Excel
    
    Returns:
        Dict con información del archivo y dataframes
    """
    resultado = {
        "exito": False,
        "error": None,
        "hojas": [],
        "dataframes": {},
        "info_general": {}
    }
    
    try:
        # Leer todas las hojas
        excel_file = pd.ExcelFile(archivo)
        hojas = excel_file.sheet_names
        
        dataframes = {}
        info_hojas = []
        
        for hoja in hojas:
            try:
                df = pd.read_excel(archivo, sheet_name=hoja)
                dataframes[hoja] = df
                
                info_hojas.append({
                    "nombre": hoja,
                    "filas": len(df),
                    "columnas": len(df.columns),
                    "tiene_datos": not df.empty
                })
                
            except Exception as e:
                info_hojas.append({
                    "nombre": hoja,
                    "error": f"Error al leer: {str(e)}"
                })
        
        resultado.update({
            "exito": True,
            "hojas": info_hojas,
            "dataframes": dataframes,
            "info_general": {
                "nombre_archivo": archivo.name,
                "total_hojas": len(hojas),
                "hojas_con_datos": sum(1 for h in info_hojas if h.get("tiene_datos", False))
            }
        })
        
    except Exception as e:
        resultado["error"] = f"Error al cargar Excel: {str(e)}"
    
    return resultado

def formatear_numero(numero: float, decimales: int = 2) -> str:
    """Formatea números para mostrar"""
    if numero >= 1_000_000:
        return f"{numero/1_000_000:.{decimales}f}M"
    elif numero >= 1_000:
        return f"{numero/1_000:.{decimales}f}K"
    else:
        return f"{numero:.{decimales}f}"

def generar_nombre_archivo(prefijo: str, extension: str = ".md") -> str:
    """Genera nombre único para archivo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefijo}_{timestamp}{extension}"

def guardar_reporte(contenido: str, nombre_archivo: str, directorio: str = "data/reportes") -> str:
    """
    Guarda un reporte en archivo
    
    Args:
        contenido: Contenido del reporte
        nombre_archivo: Nombre del archivo
        directorio: Directorio donde guardar
    
    Returns:
        Ruta del archivo guardado
    """
    try:
        # Crear directorio si no existe
        Path(directorio).mkdir(parents=True, exist_ok=True)
        
        # Ruta completa
        ruta_completa = os.path.join(directorio, nombre_archivo)
        
        # Guardar archivo
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        return ruta_completa
        
    except Exception as e:
        st.error(f"Error al guardar reporte: {str(e)}")
        return None

def mostrar_metricas_resumen(info_archivo: Dict[str, Any]):
    """Muestra métricas resumidas del archivo"""
    if not info_archivo.get("exito"):
        return
    
    info = info_archivo["info_general"]
    hojas = info_archivo["hojas"]
    
    # Calcular totales
    total_filas = sum(h.get("filas", 0) for h in hojas if "filas" in h)
    total_columnas = sum(h.get("columnas", 0) for h in hojas if "columnas" in h)
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Hojas", info["total_hojas"])
    
    with col2:
        st.metric("Filas totales", formatear_numero(total_filas, 0))
    
    with col3:
        st.metric("Columnas totales", formatear_numero(total_columnas, 0))
    
    with col4:
        hojas_con_datos = info["hojas_con_datos"]
        st.metric("Hojas con datos", f"{hojas_con_datos}/{info['total_hojas']}")

def crear_mensaje_error(error: str, solucion: Optional[str] = None) -> None:
    """Muestra mensaje de error formateado"""
    st.error(f"❌ **Error:** {error}")
    if solucion:
        st.info(f"💡 **Solución:** {solucion}")

def crear_mensaje_exito(mensaje: str) -> None:
    """Muestra mensaje de éxito formateado"""
    st.success(f"✅ {mensaje}")

def crear_mensaje_info(mensaje: str) -> None:
    """Muestra mensaje informativo formateado"""
    st.info(f"ℹ️ {mensaje}")