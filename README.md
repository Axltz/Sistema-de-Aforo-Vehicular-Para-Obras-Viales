# Sistema Inteligente de Aforo Vehicular para Obras Viales

Diseño e implementación de un sistema de visión artificial para el conteo y monitoreo vehicular en zonas de obra vial. Proyecto desarrollado para la materia de Análisis de Algoritmos.

Este proyecto surge como solución a la necesidad de automatizar la recolección de datos de tráfico en zonas de construcción, tareas que tradicionalmente se realizan de manera manual por personal en campo expuesto a riesgos.

---

## Objetivos del Proyecto

* **Detectar vehículos:** Identificar autos, camiones, motocicletas y bicicletas mediante análisis de video.
* **Contabilizar el flujo vehicular:** Registrar de forma automática el volumen de vehículos que cruzan por una línea adaptativa.
* **Analizar comportamiento:** Determinar la velocidad promedio de marcha, el nivel de congestión e identificar agrupaciones de riesgo.
* **Procesar localmente:** Operar de manera 100% local sin requerir de servicios en la nube o conexión a internet una vez inicializado el modelo de detección.

---

## Tecnologías Utilizadas

* **Backend:** Python 3.x, OpenCV (procesamiento de imágenes y video), Ultralytics YOLO (modelo de detección y rastreo de objetos).
* **Frontend:** HTML5, CSS3, JavaScript (Chart.js para las gráficas de flujo en tiempo real y distribución de horas pico).
* **Compresión:** Algoritmo de Huffman nativo implementado en JavaScript para exportación de datos.

---

## Arquitectura de Datos Local

El sistema utiliza una arquitectura desacoplada basada en archivos para permitir su funcionamiento sin conexión a internet:

* El script de Python procesa el video, calcula las métricas y sobrescribe el archivo `data/metrics_live.json` cada 10 frames para mantener los datos en tiempo real.
* Paralelamente, el script añade un registro histórico cada 150 frames al archivo diario en formato JSONL (`data/logs/metrics_YYYY-MM-DD.jsonl`).
* El frontend de JavaScript realiza consultas periódicas (polling) cada 2 segundos a estos archivos locales a través de peticiones HTTP locales.

---

## Instrucciones de Instalación y Uso

### Requisitos Previos

1. Instalar Python 3.x en el equipo.
2. Crear y activar un entorno virtual de Python:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   ```
3. Instalar las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

### Ejecución del Sistema

El sistema requiere la ejecución de dos procesos de forma simultánea. Abre dos terminales diferentes en la carpeta raíz del proyecto y ejecuta los siguientes comandos:

#### Proceso 1: Ejecutar el procesamiento de video en Python

* **Ejecutar con el video de prueba predeterminado:**
  ```bash
  python src/main.py
  ```
* **Ejecutar utilizando la cámara web en tiempo real:**
  ```bash
  python src/main.py --webcam
  ```
* **Ejecutar especificando otro archivo de video:**
  ```bash
  python src/main.py --video ruta/de/tu_video.mp4
  ```

*(Nota: En la ventana del video puedes presionar la tecla 'Q' para detener la ejecución, o la tecla 'E' para exportar un resumen manual).*

#### Proceso 2: Iniciar el servidor local para el Dashboard

En la segunda terminal, inicia el servidor estático web de Python:
```bash
python -m http.server 8080
```

### Visualizar el Dashboard

Abre tu navegador de preferencia e ingresa a la siguiente dirección:

[http://localhost:8080/frontend/src/index.html](http://localhost:8080/frontend/src/index.html)

El frontend mostrará automáticamente las métricas de conteo, estado del tráfico, agrupaciones y el gráfico de barras correspondiente a las horas pico del día actual.

---

## Estructura de Archivos del Proyecto

* `src/main.py`: Punto de entrada que gestiona la captura y el flujo de detección.
* `src/config.py`: Definición de rutas del sistema y parámetros de optimización.
* `src/storage/json_writer.py`: Lógica para escribir el JSON en vivo y el historial diario en formato JSONL.
* `frontend/src/index.html`: Estructura del panel de visualización.
* `frontend/src/app.js`: Script de actualización del Dashboard, manejo de gráficas y compresión Huffman.
* `data/`: Carpeta que almacena los videos de prueba y los registros JSON/JSONL autogenerados.

---

## Equipo de Desarrollo

* Luna Gallegos Nayeli Ximena
* Martínez Martínez Axel Guillermo
* Mijares Ahuatzi Juan Carlos

**Universidad - 5to Semestre**  
Materia: *Análisis de Algoritmos*
