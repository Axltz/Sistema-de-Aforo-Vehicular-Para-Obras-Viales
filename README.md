# Sistema Inteligente de Aforo Vehicular para Obras Viales

Este proyecto es un sistema de visión artificial en Python diseñado para monitorear, contar y analizar el flujo vehicular en tiempo real mediante el uso de redes neuronales (YOLO) y algoritmos espaciales (DBSCAN). 

El sistema está empaquetado en una interfaz gráfica moderna orientada a entornos de monitoreo vial profesional y permite comprimir datos de telemetría localmente usando el algoritmo de Huffman.

## Características Principales
- **Conteo Vehicular Bidireccional:** Tracking persistente usando YOLO y cruces de línea virtual adaptativa.
- **Detección de Congestiones:** Algoritmos de clustering espacial que detectan si los autos forman un embotellamiento.
- **Análisis de Fluidez:** Clasifica el tráfico (libre, moderado, denso, congestionado) basado en densidad y velocidad de flujo.
- **GUI Profesional:** Un panel de control tipo centro de monitoreo que integra video, gráficas en vivo y consolas de reportes.
- **Exportación a Huffman:** Capacidad real para empaquetar y comprimir los json generados a archivos binarios de bajo peso (ideal para redes de bajo ancho de banda).

## Requisitos e Instalación

1. Asegúrate de tener Python 3.9+ instalado.
2. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución del Sistema

Arranca la aplicación mediante su módulo principal:
```bash
python -m src.app
```

Una vez abierto:
1. Dale al botón **Iniciar** o usa **Cambiar Video** si deseas cargar tu propio archivo MP4.
2. El sistema se auto-calibrará en los primeros 30 frames.
3. Puedes habilitar los reportes automáticos en consola (5s, 10s, 30s) o presionar "Exportar JSON / Huffman" de forma manual.
4. Usa "Descomprimir Reporte" para validar la tasa de compresión y ver los datos empaquetados.

## Organización del Proyecto

- `src/app.py` y `__main__.py`: Lanzadores.
- `src/gui.py`: Contiene toda la lógica de la interfaz (CustomTkinter) y conecta con el pipeline visual.
- `src/analytics/`: Matemáticas puras. Clustering espacial, grafos, cálculo de métricas de congestión y algoritmos de compresión.
- `src/pipeline/`: El orquestador que fusiona los datos de YOLO y la analítica.
- `src/detection/`: Maneja el modelo neuronal y los parámetros de inferencia.
- `docs/Explicacion_Sistema.md`: Una guía rápida de cómo funciona matemáticamente el sistema para exposiciones o consultas técnicas.
