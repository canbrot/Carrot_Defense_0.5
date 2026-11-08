import time
from collections import deque
import random
import heapq
from datos import CAMINO, META, DESCONOCIDO

# Todos los algoritmos de ruta tienen la MISMA firma y devuelven lo mismo:
# algoritmo(mapa_conocido, inicio, meta, costo_celda) -> ResultadoBusqueda
# asi comparar metricas (nodos, tiempo, frontera) es trivial.

MOVIMIENTOS = [(-1, 0), (1, 0), (0, -1), (0, 1)]   # 4 vecinos (sin diagonales)


class ResultadoBusqueda:
    def __init__(self):
        self.camino = []          # celdas por recorrer, SIN incluir la de inicio
        self.costo = 0
        self.generados = 0
        self.expandidos = 0
        self.frontera_max = 0
        self.tiempo_ms = 0.0
        self.explorando = False   # True = el camino lleva a una frontera, no a la meta
        self.visitados = []       # celdas que la busqueda genero (para dibujar su patron)


def es_transitable(mapa_conocido, fila, col, optimista=True):
    # optimista=True: lo desconocido se considera transitable.
    # optimista=False: solo se camina por lo que ya se conoce (lo usa la exploracion).
    if optimista:
        return mapa_conocido[fila][col] in (CAMINO, META, DESCONOCIDO)
    return mapa_conocido[fila][col] in (CAMINO, META)


def vecinos(mapa_conocido, fila, col, optimista=True):
    filas, cols = mapa_conocido.shape
    lista = []
    for df, dc in MOVIMIENTOS:
        f, c = fila + df, col + dc
        if 0 <= f < filas and 0 <= c < cols and es_transitable(mapa_conocido, f, c, optimista):
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


# BFS 
def bfs(mapa_conocido, inicio, meta, costo_celda=None):
    # costo_celda se ignora: BFS no usa costos solo cuenta pasos
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
    res.visitados = list(padres)
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    return res


# BFS de EXPLORACION: no sabe cual es el camino mas corto. Solo camina por
# lo conocido y va a la frontera mas cercana la cual es la celda conocida con una vecina
# desconocida hasta que la meta aparece en su mapa; entonces va a la meta.
def es_frontera(mapa_conocido, fila, col):
    filas, cols = mapa_conocido.shape
    for df, dc in MOVIMIENTOS:
        f, c = fila + df, col + dc
        if 0 <= f < filas and 0 <= c < cols and mapa_conocido[f][c] == DESCONOCIDO:
            return True
    return False


def bfs_exploracion(mapa_conocido, inicio, meta, costo_celda=None):
    t0 = time.perf_counter()
    res = ResultadoBusqueda()

    frontera = deque([inicio])
    padres = {inicio: None}
    res.generados = 1
    res.frontera_max = 1
    destino = None
    primera_frontera = None      # la frontera mas cercana, basicamente la primera que sale de la cola

    while frontera:
        actual = frontera.popleft()
        res.expandidos += 1
        if actual == meta:
            destino = actual
            break
        if primera_frontera is None and actual != inicio and es_frontera(mapa_conocido, actual[0], actual[1]):
            primera_frontera = actual
        for vecino in vecinos(mapa_conocido, actual[0], actual[1], optimista=False):
            if vecino not in padres:
                padres[vecino] = actual
                frontera.append(vecino)
                res.generados += 1
        if len(frontera) > res.frontera_max:
            res.frontera_max = len(frontera)

    if destino is None and primera_frontera is not None:
        destino = primera_frontera
        res.explorando = True

    if destino is not None:
        res.camino = reconstruir_camino(padres, inicio, destino)
        res.costo = len(res.camino)
    res.visitados = list(padres)
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    return res



