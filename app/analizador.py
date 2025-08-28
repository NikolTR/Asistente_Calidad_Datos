"""
Analizador de calidad de datos para archivos Excel
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Tuple
import streamlit as st

class AnalizadorCalidadDatos:
    """Clase principal para analizar la calidad de datos en Excel"""
    
    def __init__(self):
        self.problemas_detectados = []
        self.metricas_calidad = {}
        self.recomendaciones = []
    
    def analizar_archivo_completo(self, info_archivo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza la calidad de datos de todo el archivo Excel
        
        Args:
            info_archivo: Información del archivo cargado
        
        Returns:
            Dict con análisis completo
        """
        if not info_archivo.get("exito"):
            return {"error": "Archivo no válido para análisis"}
        
        resultado_analisis = {
            "resumen_general": {},
            "analisis_por_hoja": {},
            "problemas_globales": [],
            "puntuacion_calidad": 0,
            "metricas_calidad_detalladas": {},
            "graficos": {}
        }
        
        try:
            dataframes = info_archivo["dataframes"]
            hojas = info_archivo["hojas"]
            
            # Analizar cada hoja
            for info_hoja in hojas:
                nombre_hoja = info_hoja["nombre"]
                
                if nombre_hoja in dataframes and info_hoja.get("tiene_datos", False):
                    df = dataframes[nombre_hoja]
                    analisis_hoja = self._analizar_hoja_individual(df, nombre_hoja)
                    resultado_analisis["analisis_por_hoja"][nombre_hoja] = analisis_hoja
            
            # Generar resumen general
            resultado_analisis["resumen_general"] = self._generar_resumen_general(resultado_analisis["analisis_por_hoja"])
            
            # Calcular métricas de calidad específicas
            resultado_analisis["metricas_calidad_detalladas"] = self._calcular_metricas_calidad_detalladas(resultado_analisis["analisis_por_hoja"])
            
            # Calcular puntuación de calidad
            resultado_analisis["puntuacion_calidad"] = self._calcular_puntuacion_calidad(resultado_analisis)
            
            # Generar gráficos (incluyendo velocímetros)
            resultado_analisis["graficos"] = self._generar_graficos_analisis(info_archivo, resultado_analisis)
            
        except Exception as e:
            resultado_analisis["error"] = f"Error en análisis: {str(e)}"
            # Asegurar que siempre haya métricas por defecto
            resultado_analisis["metricas_calidad_detalladas"] = {
                "completitud": 50.0,
                "exactitud": 50.0,
                "unicidad": 50.0,
                "consistencia": 50.0
            }
        
        return resultado_analisis
    
    def _analizar_hoja_individual(self, df: pd.DataFrame, nombre_hoja: str) -> Dict[str, Any]:
        """Analiza una hoja individual del Excel"""
        analisis = {
            "nombre": nombre_hoja,
            "dimensiones": {"filas": len(df), "columnas": len(df.columns)},
            "tipos_datos": {},
            "valores_nulos": {},
            "duplicados": 0,
            "problemas": [],
            "metricas": {},
            "metricas_calidad": {}
        }
        
        try:
            # Análisis de tipos de datos
            analisis["tipos_datos"] = df.dtypes.value_counts().to_dict()
            
            # Valores nulos
            nulos_por_columna = df.isnull().sum()
            analisis["valores_nulos"] = {
                "total": int(nulos_por_columna.sum()),
                "porcentaje_total": float(nulos_por_columna.sum() / (len(df) * len(df.columns)) * 100) if len(df) > 0 and len(df.columns) > 0 else 0,
                "por_columna": nulos_por_columna.to_dict()
            }
            
            # Duplicados
            analisis["duplicados"] = int(df.duplicated().sum())
            
            # Calcular métricas de calidad específicas para esta hoja
            analisis["metricas_calidad"] = self._calcular_metricas_calidad_hoja(df)
            
            # Detectar problemas específicos
            analisis["problemas"] = self._detectar_problemas_hoja(df, nombre_hoja)
            
            # Métricas adicionales
            analisis["metricas"] = self._calcular_metricas_hoja(df)
            
        except Exception as e:
            analisis["error"] = f"Error al analizar hoja {nombre_hoja}: {str(e)}"
            # Valores por defecto en caso de error
            analisis["metricas_calidad"] = {
                "completitud": 50.0,
                "exactitud": 50.0,
                "unicidad": 50.0,
                "consistencia": 50.0
            }
        
        return analisis
    
    def _calcular_metricas_calidad_hoja(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula métricas específicas de calidad para una hoja
        """
        metricas = {
            "completitud": 50.0,
            "exactitud": 50.0,
            "unicidad": 50.0,
            "consistencia": 50.0
        }
        
        if len(df) == 0 or len(df.columns) == 0:
            return metricas
        
        try:
            # 1. COMPLETITUD - Porcentaje de datos no nulos
            total_celdas = len(df) * len(df.columns)
            celdas_con_datos = total_celdas - df.isnull().sum().sum()
            metricas["completitud"] = (celdas_con_datos / total_celdas) * 100 if total_celdas > 0 else 100
            
            # 2. EXACTITUD - Basado en tipos de datos y valores válidos
            exactitud_scores = []
            for col in df.columns:
                col_score = 100.0
                
                if df[col].dtype == 'object':
                    valores_no_nulos = df[col].dropna().astype(str)
                    if len(valores_no_nulos) > 0:
                        try:
                            numericos = pd.to_numeric(valores_no_nulos, errors='coerce')
                            porcentaje_numericos = numericos.notna().sum() / len(valores_no_nulos)
                            if 0.3 < porcentaje_numericos < 0.9:
                                col_score -= 30
                        except:
                            pass
                        
                        longitudes = valores_no_nulos.str.len()
                        if longitudes.max() > 1000:
                            col_score -= 20
                
                elif df[col].dtype in ['int64', 'float64']:
                    valores_numericos = df[col].dropna()
                    if len(valores_numericos) > 3:
                        Q1 = valores_numericos.quantile(0.25)
                        Q3 = valores_numericos.quantile(0.75)
                        IQR = Q3 - Q1
                        if IQR > 0:
                            outliers = valores_numericos[(valores_numericos < Q1 - 3*IQR) | (valores_numericos > Q3 + 3*IQR)]
                            if len(outliers) > len(valores_numericos) * 0.1:
                                col_score -= 25
                
                exactitud_scores.append(max(0, col_score))
            
            metricas["exactitud"] = np.mean(exactitud_scores) if exactitud_scores else 50
            
            # 3. UNICIDAD - Porcentaje de registros únicos
            if len(df) > 0:
                filas_unicas = len(df.drop_duplicates())
                metricas["unicidad"] = (filas_unicas / len(df)) * 100
            else:
                metricas["unicidad"] = 100
            
            # 4. CONSISTENCIA - Uniformidad en tipos y formatos
            consistencia_scores = []
            
            for col in df.columns:
                col_score = 100.0
                valores_no_nulos = df[col].dropna()
                
                if len(valores_no_nulos) == 0:
                    continue
                
                if df[col].dtype == 'object':
                    valores_str = valores_no_nulos.astype(str)
                    
                    if len(valores_str) > 1:
                        mayusculas = valores_str.str.isupper().sum()
                        minusculas = valores_str.str.islower().sum()
                        if mayusculas > 0 and minusculas > 0:
                            inconsistencia = min(mayusculas, minusculas) / len(valores_str)
                            if inconsistencia > 0.1:
                                col_score -= 20
                        
                        con_espacios_inicio = valores_str.str.startswith(' ').sum()
                        con_espacios_final = valores_str.str.endswith(' ').sum()
                        if con_espacios_inicio > 0 or con_espacios_final > 0:
                            col_score -= 15
                
                consistencia_scores.append(max(0, col_score))
            
            metricas["consistencia"] = np.mean(consistencia_scores) if consistencia_scores else 50
            
        except Exception as e:
            # En caso de error, devolver valores neutros
            metricas = {
                "completitud": 50.0,
                "exactitud": 50.0,
                "unicidad": 50.0,
                "consistencia": 50.0
            }
        
        return metricas
    
    def _calcular_metricas_calidad_detalladas(self, analisis_hojas: Dict[str, Any]) -> Dict[str, float]:
        """Calcula métricas de calidad agregadas de todas las hojas"""
        metricas_consolidadas = {
            "completitud": 50.0,
            "exactitud": 50.0,
            "unicidad": 50.0,
            "consistencia": 50.0
        }
        
        try:
            metricas_por_hoja = []
            
            for nombre_hoja, analisis in analisis_hojas.items():
                if "metricas_calidad" in analisis and "error" not in analisis:
                    metricas_por_hoja.append(analisis["metricas_calidad"])
            
            if metricas_por_hoja:
                for criterio in ["completitud", "exactitud", "unicidad", "consistencia"]:
                    valores = [m.get(criterio, 50.0) for m in metricas_por_hoja]
                    metricas_consolidadas[criterio] = np.mean(valores) if valores else 50.0
        
        except Exception as e:
            pass  # Mantener valores por defecto
        
        return metricas_consolidadas
    
    def _detectar_problemas_hoja(self, df: pd.DataFrame, nombre_hoja: str) -> List[Dict[str, Any]]:
        """Detecta problemas específicos en una hoja"""
        problemas = []
        
        try:
            # Problema 1: Muchos valores nulos
            for columna in df.columns:
                if len(df) > 0:
                    porcentaje_nulos = (df[columna].isnull().sum() / len(df)) * 100
                    if porcentaje_nulos > 50:
                        problemas.append({
                            "tipo": "valores_nulos_excesivos",
                            "descripcion": f"Columna '{columna}' tiene {porcentaje_nulos:.1f}% valores nulos",
                            "severidad": "alta",
                            "columna": columna,
                            "valor": porcentaje_nulos
                        })
            
            # Problema 2: Filas completamente vacías
            if len(df) > 0:
                filas_vacias = df.isnull().all(axis=1).sum()
                if filas_vacias > 0:
                    problemas.append({
                        "tipo": "filas_vacias",
                        "descripcion": f"{filas_vacias} filas completamente vacías",
                        "severidad": "media",
                        "valor": filas_vacias
                    })
            
            # Problema 3: Duplicados excesivos
            if len(df) > 0:
                porcentaje_duplicados = (df.duplicated().sum() / len(df)) * 100
                if porcentaje_duplicados > 10:
                    problemas.append({
                        "tipo": "duplicados_excesivos",
                        "descripcion": f"{porcentaje_duplicados:.1f}% de filas duplicadas",
                        "severidad": "alta",
                        "valor": porcentaje_duplicados
                    })
            
            # Problema 4: Nombres de columnas problemáticos
            for columna in df.columns:
                if pd.isna(columna) or str(columna).startswith("Unnamed"):
                    problemas.append({
                        "tipo": "nombres_columnas_invalidos",
                        "descripcion": f"Columna sin nombre válido: '{columna}'",
                        "severidad": "media",
                        "columna": columna
                    })
        
        except Exception as e:
            pass  # En caso de error, devolver lista vacía
        
        return problemas
    
    def _calcular_metricas_hoja(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas adicionales para la hoja"""
        metricas = {
            "densidad_datos": 0,
            "diversidad_tipos": 0,
            "columnas_numericas": 0,
            "columnas_texto": 0,
            "uniformidad_promedio": 0
        }
        
        try:
            if len(df) > 0 and len(df.columns) > 0:
                total_celdas = len(df) * len(df.columns)
                celdas_con_datos = total_celdas - df.isnull().sum().sum()
                metricas["densidad_datos"] = (celdas_con_datos / total_celdas) * 100
                
                metricas["diversidad_tipos"] = len(df.dtypes.unique())
                metricas["columnas_numericas"] = df.select_dtypes(include=[np.number]).shape[1]
                metricas["columnas_texto"] = df.select_dtypes(include=['object']).shape[1]
        
        except Exception as e:
            pass  # Mantener valores por defecto
        
        return metricas
    
    def _generar_resumen_general(self, analisis_hojas: Dict[str, Any]) -> Dict[str, Any]:
        """Genera resumen general del análisis"""
        resumen = {
            "total_hojas_analizadas": len(analisis_hojas),
            "total_filas": 0,
            "total_columnas": 0,
            "total_problemas": 0,
            "problemas_por_severidad": {"alta": 0, "media": 0, "baja": 0},
            "calidad_promedio": 50
        }
        
        try:
            for nombre_hoja, analisis in analisis_hojas.items():
                if "error" not in analisis:
                    resumen["total_filas"] += analisis.get("dimensiones", {}).get("filas", 0)
                    resumen["total_columnas"] += analisis.get("dimensiones", {}).get("columnas", 0)
                    resumen["total_problemas"] += len(analisis.get("problemas", []))
                    
                    for problema in analisis.get("problemas", []):
                        severidad = problema.get("severidad", "baja")
                        if severidad in resumen["problemas_por_severidad"]:
                            resumen["problemas_por_severidad"][severidad] += 1
            
            if resumen["total_hojas_analizadas"] > 0:
                problemas_por_hoja = resumen["total_problemas"] / resumen["total_hojas_analizadas"]
                resumen["calidad_promedio"] = max(0, 100 - (problemas_por_hoja * 10))
        
        except Exception as e:
            pass
        
        return resumen
    
    def _calcular_puntuacion_calidad(self, resultado_analisis: Dict[str, Any]) -> float:
        """Calcula puntuación de calidad del 0 al 100"""
        try:
            if "metricas_calidad_detalladas" in resultado_analisis:
                metricas = resultado_analisis["metricas_calidad_detalladas"]
                puntuacion = (metricas["completitud"] + metricas["exactitud"] + 
                            metricas["unicidad"] + metricas["consistencia"]) / 4
                return max(0, min(100, puntuacion))
            
            return 50.0
            
        except:
            return 50.0
    
    def _generar_graficos_analisis(self, info_archivo: Dict[str, Any], resultado_analisis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera gráficos para visualizar el análisis"""
        graficos = {}
        
        try:
            # Gráficos originales
            graficos["problemas_por_hoja"] = self._grafico_problemas_por_hoja(resultado_analisis)
            graficos["valores_nulos"] = self._grafico_valores_nulos(resultado_analisis)
            graficos["calidad_general"] = self._grafico_calidad_general(resultado_analisis)
            graficos["tipos_datos"] = self._grafico_tipos_datos(resultado_analisis)
            
            # Velocímetros de calidad
            graficos["velocimetros_calidad"] = self._grafico_velocimetros_calidad(resultado_analisis)
            
        except Exception as e:
            graficos["error"] = f"Error generando gráficos: {str(e)}"
        
        return graficos
    
    def _grafico_velocimetros_calidad(self, resultado_analisis: Dict[str, Any]) -> go.Figure:
        """
        Genera 4 velocímetros mejorados mostrando el porcentaje de NO CUMPLIMIENTO
        con diseño limpio y sin elementos confusos
        """
        try:
            metricas = resultado_analisis.get("metricas_calidad_detalladas", {
                "completitud": 50.0,
                "exactitud": 50.0,
                "unicidad": 50.0,
                "consistencia": 50.0
            })
            
            # Calcular porcentajes de no cumplimiento
            no_cumplimiento = {
                "Completitud": 100 - metricas["completitud"],
                "Exactitud": 100 - metricas["exactitud"],
                "Unicidad": 100 - metricas["unicidad"],
                "Consistencia": 100 - metricas["consistencia"]
            }
            
            # Crear figura con subplots
            fig = make_subplots(
                rows=2, 
                cols=2,
                specs=[[{"type": "indicator"}, {"type": "indicator"}],
                    [{"type": "indicator"}, {"type": "indicator"}]],
                subplot_titles=("", "", "", ""),
                vertical_spacing=0.25,
                horizontal_spacing=0.1
            )
            
            def get_gauge_color(valor):
                """Retorna color basado en el valor de no cumplimiento"""
                if valor <= 15:
                    return "#27ae60"  # Verde
                elif valor <= 30:
                    return "#f39c12"  # Naranja
                elif valor <= 50:
                    return "#e67e22"  # Naranja oscuro
                else:
                    return "#e74c3c"  # Rojo
            
            def get_status_text(valor):
                """Retorna texto de estado basado en el valor"""
                if valor <= 15:
                    return "EXCELENTE"
                elif valor <= 30:
                    return "BUENO"
                elif valor <= 50:
                    return "REGULAR"
                else:
                    return "CRÍTICO"
            
            # Configuraciones para cada criterio
            criterios_config = {
                "Completitud": {
                    "descripcion": "Datos Faltantes",
                    "icon": "📊",
                    "pos": (1, 1)
                },
                "Exactitud": {
                    "descripcion": "Errores de Datos", 
                    "icon": "🎯",
                    "pos": (1, 2)
                },
                "Unicidad": {
                    "descripcion": "Datos Duplicados",
                    "icon": "🔄",
                    "pos": (2, 1)
                },
                "Consistencia": {
                    "descripcion": "Inconsistencias",
                    "icon": "📏",
                    "pos": (2, 2)
                }
            }
            
            # Crear cada velocímetro
            for criterio, config in criterios_config.items():
                valor = no_cumplimiento[criterio]
                color = get_gauge_color(valor)
                status = get_status_text(valor)
                pos = config["pos"]
                
                fig.add_trace(
                    go.Indicator(
                        mode="gauge+number",
                        value=valor,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={
                            'text': f"<b>{config['icon']} {criterio}</b><br>" +
                                f"<span style='font-size:12px; color:#555'>{config['descripcion']}</span><br>" +
                                f"<span style='font-size:11px; color:{color}'><b>{status}</b></span>",
                            'font': {'size': 14}
                        },
                        number={
                            'suffix': "%",
                            'font': {'size': 20, 'color': color, 'family': 'Arial Black'}
                        },
                        gauge={
                            'axis': {
                                'range': [None, 100],
                                'tickwidth': 1,
                                'tickcolor': "#2c3e50",
                                'tickfont': {'size': 10}
                            },
                            'bar': {
                                'color': color,
                                'thickness': 0.3
                            },
                            'bgcolor': "#f8f9fa",
                            'borderwidth': 2,
                            'bordercolor': "#34495e",
                            'steps': [
                                {'range': [0, 15], 'color': '#d5f4e6'},    # Verde claro
                                {'range': [15, 30], 'color': '#fef9e7'},   # Amarillo claro
                                {'range': [30, 50], 'color': '#fdf2e9'},   # Naranja claro
                                {'range': [50, 100], 'color': '#fadbd8'}   # Rojo claro
                            ],
                            # FLECHA ROJA que apunta al valor exacto del porcentaje
                            'threshold': {
                                'line': {'color': "#e74c3c", 'width': 4},
                                'thickness': 0.75,
                                'value': valor  # Apunta al valor exacto del porcentaje de problemas
                            }
                        }
                    ),
                    row=pos[0],
                    col=pos[1]
                )
            
            # Configurar layout principal SIN anotaciones superpuestas
            fig.update_layout(
                title={
                    'text': "<b>INDICADORES DE CALIDAD DE DATOS</b><br>" +
                        "<span style='font-size:14px; color:#666'>Porcentaje de Problemas Detectados</span>",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 18, 'color': '#2c3e50'}
                },
                height=500,
                font=dict(family="Arial, sans-serif", size=11),
                paper_bgcolor="#ffffff",
                plot_bgcolor="#ffffff",
                margin=dict(l=30, r=30, t=80, b=30),
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            # Crear figura de error más limpia
            fig = go.Figure()
            fig.add_annotation(
                text=f"<b>Error generando velocímetros</b><br>" +
                    f"<span style='color:#e74c3c'>Detalles: {str(e)}</span>",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="#2c3e50"),
                bgcolor="rgba(231,76,60,0.1)",
                bordercolor="#e74c3c",
                borderwidth=1,
                borderpad=15
            )
            fig.update_layout(
                height=400,
                title="Error en Indicadores de Calidad"
            )
            return fig
    
    def _grafico_problemas_por_hoja(self, resultado_analisis: Dict[str, Any]) -> go.Figure:
        """Gráfico de barras con problemas por hoja"""
        try:
            analisis_hojas = resultado_analisis.get("analisis_por_hoja", {})
            
            if not analisis_hojas:
                fig = go.Figure()
                fig.add_annotation(text="No hay hojas para analizar")
                return fig
            
            hojas = []
            problemas_altos = []
            problemas_medios = []
            problemas_bajos = []
            
            for nombre, analisis in analisis_hojas.items():
                hojas.append(nombre)
                
                conteo_severidad = {"alta": 0, "media": 0, "baja": 0}
                for problema in analisis.get("problemas", []):
                    severidad = problema.get("severidad", "baja")
                    if severidad in conteo_severidad:
                        conteo_severidad[severidad] += 1
                
                problemas_altos.append(conteo_severidad["alta"])
                problemas_medios.append(conteo_severidad["media"])
                problemas_bajos.append(conteo_severidad["baja"])
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Severidad Alta',
                x=hojas,
                y=problemas_altos,
                marker_color='#ff4444'
            ))
            
            fig.add_trace(go.Bar(
                name='Severidad Media',
                x=hojas,
                y=problemas_medios,
                marker_color='#ffaa44'
            ))
            
            fig.add_trace(go.Bar(
                name='Severidad Baja',
                x=hojas,
                y=problemas_bajos,
                marker_color='#44aaff'
            ))
            
            fig.update_layout(
                title='Problemas Detectados por Hoja',
                xaxis_title='Hojas',
                yaxis_title='Número de Problemas',
                barmode='stack',
                height=400
            )
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}")
            return fig
    
    def _grafico_valores_nulos(self, resultado_analisis: Dict[str, Any]) -> go.Figure:
        """Gráfico de valores nulos por hoja"""
        try:
            analisis_hojas = resultado_analisis.get("analisis_por_hoja", {})
            
            hojas = []
            porcentajes_nulos = []
            
            for nombre, analisis in analisis_hojas.items():
                if "valores_nulos" in analisis:
                    hojas.append(nombre)
                    porcentajes_nulos.append(analisis["valores_nulos"]["porcentaje_total"])
            
            if not hojas:
                fig = go.Figure()
                fig.add_annotation(text="No hay datos de valores nulos")
                return fig
            
            fig = px.bar(
                x=hojas,
                y=porcentajes_nulos,
                title='Porcentaje de Valores Nulos por Hoja',
                labels={'x': 'Hojas', 'y': 'Porcentaje de Nulos (%)'},
                color=porcentajes_nulos,
                color_continuous_scale='Reds'
            )
            
            fig.update_layout(height=400)
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}")
            return fig
    
    def _grafico_calidad_general(self, resultado_analisis: Dict[str, Any]) -> go.Figure:
        """Medidor de calidad general"""
        try:
            puntuacion = resultado_analisis.get("puntuacion_calidad", 50)
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = puntuacion,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Puntuación de Calidad"},
                delta = {'reference': 80},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=400)
            
            return fig
            
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}")
            return fig
    
    def _grafico_tipos_datos(self, resultado_analisis: Dict[str, Any]) -> go.Figure:
        """Gráfico de distribución de tipos de datos mejorado"""
        try:
            analisis_hojas = resultado_analisis.get("analisis_por_hoja", {})
            
            tipos_consolidados = {}
            
            for analisis in analisis_hojas.values():
                if "tipos_datos" in analisis:
                    for tipo, cantidad in analisis["tipos_datos"].items():
                        tipo_str = str(tipo)
                        tipos_consolidados[tipo_str] = tipos_consolidados.get(tipo_str, 0) + cantidad
            
            if not tipos_consolidados:
                fig = go.Figure()
                fig.add_annotation(
                    text="❌ <b>No hay datos de tipos disponibles</b><br>" +
                        "<span style='color:#666'>Verifica que el archivo tenga datos válidos</span>",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="#2c3e50"),
                    bgcolor="rgba(231,76,60,0.1)",
                    bordercolor="#e74c3c",
                    borderwidth=2,
                    borderpad=20
                )
                fig.update_layout(
                    height=400,
                    title="Error en Distribución de Tipos de Datos"
                )
                return fig
            
            # Mapeo de tipos técnicos a nombres en español más comprensibles
            mapeo_tipos = {
                'object': 'Texto',
                'int64': 'Números Enteros',
                'float64': 'Números Decimales',
                'bool': 'Valores Lógicos',
                'datetime64[ns]': 'Tiempo',
                'timedelta64[ns]': 'Intervalos de Tiempo',
                'category': 'Categorías',
                'string': 'Cadenas de Texto',
                'Int64': 'Enteros (Nullable)',
                'Float64': 'Decimales (Nullable)',
                'boolean': 'Booleanos (Nullable)',
                'complex128': 'Números Complejos',
                'period': 'Períodos',
            }
            
            # Convertir tipos técnicos a nombres en español
            tipos_español = {}
            total_columnas = sum(tipos_consolidados.values())
            
            for tipo_tecnico, cantidad in tipos_consolidados.items():
                nombre_español = mapeo_tipos.get(tipo_tecnico, f'Otros ({tipo_tecnico})')
                tipos_español[nombre_español] = tipos_español.get(nombre_español, 0) + cantidad
            
            # Ordenar por cantidad (de mayor a menor)
            tipos_ordenados = dict(sorted(tipos_español.items(), key=lambda x: x[1], reverse=True))
            
            # Colores profesionales y distintivos para cada tipo
            colores_personalizados = [
                '#2E86AB',  # Azul profesional para texto
                '#A23B72',  # Rosa/púrpura para números enteros
                '#F18F01',  # Naranja para decimales
                '#C73E1D',  # Rojo para lógicos
                '#5D4E75',  # Púrpura para fechas
                '#708B75',  # Verde grisáceo para intervalos
                '#B85450',  # Rojo ladrillo para categorías
                '#4A7C59',  # Verde oscuro para otros tipos
                '#8D5524',  # Marrón para nullable
                '#2F4858'   # Azul oscuro para complejos
            ]
            
            # Calcular porcentajes
            porcentajes = [(cantidad/total_columnas)*100 for cantidad in tipos_ordenados.values()]
            
            # Crear el gráfico circular simple y limpio
            fig = go.Figure(data=[go.Pie(
                labels=list(tipos_ordenados.keys()),
                values=list(tipos_ordenados.values()),
                marker=dict(
                    colors=colores_personalizados[:len(tipos_ordenados)],
                    line=dict(color='white', width=2)
                ),
                textinfo='label+percent',
                textfont=dict(
                    size=13,
                    family="Arial, sans-serif"
                ),
                hovertemplate='<b>%{label}</b><br>' +
                            'Columnas: %{value}<br>' +
                            'Porcentaje: %{percent}<br>' +
                            '<extra></extra>'
            )])
            
            # Configurar el layout simple y limpio
            fig.update_layout(
                title={
                    'text': 'Distribución de Tipos de Datos',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'color': '#2c3e50'}
                },
                font=dict(size=12, color="#2c3e50"),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=11)
                ),
                height=400,
                margin=dict(l=20, r=120, t=60, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
            
            return fig
                
        except Exception as e:
            # Crear figura de error más informativa
            fig = go.Figure()
            fig.add_annotation(
                text=f"❌ <b>Error generando gráfico de tipos de datos</b><br>" +
                    f"<span style='color:#e74c3c'>Detalles: {str(e)}</span><br>" +
                    "<span style='color:#666'>Verifica la estructura de datos o contacta al administrador</span>",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="#2c3e50"),
                bgcolor="rgba(231,76,60,0.1)",
                bordercolor="#e74c3c",
                borderwidth=2,
                borderpad=20
            )
            fig.update_layout(
                height=400,
                title="Error en Distribución de Tipos de Datos",
                paper_bgcolor='white'
            )
            return fig
    
    def obtener_resumen_problemas(self, resultado_analisis: Dict[str, Any]) -> str:
        """Genera resumen textual de problemas para la IA"""
        try:
            resumen = resultado_analisis.get("resumen_general", {})
            analisis_hojas = resultado_analisis.get("analisis_por_hoja", {})
            metricas_calidad = resultado_analisis.get("metricas_calidad_detalladas", {})
            
            texto_resumen = f"""
RESUMEN DE ANÁLISIS:
- Total de hojas analizadas: {resumen.get('total_hojas_analizadas', 0)}
- Total de problemas encontrados: {resumen.get('total_problemas', 0)}
- Problemas de severidad alta: {resumen.get('problemas_por_severidad', {}).get('alta', 0)}
- Problemas de severidad media: {resumen.get('problemas_por_severidad', {}).get('media', 0)}
- Problemas de severidad baja: {resumen.get('problemas_por_severidad', {}).get('baja', 0)}
- Puntuación de calidad: {resultado_analisis.get('puntuacion_calidad', 0):.1f}/100

MÉTRICAS DE CALIDAD ESPECÍFICAS:
- Completitud: {metricas_calidad.get('completitud', 50):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('completitud', 50):.1f}%)
- Exactitud: {metricas_calidad.get('exactitud', 50):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('exactitud', 50):.1f}%)
- Unicidad: {metricas_calidad.get('unicidad', 50):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('unicidad', 50):.1f}%)
- Consistencia: {metricas_calidad.get('consistencia', 50):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('consistencia', 50):.1f}%)

PROBLEMAS DETALLADOS POR HOJA:
"""
            
            for nombre_hoja, analisis in analisis_hojas.items():
                if "problemas" in analisis and analisis["problemas"]:
                    texto_resumen += f"\nHoja '{nombre_hoja}':\n"
                    for problema in analisis["problemas"]:
                        texto_resumen += f"- {problema.get('descripcion', 'Descripción no disponible')} (Severidad: {problema.get('severidad', 'desconocida')})\n"
            
            return texto_resumen
            
        except Exception as e:
            return f"Error generando resumen de problemas: {str(e)}"