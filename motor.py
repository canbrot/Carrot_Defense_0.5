from collections import deque
from datos import (RONDA_FINAL, mapa_P, FUERA, ENTRADA, META_POS, ESTADISTICAS_ENEMIGO,
                   ESTADISTICAS_TORRE, PRESUPUESTO_JUGADOR_INICIAL,
                   PRESUPUESTO_IA_INICIAL, RECOMPENSA_IA_LLEGADA, PRESUPUESTO_IA_MINIMO,
                   INGRESO_BASE_IA, CRECIMIENTO_IA_POR_RONDA,
                   BONO_EXPLORACION, INTERVALO_SPAWN, LIMITE_TICKS_RONDA, 
                   TOPE_BONO_EXPLORACION, INTERVALO_SPAWN_MIN, RONDAS_POR_REDUCCION_SPAWN, MAX_TORRES, DIFICULTADES, PESO_PROGRESO)
from entidades_struc import Enemigo, Torre
from memoria_C import MemoriaIA
from agente_ia import Comandante
import algoritmos

# Que algoritmo usa cada tipo de enemigo
ALGORITMO_POR_TIPO = {
    'topo': 'bfs_exploracion',
    'mapache': 'a_estrella',
    'jabali': 'dijkstra_pesimista',
    'jefe': 'dijkstra_pesimista'
}


