import time
from collections import deque
 
from datos import CAMINO, META, DESCONOCIDO
 
# Todos los algoritmos de ruta tienen la MISMA firma y devuelven lo mismo:
#     algoritmo(mapa_conocido, inicio, meta, costo_celda) -> ResultadoBusqueda
# asi comparar metricas (nodos, tiempo, frontera) es trivial.
 
MOVIMIENTOS = [(-1, 0), (1, 0), (0, -1), (0, 1)]   

 
class ResultadoBusqueda:
    def __init__(self):
        self.camino = []          # celdas por recorrer, SIN incluir la de inicio
        self.costo = 0
        self.generados = 0
        self.expandidos = 0
        self.frontera_max = 0
        self.tiempo_ms = 0.0
 
 
def es_transitable(mapa_conocido, fila, col):
    # Suposicion OPTIMISTA
    return mapa_conocido[fila][col] in (CAMINO, META, DESCONOCIDO)
 
 
def vecinos(mapa_conocido, fila, col):
    filas, cols = mapa_conocido.shape
    lista = []
    for df, dc in MOVIMIENTOS:
        f = fila + df
        c =  col + dc
        if 0 <= f < filas and 0 <= c < cols and es_transitable(mapa_conocido, f, c):
            lista.append((f, c))
    return lista
 
 
def reconstruir_camino(padres, inicio, meta):
    camino = []
    actual = meta
    while actual != inicio:
        camino.append(actual)
        actual = padres[actual]
    camino.reverse()
    return camino
