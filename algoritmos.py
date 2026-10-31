import time
from collections import deque
 
from datos import CAMINO, META, DESCONOCIDO
 
# Todos los algoritmos de ruta tienen la MISMA firma y devuelven lo mismo:
#     algoritmo(mapa_conocido, inicio, meta, costo_celda) -> ResultadoBusqueda 
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
 
# Una vez que la búsqueda encuentra el objetivo, reconstruye el camino 
# yendo desde la meta hacia atrás, lo invierte y lo devuelve como 
# la lista de pasos que el enemigo debe seguirdef reconstruir_camino(padres, inicio, meta):
    camino = []
    actual = meta
    while actual != inicio:
        camino.append(actual)
        actual = padres[actual]
    camino.reverse()
    return camino

def bfs(mapa_conocido, inicio, meta):
    t0 = time.perf_counter()
    res = ResultadoBusqueda()
 
    frontera = deque([inicio])
    padres = {inicio: None}
    res.generados = 1
    res.frontera_max = 1
    encontrado = False
 
    while frontera:
        actual = frontera.popleft()
        res.expandidos += 1
        if actual == meta:
            encontrado = True
            break
        for vecino in vecinos(mapa_conocido, actual[0], actual[1]):
            if vecino not in padres:
                padres[vecino] = actual
                frontera.append(vecino)
                res.generados += 1
        if len(frontera) > res.frontera_max:
            res.frontera_max = len(frontera)
 
    if encontrado:
        res.camino = reconstruir_camino(padres, inicio, meta)
        res.costo = len(res.camino)
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    return res
