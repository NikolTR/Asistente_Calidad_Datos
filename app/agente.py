"""
Agente principal para análisis de Excel con IA
"""
import requests
import json
import streamlit as st
from typing import Dict, Any, Optional
from config.configuracion import Configuracion
from config.prompts import Prompts
from app.analizador import AnalizadorCalidadDatos
from app.utilidades import generar_nombre_archivo, guardar_reporte

class AgenteExcelIA:
    """Agente principal que coordina el análisis y la IA"""
    
    def __init__(self):
        self.configuracion = Configuracion()
        self.analizador = AnalizadorCalidadDatos()
        self.prompts = Prompts()
        self.estado_conversacion = []
    
    def verificar_conexion_ollama(self) -> Dict[str, Any]:
        """Verifica si Ollama está disponible"""
        try:
            response = requests.get(
                f"{self.configuracion.OLLAMA_URL}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                modelos = response.json().get("models", [])
                modelo_disponible = any(
                    self.configuracion.MODELO_IA in modelo.get("name", "")
                    for modelo in modelos
                )
                
                return {
                    "conectado": True,
                    "modelo_disponible": modelo_disponible,
                    "modelos": [m.get("name", "") for m in modelos]
                }
            else:
                return {"conectado": False, "error": "Ollama no responde"}
                
        except requests.exceptions.RequestException as e:
            return {"conectado": False, "error": f"Error de conexión: {str(e)}"}
    
    def consultar_ia(self, prompt: str, contexto: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía consulta a Ollama y obtiene respuesta
        
        Args:
            prompt: Prompt para enviar a la IA
            contexto: Contexto adicional opcional
        
        Returns:
            Dict con respuesta de la IA
        """
        try:
            # Preparar el prompt completo
            prompt_completo = prompt
            if contexto:
                prompt_completo = f"CONTEXTO:\n{contexto}\n\nPROMPT:\n{prompt}"
            
            # Preparar datos para Ollama
            datos = {
                "model": self.configuracion.MODELO_IA,
                "prompt": prompt_completo,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            # Enviar solicitud
            response = requests.post(
                f"{self.configuracion.OLLAMA_URL}/api/generate",
                json=datos,
                timeout=60
            )
            
            if response.status_code == 200:
                resultado = response.json()
                respuesta_ia = resultado.get("response", "").strip()
                
                # Guardar en historial de conversación
                self.estado_conversacion.append({
                    "tipo": "consulta",
                    "prompt": prompt,
                    "respuesta": respuesta_ia,
                    "timestamp": json.dumps({"status": "ok"})  # Placeholder para timestamp
                })
                
                return {
                    "exito": True,
                    "respuesta": respuesta_ia,
                    "tokens_usados": resultado.get("eval_count", 0)
                }
            else:
                return {
                    "exito": False,
                    "error": f"Error HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {"exito": False, "error": "Timeout: La IA tardó mucho en responder"}
        except requests.exceptions.RequestException as e:
            return {"exito": False, "error": f"Error de conexión: {str(e)}"}
        except Exception as e:
            return {"exito": False, "error": f"Error inesperado: {str(e)}"}
    
    def generar_reporte_calidad(self, info_archivo: Dict[str, Any], resultado_analisis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera reporte de calidad usando IA
        
        Args:
            info_archivo: Información del archivo Excel
            resultado_analisis: Resultado del análisis técnico
        
        Returns:
            Dict con el reporte generado
        """
        try:
            # Preparar información para el prompt
            info_general = info_archivo.get("info_general", {})
            resumen_problemas = self.analizador.obtener_resumen_problemas(resultado_analisis)
            
            # Crear prompt usando template
            prompt = self.prompts.ANALISIS_CALIDAD.format(
                nombre_archivo=info_general.get("nombre_archivo", "Archivo sin nombre"),
                num_filas=resultado_analisis.get("resumen_general", {}).get("total_filas", 0),
                num_columnas=resultado_analisis.get("resumen_general", {}).get("total_columnas", 0),
                hojas=", ".join([h["nombre"] for h in info_archivo.get("hojas", [])]),
                analisis_tecnico=self._resumir_analisis_tecnico(resultado_analisis),
                problemas=resumen_problemas
            )
            
            # Consultar IA
            respuesta_ia = self.consultar_ia(prompt)
            
            if respuesta_ia["exito"]:
                # Guardar reporte
                nombre_reporte = generar_nombre_archivo("reporte_calidad", ".md")
                ruta_reporte = guardar_reporte(
                    respuesta_ia["respuesta"],
                    nombre_reporte
                )
                
                return {
                    "exito": True,
                    "reporte": respuesta_ia["respuesta"],
                    "archivo_guardado": ruta_reporte,
                    "nombre_archivo": nombre_reporte
                }
            else:
                return {
                    "exito": False,
                    "error": respuesta_ia["error"]
                }
                
        except Exception as e:
            return {"exito": False, "error": f"Error generando reporte: {str(e)}"}
    
    def explicar_problema_especifico(self, problema: Dict[str, Any], contexto_archivo: str = "") -> Dict[str, Any]:
        """
        Explica un problema específico usando IA
        
        Args:
            problema: Diccionario con información del problema
            contexto_archivo: Contexto adicional del archivo
        
        Returns:
            Dict con explicación del problema
        """
        try:
            # Preparar información del problema
            descripcion_problema = problema.get("descripcion", "Problema no especificado")
            tipo_problema = problema.get("tipo", "desconocido")
            severidad = problema.get("severidad", "media")
            
            # Determinar impacto basado en severidad
            impactos = {
                "alta": "Puede causar errores significativos en análisis y decisiones",
                "media": "Puede afectar la precisión de los resultados",
                "baja": "Impacto menor pero recomendable corregir"
            }
            impacto = impactos.get(severidad, "Impacto variable")
            
            # Crear prompt
            prompt = self.prompts.EXPLICACION_PROBLEMA.format(
                problema=descripcion_problema,
                contexto=f"Tipo: {tipo_problema}, Severidad: {severidad}. {contexto_archivo}",
                impacto=impacto
            )
            
            # Consultar IA
            respuesta_ia = self.consultar_ia(prompt)
            
            if respuesta_ia["exito"]:
                return {
                    "exito": True,
                    "explicacion": respuesta_ia["respuesta"]
                }
            else:
                return {
                    "exito": False,
                    "error": respuesta_ia["error"]
                }
                
        except Exception as e:
            return {"exito": False, "error": f"Error explicando problema: {str(e)}"}
    
    def generar_sugerencias_limpieza(self, info_archivo: Dict[str, Any], resultado_analisis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera sugerencias específicas de limpieza usando IA
        
        Args:
            info_archivo: Información del archivo
            resultado_analisis: Resultado del análisis
        
        Returns:
            Dict con sugerencias de limpieza
        """
        try:
            # Preparar información
            info_consolidada = {
                "nombre": info_archivo.get("info_general", {}).get("nombre_archivo", ""),
                "hojas": len(info_archivo.get("hojas", [])),
                "puntuacion_calidad": resultado_analisis.get("puntuacion_calidad", 0)
            }
            
            problemas_detectados = self.analizador.obtener_resumen_problemas(resultado_analisis)
            
            # Crear prompt
            prompt = self.prompts.SUGERENCIAS_LIMPIEZA.format(
                info_archivo=json.dumps(info_consolidada, indent=2),
                problemas_detectados=problemas_detectados
            )
            
            # Consultar IA
            respuesta_ia = self.consultar_ia(prompt)
            
            if respuesta_ia["exito"]:
                return {
                    "exito": True,
                    "sugerencias": respuesta_ia["respuesta"]
                }
            else:
                return {
                    "exito": False,
                    "error": respuesta_ia["error"]
                }
                
        except Exception as e:
            return {"exito": False, "error": f"Error generando sugerencias: {str(e)}"}
    
    def interpretar_graficos(self, resultado_analisis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpreta los gráficos generados usando IA
        
        Args:
            resultado_analisis: Resultado completo del análisis
        
        Returns:
            Dict con interpretación de gráficos
        """
        try:
            # Preparar descripción de gráficos
            graficos_info = self._describir_graficos(resultado_analisis)
            
            # Preparar métricas clave
            metricas = {
                "puntuacion_calidad": resultado_analisis.get("puntuacion_calidad", 0),
                "total_problemas": resultado_analisis.get("resumen_general", {}).get("total_problemas", 0),
                "hojas_analizadas": resultado_analisis.get("resumen_general", {}).get("total_hojas_analizadas", 0)
            }
            
            # Crear prompt
            prompt = self.prompts.INTERPRETACION_GRAFICOS.format(
                descripcion_graficos=graficos_info,
                metricas=json.dumps(metricas, indent=2)
            )
            
            # Consultar IA
            respuesta_ia = self.consultar_ia(prompt)
            
            if respuesta_ia["exito"]:
                return {
                    "exito": True,
                    "interpretacion": respuesta_ia["respuesta"]
                }
            else:
                return {
                    "exito": False,
                    "error": respuesta_ia["error"]
                }
                
        except Exception as e:
            return {"exito": False, "error": f"Error interpretando gráficos: {str(e)}"}
    
    def chat_interactivo(self, pregunta_usuario: str, contexto_archivo: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Maneja chat interactivo sobre el archivo
        
        Args:
            pregunta_usuario: Pregunta del usuario
            contexto_archivo: Contexto del archivo analizado
        
        Returns:
            Dict con respuesta del chat
        """
        try:
            # Preparar contexto si está disponible
            contexto_str = ""
            if contexto_archivo:
                info_general = contexto_archivo.get("info_general", {})
                contexto_str = f"""
INFORMACIÓN DEL ARCHIVO ACTUAL:
- Nombre: {info_general.get('nombre_archivo', 'N/A')}
- Hojas: {info_general.get('total_hojas', 0)}
- Hojas con datos: {info_general.get('hojas_con_datos', 0)}
"""
            
            # Crear prompt para chat
            prompt = f"""
Eres un asistente especializado en análisis de datos Excel. El usuario tiene una pregunta sobre su archivo.

{contexto_str}

PREGUNTA DEL USUARIO: {pregunta_usuario}

Responde de manera clara, práctica y en español. Si la pregunta no está relacionada con análisis de datos, redirige amablemente hacia temas de Excel y calidad de datos.
"""
            
            # Consultar IA
            respuesta_ia = self.consultar_ia(prompt)
            
            if respuesta_ia["exito"]:
                return {
                    "exito": True,
                    "respuesta": respuesta_ia["respuesta"]
                }
            else:
                return {
                    "exito": False,
                    "error": respuesta_ia["error"]
                }
                
        except Exception as e:
            return {"exito": False, "error": f"Error en chat: {str(e)}"}
    
    def _resumir_analisis_tecnico(self, resultado_analisis: Dict[str, Any]) -> str:
        """Resume el análisis técnico para incluir en prompts"""
        try:
            resumen = resultado_analisis.get("resumen_general", {})
            
            return f"""
Análisis técnico completado:
- Hojas analizadas: {resumen.get('total_hojas_analizadas', 0)}
- Total de filas: {resumen.get('total_filas', 0)}
- Total de columnas: {resumen.get('total_columnas', 0)}
- Problemas encontrados: {resumen.get('total_problemas', 0)}
- Puntuación de calidad: {resultado_analisis.get('puntuacion_calidad', 0):.1f}/100
"""
        except:
            return "Error resumiendo análisis técnico"
    
    def _describir_graficos(self, resultado_analisis: Dict[str, Any]) -> str:
        """Describe los gráficos para interpretación por IA"""
        try:
            descripcion = "GRÁFICOS GENERADOS:\n"
            
            # Describir cada tipo de gráfico
            graficos = resultado_analisis.get("graficos", {})
            
            if "problemas_por_hoja" in graficos:
                descripcion += "1. Gráfico de barras apiladas mostrando problemas por hoja, categorizados por severidad\n"
            
            if "valores_nulos" in graficos:
                descripcion += "2. Gráfico de barras con porcentaje de valores nulos por hoja\n"
            
            if "calidad_general" in graficos:
                puntuacion = resultado_analisis.get("puntuacion_calidad", 0)
                descripcion += f"3. Medidor de calidad general mostrando {puntuacion:.1f}/100 puntos\n"
            
            if "tipos_datos" in graficos:
                descripcion += "4. Gráfico circular con distribución de tipos de datos\n"
            
            return descripcion
            
        except:
            return "Error describiendo gráficos"
    
    def obtener_estado_sistema(self) -> Dict[str, Any]:
        """Obtiene estado actual del sistema"""
        return {
            "ollama_conectado": self.verificar_conexion_ollama()["conectado"],
            "modelo_ia": self.configuracion.MODELO_IA,
            "consultas_realizadas": len(self.estado_conversacion),
            "configuracion_valida": len(self.configuracion.verificar_configuracion()) == 0
        }