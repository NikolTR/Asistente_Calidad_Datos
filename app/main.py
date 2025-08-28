
"""
Aplicación principal del Agente Excel IA
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
import os

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Importaciones corregidas
from app.agente import AgenteExcelIA
from app.utilidades import (
    validar_archivo_excel, cargar_excel_completo, 
    mostrar_metricas_resumen, crear_mensaje_error,
    crear_mensaje_exito, crear_mensaje_info
)

# Configuración de la página
st.set_page_config(
    page_title="Agente Excel IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.problem-high {
    background-color: #ffebee;
    border-left: 4px solid #f44336;
    padding: 1rem;
    margin: 0.5rem 0;
}

.problem-medium {
    background-color: #fff3e0;
    border-left: 4px solid #ff9800;
    padding: 1rem;
    margin: 0.5rem 0;
}

.problem-low {
    background-color: #e8f5e8;
    border-left: 4px solid #4caf50;
    padding: 1rem;
    margin: 0.5rem 0;
}

.chat-container {
    background-color: #fafafa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def inicializar_sesion():
    """Inicializa variables de sesión"""
    if "agente" not in st.session_state:
        st.session_state.agente = AgenteExcelIA()
    
    if "archivo_cargado" not in st.session_state:
        st.session_state.archivo_cargado = False
    
    if "info_archivo" not in st.session_state:
        st.session_state.info_archivo = None
    
    if "resultado_analisis" not in st.session_state:
        st.session_state.resultado_analisis = None
    
    if "historial_chat" not in st.session_state:
        st.session_state.historial_chat = []

def mostrar_header():
    """Muestra el header principal"""
    st.markdown('<div class="main-header">📊 Agente Excel IA</div>', unsafe_allow_html=True)
    st.markdown("---")

def mostrar_sidebar():
    """Muestra la barra lateral con información del sistema"""
    with st.sidebar:
        st.header("🔧 Estado del Sistema")
        
        # Verificar conexión con Ollama
        estado_ollama = st.session_state.agente.verificar_conexion_ollama()
        
        if estado_ollama["conectado"]:
            if estado_ollama["modelo_disponible"]:
                st.success("✅ Ollama conectado")
                st.success(f"✅ Modelo {st.session_state.agente.configuracion.MODELO_IA} disponible")
            else:
                st.warning("⚠️ Ollama conectado pero modelo no disponible")
                st.info("Modelos disponibles:")
                for modelo in estado_ollama.get("modelos", []):
                    st.write(f"- {modelo}")
        else:
            st.error("❌ Ollama no conectado")
            st.error(f"Error: {estado_ollama.get('error', 'Desconocido')}")
        
        st.markdown("---")
        
        # Información del archivo cargado
        if st.session_state.archivo_cargado and st.session_state.info_archivo:
            st.header("📁 Archivo Actual")
            info = st.session_state.info_archivo["info_general"]
            st.write(f"**Nombre:** {info['nombre_archivo']}")
            st.write(f"**Hojas:** {info['total_hojas']}")
            st.write(f"**Con datos:** {info['hojas_con_datos']}")
            
            if st.session_state.resultado_analisis:
                puntuacion = st.session_state.resultado_analisis["puntuacion_calidad"]
                color = "🟢" if puntuacion >= 80 else "🟡" if puntuacion >= 60 else "🔴"
                st.write(f"**Calidad:** {color} {puntuacion:.1f}/100")
        
        st.markdown("---")
        
        # Acciones rápidas
        st.header("⚡ Acciones Rápidas")
        
        if st.button("🔄 Reiniciar Análisis"):
            st.session_state.archivo_cargado = False
            st.session_state.info_archivo = None
            st.session_state.resultado_analisis = None
            st.session_state.historial_chat = []
            st.rerun()
        
        if st.button("💾 Limpiar Cache"):
            st.cache_data.clear()
            crear_mensaje_exito("Cache limpiado")

def cargar_archivo():
    """Interfaz para cargar archivo Excel"""
    st.header("📤 Cargar Archivo Excel")
    
    archivo_subido = st.file_uploader(
        "Selecciona tu archivo Excel",
        type=['xlsx', 'xls', 'xlsm'],
        help="Archivos soportados: .xlsx, .xls, .xlsm (máximo 50MB)"
    )
    
    if archivo_subido is not None:
        # Validar archivo
        validacion = validar_archivo_excel(archivo_subido)
        
        if not validacion["valido"]:
            crear_mensaje_error(validacion["error"])
            return False
        
        # Mostrar información básica
        st.info(f"📁 {archivo_subido.name} ({validacion['tamaño_mb']:.1f} MB)")
        
        # Botón para procesar
        if st.button("🚀 Analizar Archivo", type="primary"):
            with st.spinner("Cargando y analizando archivo..."):
                # Cargar archivo
                info_archivo = cargar_excel_completo(archivo_subido)
                
                if not info_archivo["exito"]:
                    crear_mensaje_error(info_archivo["error"])
                    return False
                
                # Realizar análisis
                resultado_analisis = st.session_state.agente.analizador.analizar_archivo_completo(info_archivo)
                
                if "error" in resultado_analisis:
                    crear_mensaje_error(resultado_analisis["error"])
                    return False
                
                # Guardar en sesión
                st.session_state.info_archivo = info_archivo
                st.session_state.resultado_analisis = resultado_analisis
                st.session_state.archivo_cargado = True
                
                crear_mensaje_exito("¡Archivo analizado exitosamente!")
                st.rerun()
    
    return False

def mostrar_vista_previa():
    """Muestra vista previa del archivo"""
    if not st.session_state.archivo_cargado:
        return
    
    st.header("👀 Vista Previa del Archivo")
    
    # Métricas generales
    mostrar_metricas_resumen(st.session_state.info_archivo)
    
    # Selector de hoja
    hojas_con_datos = [
        h["nombre"] for h in st.session_state.info_archivo["hojas"] 
        if h.get("tiene_datos", False)
    ]
    
    if hojas_con_datos:
        hoja_seleccionada = st.selectbox("Seleccionar hoja:", hojas_con_datos)
        
        if hoja_seleccionada:
            df = st.session_state.info_archivo["dataframes"][hoja_seleccionada]
            
            # Información de la hoja
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Filas", len(df))
            with col2:
                st.metric("Columnas", len(df.columns))
            
            # Mostrar datos
            st.subheader(f"Datos de la hoja '{hoja_seleccionada}'")
            
            # Opciones de visualización
            mostrar_filas = st.slider("Número de filas a mostrar:", 5, min(100, len(df)), 10)
            
            st.dataframe(df.head(mostrar_filas), use_container_width=True)
            
            # Información de tipos de datos
            with st.expander("📊 Información de Columnas"):
                info_columnas = pd.DataFrame({
                    'Columna': df.columns,
                    'Tipo': df.dtypes.astype(str),
                    'Valores Nulos': df.isnull().sum(),
                    'Porcentaje Nulos': (df.isnull().sum() / len(df) * 100).round(2)
                })
                st.dataframe(info_columnas, use_container_width=True)

def mostrar_analisis_calidad():
    """Muestra el análisis de calidad de datos"""
    if not st.session_state.archivo_cargado or not st.session_state.resultado_analisis:
        return
    
    st.header("🔍 Análisis de Calidad de Datos")
    
    resultado = st.session_state.resultado_analisis
    resumen = resultado["resumen_general"]
    
    # Puntuación general
    puntuacion = resultado["puntuacion_calidad"]
    
    st.metric(
        "Puntuación de Calidad General",
        f"{puntuacion:.1f}/100",
        delta=f"{puntuacion - 70:.1f}" if puntuacion != 70 else None
    )
    
    # Resumen de problemas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Problemas Críticos",
            resumen["problemas_por_severidad"]["alta"],
            delta=-resumen["problemas_por_severidad"]["alta"] if resumen["problemas_por_severidad"]["alta"] > 0 else None
        )
    
    with col2:
        st.metric(
            "Problemas Medios",
            resumen["problemas_por_severidad"]["media"]
        )
    
    with col3:
        st.metric(
            "Problemas Menores",
            resumen["problemas_por_severidad"]["baja"]
        )
    
    # Gráficos de análisis
    if "graficos" in resultado:
        st.subheader("📈 Visualizaciones del Análisis")
        
        # Organizar gráficos en tabs - AGREGAR TAB PARA VELOCÍMETROS
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚨 Problemas por Hoja", 
            "🔍 Valores Nulos", 
            "📊 Calidad General", 
            "📈 Tipos de Datos",
            "⚡ Indicadores de Calidad"  # NUEVO TAB
        ])
        
        with tab1:
            if "problemas_por_hoja" in resultado["graficos"]:
                st.plotly_chart(resultado["graficos"]["problemas_por_hoja"], use_container_width=True)
        
        with tab2:
            if "valores_nulos" in resultado["graficos"]:
                st.plotly_chart(resultado["graficos"]["valores_nulos"], use_container_width=True)
        
        with tab3:
            if "calidad_general" in resultado["graficos"]:
                st.plotly_chart(resultado["graficos"]["calidad_general"], use_container_width=True)
        
        with tab4:
            if "tipos_datos" in resultado["graficos"]:
                st.plotly_chart(resultado["graficos"]["tipos_datos"], use_container_width=True)
        
        # NUEVO TAB PARA VELOCÍMETROS
    with tab5:
        if "velocimetros_calidad" in resultado["graficos"]:
            # Mostrar el gráfico limpio sin texto superpuesto
            st.plotly_chart(resultado["graficos"]["velocimetros_calidad"], use_container_width=True)
            
            # Calcular estado general FUERA del gráfico
            if "metricas_calidad_detalladas" in resultado:
                metricas = resultado["metricas_calidad_detalladas"]
                
                # Calcular porcentajes de no cumplimiento
                no_cumplimiento = {
                    "Completitud": 100 - metricas["completitud"],
                    "Exactitud": 100 - metricas["exactitud"], 
                    "Unicidad": 100 - metricas["unicidad"],
                    "Consistencia": 100 - metricas["consistencia"]
                }
                
                promedio_no_cumplimiento = sum(no_cumplimiento.values()) / 4
                
                if promedio_no_cumplimiento <= 15:
                    estado_general = "EXCELENTE"
                    color_general = "success"
                elif promedio_no_cumplimiento <= 30:
                    estado_general = "BUENO"
                    color_general = "success" 
                elif promedio_no_cumplimiento <= 50:
                    estado_general = "REGULAR"
                    color_general = "warning"
                else:
                    estado_general = "CRÍTICO"
                    color_general = "error"
                
                # Mostrar estado general como alert
                st.info(f"**🎯 CALIDAD GENERAL: {estado_general}** (Promedio: {promedio_no_cumplimiento:.1f}% problemas)")
            
            # Información de interpretación en columnas limpias
            st.subheader("📖 Guía de Interpretación")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **📊 Escala de Calidad:**
                - 🟢 **0-15%**: EXCELENTE - Calidad óptima
                - 🟡 **16-30%**: BUENO - Calidad aceptable  
                - 🟠 **31-50%**: REGULAR - Requiere atención
                - 🔴 **51-100%**: CRÍTICO - Acción inmediata
                """)
            
            with col2:
                st.markdown("""
                **🔍 Definición de Criterios:**
                - **Completitud**: % de datos faltantes o vacíos
                - **Exactitud**: % de datos incorrectos o inválidos
                - **Unicidad**: % de registros duplicados
                - **Consistencia**: % de formatos inconsistentes
                """)
            
            # Mostrar métricas numéricas específicas
            st.subheader("📊 Métricas Detalladas")
            if "metricas_calidad_detalladas" in resultado:
                metricas = resultado["metricas_calidad_detalladas"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    completitud = metricas["completitud"]
                    no_completitud = 100 - completitud
                    color_completitud = "🟢" if no_completitud <= 15 else "🟡" if no_completitud <= 30 else "🟠" if no_completitud <= 50 else "🔴"
                    st.metric(
                        f"{color_completitud} Completitud",
                        f"{completitud:.1f}%",
                        f"-{no_completitud:.1f}% problemas"
                    )
                
                with col2:
                    exactitud = metricas["exactitud"]
                    no_exactitud = 100 - exactitud
                    color_exactitud = "🟢" if no_exactitud <= 15 else "🟡" if no_exactitud <= 30 else "🟠" if no_exactitud <= 50 else "🔴"
                    st.metric(
                        f"{color_exactitud} Exactitud",
                        f"{exactitud:.1f}%",
                        f"-{no_exactitud:.1f}% problemas"
                    )
                
                with col3:
                    unicidad = metricas["unicidad"]
                    no_unicidad = 100 - unicidad
                    color_unicidad = "🟢" if no_unicidad <= 15 else "🟡" if no_unicidad <= 30 else "🟠" if no_unicidad <= 50 else "🔴"
                    st.metric(
                        f"{color_unicidad} Unicidad",
                        f"{unicidad:.1f}%",
                        f"-{no_unicidad:.1f}% problemas"
                    )
                
                with col4:
                    consistencia = metricas["consistencia"]
                    no_consistencia = 100 - consistencia
                    color_consistencia = "🟢" if no_consistencia <= 15 else "🟡" if no_consistencia <= 30 else "🟠" if no_consistencia <= 50 else "🔴"
                    st.metric(
                        f"{color_consistencia} Consistencia",
                        f"{consistencia:.1f}%",
                        f"-{no_consistencia:.1f}% problemas"
                    )
                    
            # Expandir con información adicional (OPCIONAL)
            with st.expander("ℹ️ Información Detallada sobre los Criterios de Calidad"):
                st.markdown("""
                ### 🎯 Completitud (Datos Faltantes)
                Evalúa qué porcentaje de los datos están ausentes o son nulos. Un valor bajo indica que la mayoría de campos tienen información.
                
                ### 🔍 Exactitud (Errores de Datos)  
                Mide la corrección y validez de los datos detectando:
                - Tipos de datos inconsistentes
                - Valores que no corresponden al formato esperado
                - Datos anómalos o fuera de rango
                
                ### 🔄 Unicidad (Datos Duplicados)
                Identifica qué porcentaje de registros están duplicados completamente, lo que puede indicar problemas en la recolección de datos.
                
                ### 📏 Consistencia (Inconsistencias de Formato)
                Evalúa la uniformidad en la estructura y formato de los datos:
                - Inconsistencias en mayúsculas/minúsculas
                - Espacios en blanco innecesarios
                - Formatos mixtos en el mismo campo
                """)
        else:
            st.error("No se pudieron generar los indicadores de calidad")
    
    # Problemas detallados por hoja
    st.subheader("🚨 Problemas Detectados")
    
    analisis_hojas = resultado["analisis_por_hoja"]
    
    for nombre_hoja, analisis in analisis_hojas.items():
        if analisis.get("problemas"):
            with st.expander(f"Hoja: {nombre_hoja} ({len(analisis['problemas'])} problemas)"):
                for i, problema in enumerate(analisis["problemas"]):
                    severidad = problema["severidad"]
                    clase_css = f"problem-{severidad}"
                    
                    emoji = "🔴" if severidad == "alta" else "🟡" if severidad == "media" else "🟢"
                    
                    st.markdown(f"""
                    <div class="{clase_css}">
                        {emoji} <strong>{problema["descripcion"]}</strong><br>
                        <small>Severidad: {severidad.capitalize()}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón para explicación detallada con key único
                    if st.button(f"💡 Explicar", key=f"explain_{nombre_hoja}_{i}"):
                        with st.spinner("Generando explicación..."):
                            explicacion = st.session_state.agente.explicar_problema_especifico(
                                problema, 
                                f"Hoja: {nombre_hoja}"
                            )
                            
                            if explicacion["exito"]:
                                st.info(explicacion["explicacion"])
                            else:
                                crear_mensaje_error(f"Error generando explicación: {explicacion['error']}")

def mostrar_reporte_ia():
    """Muestra el reporte generado por IA"""
    if not st.session_state.archivo_cargado or not st.session_state.resultado_analisis:
        return
    
    st.header("🤖 Reporte Inteligente")
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Generar Reporte Completo", type="primary"):
            with st.spinner("Generando reporte con IA..."):
                reporte = st.session_state.agente.generar_reporte_calidad(
                    st.session_state.info_archivo,
                    st.session_state.resultado_analisis
                )
                
                if reporte["exito"]:
                    st.session_state.reporte_completo = reporte["reporte"]
                    crear_mensaje_exito(f"Reporte generado y guardado como: {reporte['nombre_archivo']}")
                else:
                    crear_mensaje_error(f"Error generando reporte: {reporte['error']}")
    
    with col2:
        if st.button("🛠️ Sugerencias de Limpieza"):
            with st.spinner("Generando sugerencias..."):
                sugerencias = st.session_state.agente.generar_sugerencias_limpieza(
                    st.session_state.info_archivo,
                    st.session_state.resultado_analisis
                )
                
                if sugerencias["exito"]:
                    st.session_state.sugerencias_limpieza = sugerencias["sugerencias"]
                    crear_mensaje_exito("Sugerencias generadas")
                else:
                    crear_mensaje_error(f"Error generando sugerencias: {sugerencias['error']}")
    
    with col3:
        if st.button("📊 Interpretar Gráficos"):
            with st.spinner("Interpretando visualizaciones..."):
                interpretacion = st.session_state.agente.interpretar_graficos(
                    st.session_state.resultado_analisis
                )
                
                if interpretacion["exito"]:
                    st.session_state.interpretacion_graficos = interpretacion["interpretacion"]
                    crear_mensaje_exito("Interpretación generada")
                else:
                    crear_mensaje_error(f"Error interpretando gráficos: {interpretacion['error']}")
    
    # Mostrar resultados
    if hasattr(st.session_state, 'reporte_completo'):
        st.subheader("📄 Reporte Completo")
        st.markdown(st.session_state.reporte_completo)
    
    if hasattr(st.session_state, 'sugerencias_limpieza'):
        st.subheader("🛠️ Sugerencias de Limpieza")
        st.markdown(st.session_state.sugerencias_limpieza)
    
    if hasattr(st.session_state, 'interpretacion_graficos'):
        st.subheader("📊 Interpretación de Gráficos")
        st.markdown(st.session_state.interpretacion_graficos)

def mostrar_chat_interactivo():
    """Muestra interfaz de chat interactivo"""
    st.header("💬 Chat Interactivo")
    
    # Mostrar historial de chat
    for mensaje in st.session_state.historial_chat:
        if mensaje["tipo"] == "usuario":
            st.chat_message("user").write(mensaje["contenido"])
        else:
            st.chat_message("assistant").write(mensaje["contenido"])
    
    # Input para nueva pregunta
    pregunta = st.chat_input("Pregunta sobre tu archivo Excel...")
    
    if pregunta:
        # Agregar pregunta al historial
        st.session_state.historial_chat.append({
            "tipo": "usuario",
            "contenido": pregunta
        })
        
        # Mostrar pregunta
        st.chat_message("user").write(pregunta)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                respuesta = st.session_state.agente.chat_interactivo(
                    pregunta,
                    st.session_state.info_archivo if st.session_state.archivo_cargado else None
                )
                
                if respuesta["exito"]:
                    st.write(respuesta["respuesta"])
                    
                    # Agregar respuesta al historial
                    st.session_state.historial_chat.append({
                        "tipo": "asistente",
                        "contenido": respuesta["respuesta"]
                    })
                else:
                    error_msg = f"Error: {respuesta['error']}"
                    st.error(error_msg)
                    
                    st.session_state.historial_chat.append({
                        "tipo": "asistente",
                        "contenido": error_msg
                    })

def main():
    """Función principal de la aplicación"""
    # Inicializar sesión
    inicializar_sesion()
    
    # Mostrar header
    mostrar_header()
    
    # Mostrar sidebar
    mostrar_sidebar()
    
    # Verificar conexión con Ollama
    estado_ollama = st.session_state.agente.verificar_conexion_ollama()
    if not estado_ollama["conectado"]:
        st.error("⚠️ **Ollama no está conectado**")
        st.info("Para usar el Agente Excel IA necesitas:")
        st.code("1. ollama serve")
        st.code("2. ollama pull llama3.1")
        st.stop()
    
    if not estado_ollama["modelo_disponible"]:
        st.warning("⚠️ **Modelo de IA no disponible**")
        st.info(f"Descarga el modelo con: `ollama pull {st.session_state.agente.configuracion.MODELO_IA}`")
    
    # Crear tabs principales
    if st.session_state.archivo_cargado:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📤 Cargar Archivo", 
            "👀 Vista Previa", 
            "🔍 Análisis de Calidad", 
            "🤖 Reporte IA", 
            "💬 Chat"
        ])
    else:
        tab1 = st.tabs(["📤 Cargar Archivo"])[0]
    
    # Tab 1: Cargar archivo
    with tab1:
        cargar_archivo()
    
    # Tabs adicionales solo si hay archivo cargado
    if st.session_state.archivo_cargado:
        with tab2:
            mostrar_vista_previa()
        
        with tab3:
            mostrar_analisis_calidad()
        
        with tab4:
            mostrar_reporte_ia()
        
        with tab5:
            mostrar_chat_interactivo()

if __name__ == "__main__":
    main()