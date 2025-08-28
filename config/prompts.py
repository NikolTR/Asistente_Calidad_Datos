"""
Plantillas de prompts para la IA
"""

class Prompts:
    """Plantillas de prompts para diferentes tipos de análisis"""
    
    ANALISIS_CALIDAD = """
Eres un experto analista de datos que trabaja en una institución de educación superior. Analiza la siguiente información sobre un archivo Excel y proporciona un reporte detallado sobre la calidad de los datos.

INFORMACIÓN DEL ARCHIVO:
- Nombre: {nombre_archivo}
- Número de filas: {num_filas}
- Número de columnas: {num_columnas}
- Hojas: {hojas}

ANÁLISIS REALIZADO:
{analisis_tecnico}

PROBLEMAS DETECTADOS:
{problemas}

Proporciona un reporte en español que incluya:
1. **Resumen Ejecutivo**: Evaluación general de la calidad (Excelente/Buena/Regular/Mala)
2. **Problemas Identificados**: Lista detallada de issues encontrados
3. **Recomendaciones**: Acciones específicas para mejorar la calidad
4. **Priorización**: Qué problemas resolver primero

Sé específico y práctico en tus recomendaciones.
"""

    EXPLICACION_PROBLEMA = """
Explica de manera clara y pedagógica el siguiente problema de calidad de datos:

PROBLEMA: {problema}
CONTEXTO: {contexto}
IMPACTO: {impacto}

Proporciona:
1. **¿Qué significa este problema?**: Explicación simple
2. **¿Por qué es importante?**: Consecuencias de no solucionarlo
3. **¿Cómo solucionarlo?**: Pasos específicos para corregirlo
4. **Ejemplo práctico**: Un caso concreto de cómo aplicar la solución

Responde en español de manera clara y práctica.
"""

    SUGERENCIAS_LIMPIEZA = """
Basándote en el análisis de calidad de datos, genera sugerencias específicas de limpieza para este archivo Excel:

DATOS DEL ARCHIVO:
{info_archivo}

PROBLEMAS DETECTADOS:
{problemas_detectados}

Proporciona sugerencias concretas organizadas por:
1. **Limpieza Inmediata**: Problemas críticos que deben resolverse ahora
2. **Mejoras Estructurales**: Cambios para mejorar la organización
3. **Validaciones**: Reglas para mantener la calidad a futuro
4. **Automatización**: Procesos que se pueden automatizar

Cada sugerencia debe incluir:
- Descripción clara del problema
- Pasos específicos para solucionarlo
- Herramientas recomendadas (Excel, Python, etc.)

Responde en español de manera práctica y accionable.
"""

    INTERPRETACION_GRAFICOS = """
Interpreta los siguientes gráficos de análisis de datos y explica qué revelan sobre la calidad:

GRÁFICOS GENERADOS:
{descripcion_graficos}

MÉTRICAS CLAVE:
{metricas}

Proporciona una interpretación que incluya:
1. **Patrones Identificados**: Qué revelan los gráficos
2. **Anomalías**: Valores o comportamientos inusuales
3. **Tendencias**: Patrones que se observan en los datos
4. **Conclusiones**: Qué significa esto para la calidad general

Explica en español de manera clara, como si fueras un consultor de datos para una institución de educación superior hablando con un cliente no técnico.
"""