# Heuristicas (para A*)
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidiana(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


# A*  

def a_estrella(mapa_conocido, inicio, meta, costo_celda=None, heuristica=manhattan):
    # Si no se pasa una función de costo por celda, por defecto cada paso cuesta 1
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
        _, actual = heapq.heappop(frontera)
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

    res.visitados = list(g)
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    return res

 
# Q-learning


RECOMPENSA_META = 1000
RECOMPENSA_PARED = -5     # chocar con una pared: se queda en la celda y el episodio sigue


class AgenteQLearning:
    """
    Estado = (fila, col); acciones = 4 movimientos (ej: 0: arriba, 1: abajo, 2: izq, 3: der).
    """
    def __init__(self, alpha=0.3, gamma=0.9, epsilon=0.2):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q = {}    # q[(fila, col)] = [valor_arriba, valor_abajo, valor_izq, valor_der]
        self.historial = []   # un dict por episodio: recompensa, pasos, llego
        self.llamadas = []    # un dict por llamada a q_learning: llegadas, largo, convergio

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

agente = AgenteQLearning(alpha=0.3, gamma=0.99, epsilon=0.2)


def q_learning(mapa_conocido, inicio, meta, costo_celda=None, episodios=200, max_pasos=500):
    if costo_celda is None:
        costo_celda = lambda celda: 1

    t0 = time.perf_counter()
    res = ResultadoBusqueda()
    filas, cols = mapa_conocido.shape
    llegadas = 0

    # --- Entrenamiento ---
    for episodio in range(episodios):
        estado = inicio
        recompensa_total = 0
        pasos = 0
        llego = False
        for paso in range(max_pasos):
            accion = agente.elegir_accion(estado)
            df, dc = MOVIMIENTOS[accion]
            nuevo = (estado[0] + df, estado[1] + dc)
            res.generados += 1
            pasos += 1

            # pared o fuera del mapa
            if not (0 <= nuevo[0] < filas and 0 <= nuevo[1] < cols) \
                    or not es_transitable(mapa_conocido, nuevo[0], nuevo[1]):
                agente.actualizar(estado, accion, RECOMPENSA_PARED, estado)
                recompensa_total += RECOMPENSA_PARED
                continue

            # meta
            if nuevo == meta:
                agente.actualizar(estado, accion, RECOMPENSA_META, nuevo)
                recompensa_total += RECOMPENSA_META
                llego = True
                llegadas += 1
                break

            # paso normal: el costo de la celda (peligro) lo penaliza
            recompensa = -costo_celda(nuevo)
            agente.actualizar(estado, accion, recompensa, nuevo)
            recompensa_total += recompensa
            estado = nuevo

        agente.historial.append({'recompensa': recompensa_total, 'pasos': pasos, 'llego': llego})

    if len(agente.historial) > 3000:
        del agente.historial[:-3000]

    # --- Seguir lo aprendido (sin azar) ---
    camino = []
    estado = inicio
    visitados = {inicio}
    for paso in range(max_pasos):
        if estado == meta:
            break
        agente._asegurar_estado(estado)
        valores = agente.q[estado]
        accion = valores.index(max(valores))
        df, dc = MOVIMIENTOS[accion]
        estado = (estado[0] + df, estado[1] + dc)
        if not (0 <= estado[0] < filas and 0 <= estado[1] < cols) or estado in visitados:
            break
        camino.append(estado)
        visitados.add(estado)

    convergio = (estado == meta)
    agente.llamadas.append({'episodios': episodios, 'llegadas': llegadas,
                            'largo': len(camino) if convergio else 0, 'convergio': convergio})

    if convergio:
        res.camino = camino
        res.costo = len(camino)
        res.visitados = list(visitados)
        res.tiempo_ms = (time.perf_counter() - t0) * 1000
        return res

    # si no aprendio a llegar, que el jefe no se quede quieto
    return a_estrella(mapa_conocido, inicio, meta, costo_celda)


# Diccionario para escoger el algoritmo por nombre
ALGORITMOS = {
    'bfs': bfs,
    'bfs_exploracion': bfs_exploracion,
    'a_estrella': a_estrella,
    'q_learning': q_learning,
}