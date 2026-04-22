class AnalizadorTrafico:
    def __init__(self):
        self.metricas_anteriores = None
        
        self.historial_densidad = []

    def clasificar_trafico(self, densidad):
        if densidad >= 100:
            return "CONGESTIONADO"
        elif densidad >= 30:
            return "MEDIO"
        else:
            return "FLUIDO"
    
    def analizar_cambios(self):

        if len(self.historial_densidad) < 10:
            return "Recopilando datos..."

        pasado = self.historial_densidad[-10:-5]
        actual = self.historial_densidad[-5:]

        promedio_pasado = sum(pasado) / len(pasado)
        promedio_actual = sum(actual) / len(actual)

        diferencia = promedio_actual - promedio_pasado

        if diferencia >= 15:
            return "Aumento progresivo de tráfico"
        elif diferencia <= -15:
            return "Disminución de tráfico"
        else:
            return "Tráfico estable"

   
    def procesar_frame_vehiculo(self, vehiculos, tiempo_segundos):
        densidad_actual = len(vehiculos)
        self.historial_densidad.append(densidad_actual)
        
        if tiempo_segundos > 0:
            flujo_actual = densidad_actual / tiempo_segundos
        else:
            flujo_actual = 0

        velocidad_simulada = 0
        dispersión = 0
        actividad_espacial = 0

        if densidad_actual > 0:
            velocidades = []
            for v in vehiculos:
                velocidad = (v.get("x", 0)**2 + v.get("y", 0)**2) ** 0.5
                velocidades.append(velocidad)

            velocidad_simulada = sum(velocidades) / densidad_actual

            xs = [v.get("x", 0) for v in vehiculos]
            ys = [v.get("y", 0) for v in vehiculos]
            centro_x = sum(xs) / densidad_actual
            centro_y = sum(ys) / densidad_actual

            for v in vehiculos:
                dx = v.get("x", 0) - centro_x
                dy = v.get("y", 0) - centro_y
                dispersión += (dx**2 + dy**2)
            dispersión /= densidad_actual

            actividad_espacial = velocidad_simulada / (1 + dispersión)
            
        metricas_calculadas = {
            "densidad": densidad_actual,
            "flujo_vehiculos_seg": flujo_actual,
            "velocidad_simulada": velocidad_simulada,
            "dispersion": dispersión,
            "actividad_espacial": actividad_espacial
        }
        
        estado = self.clasificar_trafico(densidad_actual)
        cambios = self.analizar_cambios()
        
        self.metricas_anteriores = metricas_calculadas
        
        return {
            "numeros": metricas_calculadas,
            "estado": estado,
            "cambio_frame": cambios,
        }
