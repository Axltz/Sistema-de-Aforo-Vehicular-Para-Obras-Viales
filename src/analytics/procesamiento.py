# Datos simulados: Coordenadas (x, y) de los vehículos por frame
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
        return "Carril 1"
    elif x < 400:
        return "Carril 2"
    else:
        return "Carril 3"
    
def calcular_densidad(n):
    if n <= 5:
        return "Baja"
    elif n <= 15:
        return "Media"
    else:
        return "Alta"

resultados = []

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

    return {
        "n_vehiculos": n,
        "densidad": calcular_densidad(n),
        "zonas": {"Z1": z1, "Z2": z2, "Z3": z3},
        "dispersion": dispersion
    }
