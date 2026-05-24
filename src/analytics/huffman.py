import heapq
import json
from collections import Counter

class NodoHuffman:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def construir_arbol_huffman(texto):
    frecuencias = Counter(texto)
    heap = [NodoHuffman(char, freq) for char, freq in frecuencias.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        nodo_izq = heapq.heappop(heap)
        nodo_der = heapq.heappop(heap)
        nodo_padre = NodoHuffman(None, nodo_izq.freq + nodo_der.freq)
        nodo_padre.left = nodo_izq
        nodo_padre.right = nodo_der
        heapq.heappush(heap, nodo_padre)
    return heap[0] if heap else None

def generar_codigos(nodo, codigo_actual="", codigos=None):
    if codigos is None:
        codigos = {}
    if nodo is not None:
        if nodo.char is not None:
            codigos[nodo.char] = codigo_actual
        generar_codigos(nodo.left, codigo_actual + "0", codigos)
        generar_codigos(nodo.right, codigo_actual + "1", codigos)
    return codigos

def comprimir_texto_huffman(texto):
    if not texto:
        return "", {}
    raiz = construir_arbol_huffman(texto)
    diccionario_codigos = generar_codigos(raiz)
    texto_comprimido = "".join([diccionario_codigos[char] for char in texto])
    return texto_comprimido, diccionario_codigos

def descompresor_huffman(ruta_bin, ruta_dict):
    with open(ruta_dict, "r", encoding="utf-8") as f:
        codigos = json.load(f)
    codigos_invertidos = {v: k for k, v in codigos.items()}
    
    with open(ruta_bin, "rb") as f:
        contenido_bytes = f.read()
    
    cadena_bits = "".join([f"{byte:08b}" for byte in contenido_bytes])
        
    texto_decodificado = ""
    codigo_actual = ""
    for bit in cadena_bits:
        codigo_actual += bit
        if codigo_actual in codigos_invertidos:
            texto_decodificado += codigos_invertidos[codigo_actual]
            codigo_actual = ""
            
    # Buscamos dónde está la última llave de cierre '}' del JSON real
    # para recortar los caracteres extra generados por los bits de relleno
    fin_json = texto_decodificado.rfind('}') + 1
    texto_limpio = texto_decodificado[:fin_json]
            
    return json.loads(texto_limpio)