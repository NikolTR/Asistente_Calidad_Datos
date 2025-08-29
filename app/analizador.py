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
import re

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
                "completitud": 30.0,
                "exactitud": 25.0,
                "unicidad": 40.0,
                "consistencia": 35.0
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
                "completitud": 30.0,
                "exactitud": 25.0,
                "unicidad": 40.0,
                "consistencia": 35.0
            }
        
        return analisis
    
    def _calcular_metricas_calidad_hoja(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula métricas específicas de calidad para una hoja con validaciones más estrictas
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
            # 1. COMPLETITUD MEJORADA - Detecta valores nulos, vacíos y placeholders
            total_celdas = len(df) * len(df.columns)
            celdas_problematicas = 0
            
            for col in df.columns:
                for idx, valor in df[col].items():
                    # Contar como problemático si:
                    if pd.isna(valor):  # Nulo
                        celdas_problematicas += 1
                    elif isinstance(valor, str):
                        valor_limpio = str(valor).strip()
                        if (valor_limpio == '' or  # Vacío
                            valor_limpio == '??' or  # Placeholder
                            valor_limpio.lower() in ['n/a', 'na', 'null', 'none'] or  # Valores nulos textuales
                            len(valor_limpio) == 0):  # Solo espacios
                            celdas_problematicas += 1
            
            metricas["completitud"] = max(0, ((total_celdas - celdas_problematicas) / total_celdas) * 100) if total_celdas > 0 else 100
            
            # 2. EXACTITUD MEJORADA - Validaciones específicas por tipo de dato
            exactitud_scores = []
            
            for col in df.columns:
                col_score = 100.0
                valores_no_nulos = df[col].dropna()
                
                if len(valores_no_nulos) == 0:
                    exactitud_scores.append(col_score)
                    continue
                
                # Validaciones específicas según el nombre de la columna
                col_lower = col.lower()
                
                # Validación de fechas
                if 'fecha' in col_lower:
                    for valor in valores_no_nulos:
                        valor_str = str(valor).strip()
                        if valor_str.lower() == 'hoy':  # Fecha inválida
                            col_score -= 20
                        else:
                            try:
                                pd.to_datetime(valor_str, errors='raise')
                            except:
                                col_score -= 15
                
                # Validación de códigos/IDs
                elif any(word in col_lower for word in ['codigo', 'id_']):
                    for valor in valores_no_nulos:
                        valor_str = str(valor).strip()
                        if valor_str == '' or valor_str == '??':
                            col_score -= 25
                
                # Validación de teléfonos/celulares
                elif any(word in col_lower for word in ['telefono', 'celular']):
                    for valor in valores_no_nulos:
                        valor_str = str(valor).strip()
                        if len(valor_str) > 12 or len(valor_str) < 7:  # Longitud anormal
                            col_score -= 20
                        elif not valor_str.isdigit():
                            col_score -= 15
                
                # Validación de género
                elif 'genero' in col_lower:
                    valores_validos = ['masculino', 'femenino', 'otro']
                    for valor in valores_no_nulos:
                        valor_str = str(valor).strip().lower()
                        if valor_str not in valores_validos and valor_str != '??':
                            col_score -= 30
                        elif valor_str == '??':
                            col_score -= 40
                
                # Validación de emails
                elif 'email' in col_lower or 'correo' in col_lower:
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    for valor in valores_no_nulos:
                        valor_str = str(valor).strip()
                        if not re.match(email_pattern, valor_str):
                            col_score -= 25
                
                # Validación de sede/institución
                elif any(word in col_lower for word in ['sede', 'institucion']):
                    for valor in valores_no_nulos:
                        valor_str = str(valor).strip()
                        # Detectar errores tipográficos como "bUD" en lugar de "IUD"
                        if len(valor_str) < 3 or any(c in valor_str for c in ['??', '@@']):
                            col_score -= 30
                
                # Validación general de texto
                if df[col].dtype == 'object':
                    valores_str = valores_no_nulos.astype(str)
                    for valor_str in valores_str:
                        # Detectar caracteres raros o errores tipográficos
                        if any(char in valor_str for char in ['??', '@@', '##']):
                            col_score -= 15
                        
                        # Detectar longitudes anormales
                        if len(valor_str) > 200:  # Muy largo
                            col_score -= 10
                
                exactitud_scores.append(max(0, col_score))
            
            metricas["exactitud"] = np.mean(exactitud_scores) if exactitud_scores else 50
            
            # 3. UNICIDAD MEJORADA - Considera duplicados parciales
            if len(df) > 0:
                # Duplicados completos
                filas_unicas = len(df.drop_duplicates())
                unicidad_completa = (filas_unicas / len(df)) * 100
                
                # Verificar duplicados en campos clave (como documento)
                unicidad_campos_clave = 100.0
                campos_clave = ['documento', 'id_estudiante', 'email']
                
                for campo in campos_clave:
                    col_encontrada = None
                    for col in df.columns:
                        if campo.lower() in col.lower():
                            col_encontrada = col
                            break
                    
                    if col_encontrada and col_encontrada in df.columns:
                        valores_campo = df[col_encontrada].dropna()
                        if len(valores_campo) > 0:
                            valores_unicos = len(valores_campo.drop_duplicates())
                            porcentaje_unicos = (valores_unicos / len(valores_campo)) * 100
                            unicidad_campos_clave = min(unicidad_campos_clave, porcentaje_unicos)
                
                metricas["unicidad"] = min(unicidad_completa, unicidad_campos_clave)
            else:
                metricas["unicidad"] = 100
            
            # 4. CONSISTENCIA MEJORADA - Validaciones de formato y estructura
            consistencia_scores = []
            
            for col in df.columns:
                col_score = 100.0
                valores_no_nulos = df[col].dropna()
                
                if len(valores_no_nulos) == 0:
                    continue
                
                if df[col].dtype == 'object':
                    valores_str = valores_no_nulos.astype(str)
                    
                    # Verificar consistencia en formato de fechas
                    if 'fecha' in col.lower() or 'periodo' in col.lower():
                        formatos_encontrados = set()
                        for valor in valores_str:
                            valor = valor.strip()
                            if '/' in valor:
                                formatos_encontrados.add('dd/mm/yyyy')
                            elif '-' in valor:
                                formatos_encontrados.add('yyyy-mm-dd')
                            elif valor.lower() == 'hoy':
                                formatos_encontrados.add('texto')
                            else:
                                formatos_encontrados.add('otro')
                        
                        if len(formatos_encontrados) > 1:
                            col_score -= 30
                    
                    # Verificar consistencia en códigos
                    elif 'codigo' in col.lower() or col.lower().startswith('id'):
                        longitudes = [len(str(v).strip()) for v in valores_str]
                        if len(set(longitudes)) > 2:  # Más de 2 longitudes diferentes
                            col_score -= 25
                    
                    # Verificar consistencia general de formato
                    if len(valores_str) > 1:
                        # Verificar mayúsculas/minúsculas
                        mayusculas = sum(1 for v in valores_str if str(v).isupper())
                        minusculas = sum(1 for v in valores_str if str(v).islower())
                        if mayusculas > 0 and minusculas > 0:
                            inconsistencia = min(mayusculas, minusculas) / len(valores_str)
                            if inconsistencia > 0.2:  # Más estricto
                                col_score -= 25
                        
                        # Verificar espacios al inicio/final
                        con_espacios = sum(1 for v in valores_str if str(v) != str(v).strip())
                        if con_espacios > len(valores_str) * 0.1:
                            col_score -= 20
                        
                        # Verificar caracteres especiales inconsistentes
                        con_caracteres_especiales = sum(1 for v in valores_str if any(c in str(v) for c in ['@', '#', '$', '%']))
                        if con_caracteres_especiales > 0 and con_caracteres_especiales < len(valores_str):
                            col_score -= 15
                
                consistencia_scores.append(max(0, col_score))
            
            metricas["consistencia"] = np.mean(consistencia_scores) if consistencia_scores else 50
            
            # Aplicar penalizaciones adicionales por problemas graves detectados
            problemas_graves = 0
            
            # Buscar errores tipográficos evidentes en toda la tabla
            for col in df.columns:
                for valor in df[col].dropna():
                    valor_str = str(valor).strip()
                    # Detectar patrones de error comunes
                    if any(patron in valor_str for patron in ['bUD', 'j025', 'x025', 'n025']):
                        problemas_graves += 1
                    elif valor_str == 'hoy' and 'fecha' in col.lower():
                        problemas_graves += 1
                    elif '999999999999999' in valor_str:  # Números excesivamente largos
                        problemas_graves += 1
            
            # Aplicar penalización proporcional
            if problemas_graves > 0:
                factor_penalizacion = min(0.5, problemas_graves / (len(df) * 0.1))  # Máximo 50% de penalización
                for metrica in metricas:
                    metricas[metrica] *= (1 - factor_penalizacion)
        
        except Exception as e:
            # En caso de error, devolver valores que reflejen problemas
            metricas = {
                "completitud": 30.0,
                "exactitud": 25.0,
                "unicidad": 40.0,
                "consistencia": 35.0
            }
        
        # Asegurar que todas las métricas estén en el rango 0-100
        for key in metricas:
            metricas[key] = max(0.0, min(100.0, metricas[key]))
        
        return metricas
    
    def _calcular_metricas_calidad_detalladas(self, analisis_hojas: Dict[str, Any]) -> Dict[str, float]:
        """Calcula métricas de calidad agregadas de todas las hojas"""
        metricas_consolidadas = {
            "completitud": 30.0,
            "exactitud": 25.0,
            "unicidad": 40.0,
            "consistencia": 35.0
        }
        
        try:
            metricas_por_hoja = []
            
            for nombre_hoja, analisis in analisis_hojas.items():
                if "metricas_calidad" in analisis and "error" not in analisis:
                    metricas_por_hoja.append(analisis["metricas_calidad"])
            
            if metricas_por_hoja:
                for criterio in ["completitud", "exactitud", "unicidad", "consistencia"]:
                    valores = [m.get(criterio, 30.0) for m in metricas_por_hoja]
                    metricas_consolidadas[criterio] = np.mean(valores) if valores else 30.0
        
        except Exception as e:
            pass  # Mantener valores por defecto
        
        return metricas_consolidadas
    
    def _detectar_problemas_hoja(self, df: pd.DataFrame, nombre_hoja: str) -> List[Dict[str, Any]]:
        """Detecta problemas específicos en una hoja con validaciones más detalladas"""
        problemas = []
        
        try:
            # 1. Valores nulos y vacíos por columna
            for columna in df.columns:
                if len(df) > 0:
                    # Contar diferentes tipos de problemas
                    nulos_reales = df[columna].isnull().sum()
                    valores_vacios = 0
                    valores_placeholder = 0
                    
                    for valor in df[columna].dropna():
                        valor_str = str(valor).strip()
                        if valor_str == '' or len(valor_str) == 0:
                            valores_vacios += 1
                        elif valor_str in ['??', 'N/A', 'na', 'null']:
                            valores_placeholder += 1
                    
                    total_problemas = nulos_reales + valores_vacios + valores_placeholder
                    if total_problemas > 0:
                        porcentaje_problemas = (total_problemas / len(df)) * 100
                        if porcentaje_problemas > 10:  # Más estricto
                            severidad = "alta" if porcentaje_problemas > 30 else "media"
                            problemas.append({
                                "tipo": "datos_faltantes_o_invalidos",
                                "descripcion": f"Columna '{columna}': {total_problemas} valores problemáticos ({porcentaje_problemas:.1f}%)",
                                "severidad": severidad,
                                "columna": columna,
                                "valor": porcentaje_problemas,
                                "detalles": {
                                    "nulos": nulos_reales,
                                    "vacios": valores_vacios,
                                    "placeholders": valores_placeholder
                                }
                            })
            
            # 2. Errores tipográficos específicos
            errores_tipograficos = []
            patrones_error = {
                'bUD': 'IUD',
                'j025-1': '2025-1',
                'x025-1': '2025-1',
                'n025-1': '2025-1',
                'i025-1': '2025-1',
                'hoy': 'fecha específica',
                'tISNEROS': 'CISNEROS',
                'µ': 'A',
                '¢': 'o',
                '‚': 'e'
            }
            
            for columna in df.columns:
                for idx, valor in df[columna].items():
                    if pd.notna(valor):
                        valor_str = str(valor)
                        for patron, correccion in patrones_error.items():
                            if patron in valor_str:
                                errores_tipograficos.append({
                                    "fila": idx,
                                    "columna": columna,
                                    "valor_actual": valor_str,
                                    "patron_error": patron,
                                    "sugerencia": valor_str.replace(patron, correccion)
                                })
            
            if errores_tipograficos:
                problemas.append({
                    "tipo": "errores_tipograficos",
                    "descripcion": f"{len(errores_tipograficos)} errores tipográficos detectados",
                    "severidad": "alta",
                    "valor": len(errores_tipograficos),
                    "ejemplos": errores_tipograficos[:5]  # Mostrar solo los primeros 5
                })
            
            # 3. Valores de longitud anormal
            for columna in df.columns:
                if 'telefono' in columna.lower() or 'celular' in columna.lower():
                    valores_anormales = []
                    for idx, valor in df[columna].items():
                        if pd.notna(valor):
                            valor_str = str(valor).strip()
                            if len(valor_str) > 12 or len(valor_str) < 7:
                                valores_anormales.append({
                                    "fila": idx,
                                    "valor": valor_str,
                                    "longitud": len(valor_str)
                                })
                    
                    if valores_anormales:
                        problemas.append({
                            "tipo": "longitud_telefono_anormal",
                            "descripcion": f"Columna '{columna}': {len(valores_anormales)} números con longitud anormal",
                            "severidad": "media",
                            "columna": columna,
                            "valor": len(valores_anormales),
                            "ejemplos": valores_anormales[:3]
                        })
            
            # 4. Inconsistencias en códigos obligatorios
            campos_obligatorios = ['codigo programa', 'codigo_programa', 'id_estudiante']
            for campo_obligatorio in campos_obligatorios:
                columna_encontrada = None
                for col in df.columns:
                    if campo_obligatorio.lower().replace('_', ' ') in col.lower().replace('_', ' '):
                        columna_encontrada = col
                        break
                
                if columna_encontrada:
                    valores_faltantes = 0
                    for valor in df[columna_encontrada]:
                        if pd.isna(valor) or str(valor).strip() == '':
                            valores_faltantes += 1
                    
                    if valores_faltantes > 0:
                        problemas.append({
                            "tipo": "campo_obligatorio_faltante",
                            "descripcion": f"Campo obligatorio '{columna_encontrada}' tiene {valores_faltantes} valores faltantes",
                            "severidad": "alta",
                            "columna": columna_encontrada,
                            "valor": valores_faltantes
                        })
            
            # 5. Duplicados en campos únicos
            campos_unicos = ['documento', 'id_estudiante', 'email']
            for campo_unico in campos_unicos:
                columna_encontrada = None
                for col in df.columns:
                    if campo_unico.lower() in col.lower():
                        columna_encontrada = col
                        break
                
                if columna_encontrada:
                    valores_validos = df[columna_encontrada].dropna()
                    if len(valores_validos) > 0:
                        duplicados = valores_validos.duplicated().sum()
                        if duplicados > 0:
                            problemas.append({
                                "tipo": "duplicados_en_campo_unico",
                                "descripcion": f"Campo único '{columna_encontrada}' tiene {duplicados} valores duplicados",
                                "severidad": "alta",
                                "columna": columna_encontrada,
                                "valor": duplicados
                            })
            
            # 6. Valores imposibles en fecha de nacimiento (edades)
            col_fecha_nacimiento = None
            for col in df.columns:
                if 'fecha' in col.lower() and 'nacimiento' in col.lower():
                    col_fecha_nacimiento = col
                    break
            
            if col_fecha_nacimiento:
                edades_imposibles = []
                fecha_actual = pd.Timestamp.now()
                
                for idx, valor in df[col_fecha_nacimiento].items():
                    if pd.notna(valor):
                        try:
                            fecha_nac = pd.to_datetime(str(valor), errors='coerce')
                            if pd.notna(fecha_nac):
                                edad = (fecha_actual - fecha_nac).days / 365.25
                                if edad < 15 or edad > 80:  # Edades improbables para estudiantes
                                    edades_imposibles.append({
                                        "fila": idx,
                                        "fecha_nacimiento": str(valor),
                                        "edad_calculada": round(edad, 1)
                                    })
                        except:
                            pass
                
                if edades_imposibles:
                    problemas.append({
                        "tipo": "edades_improbables",
                        "descripcion": f"{len(edades_imposibles)} estudiantes con edades improbables",
                        "severidad": "media",
                        "columna": col_fecha_nacimiento,
                        "valor": len(edades_imposibles),
                        "ejemplos": edades_imposibles[:3]
                    })
            
            # 7. Emails malformados
            col_email = None
            for col in df.columns:
                if 'email' in col.lower() or 'correo' in col.lower():
                    col_email = col
                    break
            
            if col_email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                emails_invalidos = []
                
                for idx, valor in df[col_email].items():
                    if pd.notna(valor):
                        valor_str = str(valor).strip()
                        if not re.match(email_pattern, valor_str):
                            emails_invalidos.append({
                                "fila": idx,
                                "email": valor_str
                            })
                
                if emails_invalidos:
                    problemas.append({
                        "tipo": "emails_malformados",
                        "descripcion": f"{len(emails_invalidos)} emails con formato inválido",
                        "severidad": "media",
                        "columna": col_email,
                        "valor": len(emails_invalidos),
                        "ejemplos": emails_invalidos[:5]
                    })
            
            # 8. Filas completamente vacías (ya existente pero mejorado)
            if len(df) > 0:
                filas_vacias = df.isnull().all(axis=1).sum()
                filas_casi_vacias = 0
                
                for idx, fila in df.iterrows():
                    valores_no_nulos = fila.dropna()
                    if len(valores_no_nulos) <= 2:  # Menos de 3 campos completados
                        filas_casi_vacias += 1
                
                if filas_vacias > 0:
                    problemas.append({
                        "tipo": "filas_vacias",
                        "descripcion": f"{filas_vacias} filas completamente vacías",
                        "severidad": "media",
                        "valor": filas_vacias
                    })
                
                if filas_casi_vacias > 0:
                    problemas.append({
                        "tipo": "filas_casi_vacias",
                        "descripcion": f"{filas_casi_vacias} filas con muy pocos datos (≤2 campos)",
                        "severidad": "media",
                        "valor": filas_casi_vacias
                    })
        
        except Exception as e:
            problemas.append({
                "tipo": "error_analisis",
                "descripcion": f"Error durante el análisis: {str(e)}",
                "severidad": "alta"
            })
        
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
            "calidad_promedio": 30
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
                # Cálculo más estricto de calidad promedio
                problemas_por_hoja = resumen["total_problemas"] / resumen["total_hojas_analizadas"]
                problemas_altos = resumen["problemas_por_severidad"]["alta"]
                problemas_medios = resumen["problemas_por_severidad"]["media"]
                
                # Penalización más severa por problemas
                penalizacion_alta = problemas_altos * 15  # 15 puntos por problema alto
                penalizacion_media = problemas_medios * 8  # 8 puntos por problema medio
                penalizacion_total = penalizacion_alta + penalizacion_media
                
                resumen["calidad_promedio"] = max(0, 100 - penalizacion_total)
        
        except Exception as e:
            pass
        
        return resumen
    
    def _calcular_puntuacion_calidad(self, resultado_analisis: Dict[str, Any]) -> float:
        """Calcula puntuación de calidad del 0 al 100 con criterios más estrictos"""
        try:
            if "metricas_calidad_detalladas" in resultado_analisis:
                metricas = resultado_analisis["metricas_calidad_detalladas"]
                
                # Ponderación más estricta
                completitud_peso = 0.3
                exactitud_peso = 0.35  # Mayor peso a exactitud
                unicidad_peso = 0.15
                consistencia_peso = 0.2
                
                puntuacion = (
                    metricas["completitud"] * completitud_peso +
                    metricas["exactitud"] * exactitud_peso + 
                    metricas["unicidad"] * unicidad_peso +
                    metricas["consistencia"] * consistencia_peso
                )
                
                # Aplicar penalización adicional por número total de problemas
                resumen_general = resultado_analisis.get("resumen_general", {})
                total_problemas = resumen_general.get("total_problemas", 0)
                problemas_altos = resumen_general.get("problemas_por_severidad", {}).get("alta", 0)
                
                # Penalización extra por problemas críticos
                if problemas_altos > 0:
                    penalizacion_critica = min(30, problemas_altos * 5)  # Max 30% penalización
                    puntuacion *= (1 - penalizacion_critica / 100)
                
                return max(0, min(100, puntuacion))
            
            return 30.0
            
        except:
            return 30.0
    
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
                "completitud": 30.0,
                "exactitud": 25.0,
                "unicidad": 40.0,
                "consistencia": 35.0
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
            puntuacion = resultado_analisis.get("puntuacion_calidad", 30)
            
            # Determinar color basado en puntuación
            if puntuacion >= 80:
                color_bar = "green"
            elif puntuacion >= 60:
                color_bar = "yellow"
            elif puntuacion >= 40:
                color_bar = "orange"
            else:
                color_bar = "red"
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = puntuacion,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Puntuación de Calidad"},
                delta = {'reference': 70, 'increasing': {'color': "green"}},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color_bar},
                    'steps': [
                        {'range': [0, 40], 'color': "lightcoral"},
                        {'range': [40, 60], 'color': "lightyellow"},
                        {'range': [60, 80], 'color': "lightgreen"},
                        {'range': [80, 100], 'color': "darkgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
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
- Completitud: {metricas_calidad.get('completitud', 30):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('completitud', 30):.1f}%)
- Exactitud: {metricas_calidad.get('exactitud', 25):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('exactitud', 25):.1f}%)
- Unicidad: {metricas_calidad.get('unicidad', 40):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('unicidad', 40):.1f}%)
- Consistencia: {metricas_calidad.get('consistencia', 35):.1f}% (% de no cumplimiento: {100-metricas_calidad.get('consistencia', 35):.1f}%)

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