class Juego:
    """Motor del juego. NO usa pygame: la interfaz solo lee su estado y le
    manda ordenes (colocar_torre, iniciar_ronda, paso...). Asi el benchmark
    puede correr rondas sin ventana."""

    def __init__(self, dificultad='normal'):
        self.dificultad = dificultad
        self.ajustes = DIFICULTADES[dificultad]
        self.mapa_real = mapa_P
        self.dist_meta = self._distancias_a_meta()   # pasos por el camino real hasta el nucleo (solo para el premio)
        self.memoria = MemoriaIA(self.mapa_real)
        self.comandante = Comandante(self.ajustes['valor_llegada'])     # decide que tropas manda la IA (ver agente_ia.py)
        self.resultado_por_tipo = {}       # enviados, llegaron y saciados de cada tipo (acumulado)
        self.torres = []
        self.enemigos = []
        self.cola_spawn = []        # [tick_de_aparicion, tipo]
        self.efectos = []           # disparos para dibujar: [f1, c1, f2, c2, vida]
        self.ronda = 1
        self.fase = 'preparacion'   # 'preparacion', 'ronda', 'resumen', 'derrota'
        self.vida_maxima = self.ajustes['vida_base']
        self.vida_base = self.vida_maxima
        self.presupuesto_jugador = PRESUPUESTO_JUGADOR_INICIAL
        self.presupuesto_ia = int(PRESUPUESTO_IA_INICIAL * self.ajustes['dinero_ia'])
        self.tick = 0
        self.stats_ronda = {}
        self.celdas_al_inicio = 0
        self.algoritmo_por_tipo = dict(ALGORITMO_POR_TIPO)
        self.metricas = {}          # metricas acumuladas por algoritmo
        # --- datos para la interfaz de la IA ---
        self.rastros = {}           # rastros[algoritmo][celda] = veces que un enemigo piso la celda (acumulado)
        self.rastros_ronda = {}     # lo mismo pero solo de la ronda actual
        self.ultima_busqueda = {}   # ultima busqueda de cada algoritmo (visitados y camino)
        self.resultado_por_algoritmo = {}   # cuantos enemigos de cada algoritmo llegaron o fueron saciados
        self.historial_rondas = []  # un dict por ronda terminada

    def _distancias_a_meta(self):
        # BFS desde el nucleo sobre el mapa real: cuantos pasos le faltan a cada celda del camino
        dist = {META_POS: 0}
        cola = deque([META_POS])
        while cola:
            actual = cola.popleft()
            for vecino in algoritmos.vecinos(self.mapa_real, actual[0], actual[1], optimista=False):
                if vecino not in dist:
                    dist[vecino] = dist[actual] + 1
                    cola.append(vecino)
        return dist

    def _progreso(self, e):
        # 0 = murio en la entrada, 1 = murio pegado al nucleo
        total = self.dist_meta.get(ENTRADA, 0)
        if total == 0:
            return 0.0
        faltan = self.dist_meta.get((e.fila, e.col), total)
        return max(0.0, min(1.0, 1 - faltan / total))

    # Fase de preparacion (el jugador edita torres SOLO aqui)
    def torre_en(self, fila, col):
        for t in self.torres:
            if t.fila == fila and t.col == col:
                return t
        return None

    def es_construible(self, fila, col):
        filas, cols = self.mapa_real.shape
        if not (0 <= fila < filas and 0 <= col < cols):
            return False
        return self.mapa_real[fila][col] == FUERA and self.torre_en(fila, col) is None

    def colocar_torre(self, tipo, fila, col):
        if self.fase != 'preparacion' or not self.es_construible(fila, col) or len(self.torres) >= MAX_TORRES:
            return False
        costo = ESTADISTICAS_TORRE[tipo]['costo']
        if costo > self.presupuesto_jugador:
            return False
        self.torres.append(Torre(tipo, fila, col))
        self.presupuesto_jugador -= costo
        return True

    def quitar_torre(self, fila, col):
        if self.fase != 'preparacion':
            return False
        torre = self.torre_en(fila, col)
        if torre is None:
            return False
        self.torres.remove(torre)
        self.presupuesto_jugador += torre.costo   # reembolso completo
        return True


    # Rondas

    def mejorar_torre(self, fila, col):
        torre = self.torre_en(fila, col)
        if self.fase != 'preparacion' or torre is None:
            return False
        costo = torre.costo_mejora()
        if costo is None or costo > self.presupuesto_jugador:
            return False
        self.presupuesto_jugador -= costo
        torre.mejorar()
        return True

    def generar_oleada(self):
        self.presupuesto_ia = max(self.presupuesto_ia, PRESUPUESTO_IA_MINIMO)
        final = (self.ronda == RONDA_FINAL)
        caja = self.presupuesto_ia
        intervalo = max(INTERVALO_SPAWN_MIN,
                    INTERVALO_SPAWN - (self.ronda - 1) // RONDAS_POR_REDUCCION_SPAWN)
        # el comandante evalua las rutas, elige la mezcla y decide que compra y cuanto guarda
        evaluacion = self.comandante.evaluar(self.memoria, self.algoritmo_por_tipo)
        mezcla = self.comandante.elegir_mezcla(final)
        tipos, sobrante = self.comandante.componer(caja, evaluacion, mezcla, final)
        tiempo = 1
        for tipo in tipos:
            self.cola_spawn.append([tiempo, tipo])
            tiempo += intervalo
        if final:
            self.cola_spawn.append([tiempo + INTERVALO_SPAWN, 'jefe'])
            sobrante = 0
        self.stats_ronda['gasto_ia'] = caja - sobrante
        self.presupuesto_ia = sobrante

    def iniciar_ronda(self):
        if self.fase != 'preparacion':
            return False
        self.tick = 0
        self.enemigos = []
        self.cola_spawn = []
        self.efectos = []
        self.rastros_ronda = {}
        self.stats_ronda = {'enviados': 0, 'llegaron': 0, 'saciados': 0,
                            'atascados': 0, 'celdas_nuevas': 0, 'dinero_ganado': 0,
                            'progreso_saciados': 0.0}
        self.celdas_al_inicio = self.memoria.celdas_conocidas()
        self.generar_oleada()
        self.stats_ronda['enviados'] = len(self.cola_spawn)
        composicion = {}
        for item in self.cola_spawn:
            composicion[item[1]] = composicion.get(item[1], 0) + 1
        self.stats_ronda['composicion'] = composicion
        self.stats_ronda['por_tipo'] = {}
        for tipo, n in composicion.items():
            self.stats_ronda['por_tipo'][tipo] = {'enviados': n, 'llegaron': 0, 'saciados': 0}
            total = self.resultado_por_tipo.setdefault(tipo, {'enviados': 0, 'llegaron': 0, 'saciados': 0})
            total['enviados'] += n
        self.fase = 'ronda'
        return True

    def siguiente_ronda(self):
        if self.fase != 'resumen':
            return False
        self.ronda += 1
        # presupuesto base de la IA: crece con las rondas (ademas de recompensas y bono)
        ingreso = INGRESO_BASE_IA + CRECIMIENTO_IA_POR_RONDA * (self.ronda - 1)
        self.presupuesto_ia += int(ingreso * self.ajustes['dinero_ia'])
        self.enemigos = []
        self.efectos = []
        self.fase = 'preparacion'
        return True

    def paso(self):
        """Un tick de la simulacion."""
        if self.fase != 'ronda':
            return
        self.tick += 1
        self._aparecer_enemigos()
        for e in self.enemigos:
            if e.estado == 'vivo':
                self._mover(e)
        self._disparar_torres()
        self._limpiar()

        if self.fase != 'ronda':
            return
        if self.tick >= LIMITE_TICKS_RONDA:
            self.stats_ronda['atascados'] += len(self.enemigos) + len(self.cola_spawn)
            self.enemigos = []
            self.cola_spawn = []
        if not self.enemigos and not self.cola_spawn:
            self._terminar_ronda()

    # ----------------------------------------------------------
    # Pasos internos
    # ----------------------------------------------------------
    def _aparecer_enemigos(self):
        pendientes = []
        for item in self.cola_spawn:
            if item[0] <= self.tick:
                e = Enemigo(item[1], ENTRADA[0], ENTRADA[1], self.ronda, self.ajustes['escala_panza'])
                self.memoria.revelar(self.mapa_real, e.fila, e.col, e.vision)
                self.memoria.registrar_pasada(e.tipo, (e.fila, e.col))
                self.enemigos.append(e)
            else:
                pendientes.append(item)
        self.cola_spawn = pendientes

    def _planificar(self, e):
        nombre = self.algoritmo_por_tipo[e.tipo]
        funcion = algoritmos.ALGORITMOS[nombre]
        costo = lambda celda: self.memoria.costo_celda(e.tipo, celda)
        res = funcion(self.memoria.mapa_conocido, (e.fila, e.col), META_POS, costo)
        e.camino_asignado = res.camino
        e.explorando = res.explorando

        m = self.metricas.setdefault(nombre, {'llamadas': 0, 'generados': 0, 'expandidos': 0,
                                              'frontera_max': 0, 'tiempo_ms': 0.0})
        m['llamadas'] += 1
        m['generados'] += res.generados
        m['expandidos'] += res.expandidos
        m['frontera_max'] = max(m['frontera_max'], res.frontera_max)
        m['tiempo_ms'] += res.tiempo_ms

        self.ultima_busqueda[nombre] = {'visitados': res.visitados, 'camino': list(res.camino),
                                        'inicio': (e.fila, e.col), 'tipo': e.tipo,
                                        'ronda': self.ronda, 'explorando': res.explorando}

    def _mover(self, e):
        e.espera -= 1
        if e.espera > 0:
            return
        e.espera = e.ticks_por_paso

        # replanificar si no hay ruta o si alguna celda de la ruta ya se supo que es pared
        conocido = self.memoria.mapa_conocido
        # mientras explora, replanifica en cada paso porque cada paso revela celdas nuevas
        if e.explorando or not e.camino_asignado or any(conocido[c] == FUERA for c in e.camino_asignado):
            self._planificar(e)
            if not e.camino_asignado:
                return

        nueva_f, nueva_c = e.camino_asignado.pop(0)
        if nueva_f < e.fila:
            e.direccion = 'arriba'
        elif nueva_f > e.fila:
            e.direccion = 'abajo'
        elif nueva_c < e.col:
            e.direccion = 'izquierda'
        elif nueva_c > e.col:
            e.direccion = 'derecha'
        e.fila, e.col = nueva_f, nueva_c
        nombre = self.algoritmo_por_tipo[e.tipo]
        for rastro in (self.rastros, self.rastros_ronda):
            celdas = rastro.setdefault(nombre, {})
            celdas[(e.fila, e.col)] = celdas.get((e.fila, e.col), 0) + 1
        self.memoria.revelar(self.mapa_real, e.fila, e.col, e.vision)
        self.memoria.registrar_pasada(e.tipo, (e.fila, e.col))
        if (e.fila, e.col) == META_POS:
            e.estado = 'llego'

    def _disparar_torres(self):
        for t in self.torres:
            if t.espera > 0:
                t.espera -= 1
                continue
            objetivo = None
            mejor = None
            for e in self.enemigos:
                if e.estado != 'vivo' or not t.puede_ver(e) or not t.en_rango(e.fila, e.col):
                    continue
                dist = (t.fila - e.fila) ** 2 + (t.col - e.col) ** 2
                # la torre de reconocimiento prioriza topos; luego, el mas cercano
                prioridad = 0 if (t.uniq == 1 and e.invisible) else 1
                clave = (prioridad, dist)
                if mejor is None or clave < mejor:
                    mejor = clave
                    objetivo = e
            if objetivo is None:
                continue
            objetivo.panza_actual += t.Dmg
            self.memoria.registrar_golpe(objetivo.tipo, (objetivo.fila, objetivo.col),
                                         t.Dmg / objetivo.panza_maxima)
            t.espera = t.cooldown - 1
            self.efectos.append([t.fila, t.col, objetivo.fila, objetivo.col, 3])
            if objetivo.panza_actual >= objetivo.panza_maxima:
                objetivo.estado = 'saciado'
                recompensa = ESTADISTICAS_ENEMIGO[objetivo.tipo]['recompensa']
                self.presupuesto_jugador += recompensa
                self.stats_ronda['dinero_ganado'] += recompensa

    def _limpiar(self):
        for e in self.enemigos:
            if e.estado in ('llego', 'saciado'):
                r = self.resultado_por_algoritmo.setdefault(self.algoritmo_por_tipo[e.tipo],
                                                            {'llegaron': 0, 'saciados': 0})
                campo = 'llegaron' if e.estado == 'llego' else 'saciados'
                r[campo] += 1
                self.stats_ronda['por_tipo'][e.tipo][campo] += 1
                self.resultado_por_tipo[e.tipo][campo] += 1
            if e.estado == 'llego':
                self.vida_base -= 1
                self.presupuesto_ia += RECOMPENSA_IA_LLEGADA
                self.stats_ronda['llegaron'] += 1
            elif e.estado == 'saciado':
                self.stats_ronda['saciados'] += 1
                self.stats_ronda['progreso_saciados'] += self._progreso(e)
        self.enemigos = [e for e in self.enemigos if e.estado == 'vivo']
        self.efectos = [[a, b, c, d, v - 1] for a, b, c, d, v in self.efectos if v > 1]
        if self.vida_base <= 0:
            self.fase = 'derrota'
            self._guardar_historial()

    def _terminar_ronda(self):
        # el comandante aprende: llegar vale 1; una tropa saciada vale PESO_PROGRESO x lo cerca que llego del nucleo
        enviados = self.stats_ronda['enviados']
        puntos = self.stats_ronda['llegaron'] + PESO_PROGRESO * self.stats_ronda['progreso_saciados']
        premio = puntos / enviados if enviados else 0.0
        self.comandante.aprender(self.ronda, premio, self.stats_ronda['composicion'])
        self.memoria.terminar_ronda()
        nuevas = self.memoria.celdas_conocidas() - self.celdas_al_inicio
        self.stats_ronda['celdas_nuevas'] = nuevas
        self.presupuesto_ia += min(nuevas * BONO_EXPLORACION, TOPE_BONO_EXPLORACION)
        self.fase = 'resumen'
        if self.ronda == RONDA_FINAL:
            self.fase = 'victoria'
        self._guardar_historial()

    def _guardar_historial(self):
        datos_ronda = dict(self.stats_ronda)
        datos_ronda['ronda'] = self.ronda
        datos_ronda['presupuesto_ia'] = self.presupuesto_ia
        datos_ronda['presupuesto_jugador'] = self.presupuesto_jugador
        datos_ronda['vida_base'] = self.vida_base
        datos_ronda['celdas_conocidas'] = self.memoria.celdas_conocidas()
        self.historial_rondas.append(datos_ronda)
