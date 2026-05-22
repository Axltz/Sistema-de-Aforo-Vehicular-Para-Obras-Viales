# SISTEMA INTELIGENTE DE AFORO VEHICULAR PARA OBRAS VIALES

Sistema de visión artificial optimizado y dashboard interactivo en tiempo real diseñado para el conteo, monitoreo y análisis del flujo vehicular en zonas de obra vial.

Este software reemplaza los conteos manuales tradicionales por un sistema de monitoreo inteligente local 100% offline, recolectando datos de tráfico precisos de forma segura y económica.

---

## 🚀 Arquitectura Local y Offline

El sistema funciona con un diseño híbrido local que no requiere conexiones de red externas ni bases de datos en la nube (cero APIs, cero dependencias online):

```
+------------------------------------+          +------------------------------------+
|  Motor Python (OpenCV + YOLO)      |          |  Dashboard Frontend (HTML5/JS/CSS)  |
|  - Procesa video o webcam          |          |  - Corre localmente (http.server)  |
|  - Frame skipping (optimiza CPU)   |          |  - Polling dinámico cada 2 segs    |
|  - Conteo y analítica adaptativa   |          |  - Gráfico neón de Horas Pico      |
+------------------------------------+          +------------------------------------+
                  |                                               |
                  v (Escribe periódicamente)                      v (Lee de forma offline)
      data/metrics_live.json    ----------------------------------+
      data/logs/metrics_HOY.jsonl --------------------------------+
```

---

## 🛠️ Tecnologías Empleadas

* **Backend (Procesamiento):** Python 3.x, OpenCV (manejo de video/cámara), Ultralytics YOLOv8/YOLOv11 Nano (detección y tracking neuronal ligero).
* **Frontend (Visualización):** HTML5 Semántico, CSS3 con estética de Centro de Control (Neón/Glassmorphism/Partículas), Chart.js (Gráfico lineal de flujo en tiempo real + Gráfico de barras de Horas Pico).
* **Compresión:** Implementación de un algoritmo de **Compresión Huffman** nativo en el navegador para empaquetar, comprimir y descargar los datos históricos acumulados sin consumir ancho de banda.

---

## 📦 Requisitos e Instalación

1. **Clonar o descargar el repositorio** en tu computadora.
2. **Crear y activar un entorno virtual de Python** (Recomendado):
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   ```
3. **Instalar las dependencias locales:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Nota: Se utiliza la librería oficial de `ultralytics` para YOLO y `opencv-python` para la interfaz de cámara y video).*

---

## 🚦 Instrucciones de Uso (Paso a Paso)

Para arrancar el sistema en demo o tiempo real de forma local, se ejecutan únicamente **dos comandos** en terminales separadas:

### Terminal 1: Iniciar el Motor de Inteligencia (Python)

Puedes ejecutar el motor de dos formas:

* **Opción A (Video de Prueba precargado):**
  ```bash
  python src/main.py
  ```
* **Opción B (Cámara Web o Stream RTSP en tiempo real):**
  ```bash
  python src/main.py --webcam
  ```
  *(Opcional: Si deseas usar otro video en particular, usa `python src/main.py --video data/videos/nombre_video.mp4`)*

* **Teclas útiles en la ventana de video:**
  * Presiona `Q` para apagar el sistema correctamente.
  * Presiona `E` para forzar la exportación de un reporte consolidado instantáneo a `data/json/traffic_data.json`.

---

### Terminal 2: Iniciar el Servidor Web del Dashboard

Ejecuta el servidor web estático integrado en Python desde la raíz del proyecto para que el navegador pueda acceder de forma segura a los archivos locales de datos:

```bash
python -m http.server 8080
```

---

### Abrir el Dashboard en el Navegador

Una vez encendidos ambos comandos, abre tu navegador web preferido e ingresa a la siguiente dirección:

👉 **[http://localhost:8080/frontend/src/index.html](http://localhost:8080/frontend/src/index.html)**

El dashboard se conectará automáticamente con el motor local. Podrás ver en tiempo real:
1. **Aforo Total acumulado** y **Vehículos en Escena**.
2. **Velocidad de marcha** y **Fluidez de avance** adaptativa.
3. **Gráfico interactivo de Horas Pico** (barras con colores neón agrupadas por hora) calculado automáticamente a partir del historial del día.
4. **Exportar JSON y Huffman (.hfm):** Descargar copias de seguridad de las estadísticas directamente en tu computadora 100% offline.

---

## 📁 Estructura del Almacenamiento Local

* `data/metrics_live.json`: Contiene las métricas del frame actual del sistema (se sobrescribe cada 10 frames para mantener un uso de disco casi nulo).
* `data/logs/metrics_YYYY-MM-DD.jsonl`: Archivo de log diario donde se van acumulando las líneas de registros (JSONL) de forma cronológica cada 150 frames (~5 segundos) para construir la analítica y horas pico del día.
* `data/videos/trafico3.mp4`: Video muestra utilizado para calibración y pruebas en laboratorio.

---

## 👥 Equipo de Desarrollo

* **Luna Gallegos Nayeli Ximena**
* **Martínez Martínez Axel Guillermo**
* **Mijares Ahuatzi Juan Carlos**

*Proyecto desarrollado para la materia de Análisis de Algoritmos (5to Semestre) — Visualización de alto impacto y procesamiento optimizado en el borde.*
