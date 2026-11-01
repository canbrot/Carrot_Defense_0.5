import random
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
 
    while len(frontera) > 0:
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
 
    if encontrado == True:
        res.camino = reconstruir_camino(padres, inicio, meta)
        res.costo = len(res.camino)
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    return res


# Heuristicas 
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
 
 
def euclidiana(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
 
 

def a_estrella(mapa_conocido, inicio, meta, costo_celda=None, heuristica=manhattan
    if costo_celda is None:
       costo_celda = lambda celda: 1

    t0 = time.perf_counter()
    res = ResultadoBusqueda()

    # g guarda el costo real acumulado desde el inicio hasta cada nodo
    g = {inicio: 0}
    padres = {inicio: None}

    # f = g + h (costo acumulado + heurística estimada hasta la meta)
    f_inicial = heuristica(inicio, meta)
    
    # Frontera como cola de prioridad (min-heap) usando heapq
    frontera = []
    heapq.heappush(frontera, (f_inicial, inicio))

    res.generados = 1
    res.frontera_max = 1
    encontrado = False

    while frontera:
        # Sacamos el nodo con el menor valor de f
        f_actual, actual = heapq.heappop(frontera)
        res.expandidos += 1

        if actual == meta:
            encontrado = True
            break

        # Recorremos los vecinos válidos
        for vecino in vecinos(mapa_conocido, actual[0], actual[1]):
            nuevo_g = g[actual] + costo_celda(vecino)

            # Si el vecino no ha sido visitado o encontramos un camino con menor costo g
            if vecino not in g or nuevo_g < g[vecino]:
                g[vecino] = nuevo_g
                padres[vecino] = actual
                f_vecino = nuevo_g + heuristica(vecino, meta)
                heapq.heappush(frontera, (f_vecino, vecino))
                res.generados += 1

        # Monitoreamos el tamaño máximo de la frontera
        if len(frontera) > res.frontera_max:
            res.frontera_max = len(frontera)

    if encontrado:
        res.camino = reconstruir_camino(padres, inicio, meta)
        res.costo = g[meta]  # El costo total ponderado del camino encontrado

    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    return res
    raise NotImplementedError('A* por implementar')
 


RECOMPENSA_META = 100
RECOMPENSA_MUERTE = -20
RECOMPENSA_PASO = -1
RECOMPENSA_CELDA_NUEVA = 2

class AgenteQLearning:
    """
    Estado = (fila, col); acciones = 4 movimientos (ej: 0: arriba, 1: abajo, 2: izq, 3: der).
    """
    def __init__(self, alpha=0.3, gamma=0.9, epsilon=0.2):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q = {}    # q[(fila, col)] = [valor_arriba, valor_abajo, valor_izq, valor_der]

    def _asegurar_estado(self, estado):
        """Inicializa la celda en la tabla Q si es la primera vez que el agente la visita."""
        if estado not in self.q:
            # Inicializamos con pequeños valores en 0 para las 4 direcciones
            self.q[estado] = [0.0, 0.0, 0.0, 0.0]

    def elegir_accion(self, estado):
        """Selecciona una acción usando la política Epsilon-Greedy."""
        self._asegurar_estado(estado)
        
        # Exploración: Con probabilidad epsilon, toma una acción al azar
        if random.random() < self.epsilon:
            return random.randint(0, 3)
        
        # Explotación: Elige la acción con el mayor valor Q en la celda actual
        valores_acciones = self.q[estado]
        max_valor = max(valores_acciones)
        
        # Si hubiera empates, seleccionamos al azar entre los mejores
mejores_acciones = [i for i, val in enumerate(valores_acciones) if val == max_valor]
        return random.choice(mejores_acciones)

    def actualizar(self, estado, accion, recompensa, estado_nuevo):
        """Actualiza la tabla Q usando la fórmula clásica de Q-Learning."""
        self._asegurar_estado(estado)
        self._asegurar_estado(estado_nuevo)
        
        # Q-Learning: Aprende considerando la mejor acción futura posible (max)
        mejor_futuro = max(self.q[estado_nuevo])
        valor_actual = self.q[estado][accion]
        
        # Fórmula de actualización de Q-Learning
        self.q[estado][accion] += self.alpha * (
            recompensa + (self.gamma * mejor_futuro) - valor_actual
        )

ALGORITMOS = {
    'bfs': bfs,
    'a_estrella': a_estrella,
}

