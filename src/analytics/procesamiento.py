frames = {
    1: [(10, 20), (30, 40), (50, 60), (70, 80), (90, 100), (110, 120)],
    2: [(15, 25), (35, 45)],
    3: [(100, 200), (120, 220), (140, 240),
        (160, 260), (180, 280), (200, 300),
        (220, 320), (240, 340), (260, 360), 
        (280, 380), (300, 400), (320, 420), 
        (340, 440), (360, 460), (380, 480),
        (400,500)],
}

def obtener_zona(x): 
    if x < 200:
        return 1
    elif x < 400:
        return 2
    else:
        return 3
    
def calcular_densidad(n):
    if n <= 5:
        return "Baja"
    elif n <= 15:
        return "Media"
    else:
        return "Alta"

def detectar_patron(zonas):
    total = sum(zonas.values())
    if total == 0:
        return "Sin datos"

    z1, z2, z3 = zonas["Z1"], zonas["Z2"], zonas["Z3"]

    p1 = z1 / total
    p2 = z2 / total
    p3 = z3 / total

    if max(p1, p2, p3) > 0.6:
        if p1 == max(p1, p2, p3):
            return "Alta concentración en carril 1"
        elif p2 == max(p1, p2, p3):
            return "Alta concentración en carril 2"
        else:
            return "Alta concentración en carril 3"

    if max(p1, p2, p3) - min(p1, p2, p3) > 0.3:
        return "Distribución desigual"

    return "Flujo equilibrado"

def clasificar_trafico(densidad, dispersion):
    if densidad == "Alta":
        if dispersion < 50000:
            return "Congestionado (compacto)"
        else:
            return "Congestionado (disperso)"

    elif densidad == "Media":
        if dispersion < 40000:
            return "Moderado con acumulación"
        else:
            return "Moderado fluido"

    else:
        return "Fluido"

def procesar_frame(vehiculos):   
    n = len(vehiculos)
    if n == 0:
        return None

    z1 = z2 = z3 = 0

    for x, y in vehiculos:
        zona = obtener_zona(x)

        if zona == 1: z1 += 1
        elif zona == 2: z2 += 1
        else: z3 += 1

    dispersion = 0
    for i in range(n):
        for j in range(i+1, n):
            dx = vehiculos[i][0] - vehiculos[j][0]
            dy = vehiculos[i][1] - vehiculos[j][1]
            dispersion += (dx**2 + dy**2)

    dispersion = dispersion / n

    return {
        "n_vehiculos": n,
        "densidad": calcular_densidad(n),
        "zonas": {"Z1": z1, "Z2": z2, "Z3": z3},
        "dispersion": dispersion
    }

def comparar_frames(actual, anterior):
    if not anterior:
        return "Sin referencia"

    diff = actual["n_vehiculos"] - anterior["n_vehiculos"]

    ratio = diff / (anterior["n_vehiculos"] + 1)

    if ratio > 0.5:
        return "Incremento brusco"
    elif ratio > 0.1:
        return "Incremento gradual"
    elif ratio < -0.5:
        return "Caída brusca"
    elif ratio < -0.1:
        return "Disminución gradual"
    else:
        return "Estable"