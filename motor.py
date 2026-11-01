from datos import (mapa_P, FUERA, ENTRADA, META_POS, ESTADISTICAS_ENEMIGO,
                   ESTADISTICAS_TORRE, VIDA_BASE, PRESUPUESTO_JUGADOR_INICIAL,
                   INGRESO_JUGADOR_RONDA, PRESUPUESTO_IA_INICIAL, INGRESO_IA_RONDA,
                   BONO_EXPLORACION, INTERVALO_SPAWN, LIMITE_TICKS_RONDA)
from entidades_struc import Enemigo, Torre
from memoria_C import MemoriaIA
import algoritmos

# Que algoritmo usa cada tipo de enemigo (cambiar aqui para probar otros)
ALGORITMO_POR_TIPO = {
    'topo': 'bfs',
    'mapache': 'bfs',
    'jabali': 'bfs',
}


class Juego:
    """Motor del juego. NO usa pygame: la interfaz solo lee su estado y le
    manda ordenes (colocar_torre, iniciar_ronda, paso...). Asi el benchmark
    puede correr rondas sin ventana."""

    def __init__(self):
        self.mapa_real = mapa_P
        self.memoria = MemoriaIA(self.mapa_real)
        self.torres = []
        self.enemigos = []
        self.cola_spawn = []        # [tick_de_aparicion, tipo]
        self.efectos = []           # disparos para dibujar: [f1, c1, f2, c2, vida]
        self.ronda = 1
        self.fase = 'preparacion'   # 'preparacion', 'ronda', 'resumen', 'derrota'
        self.vida_base = VIDA_BASE
        self.presupuesto_jugador = PRESUPUESTO_JUGADOR_INICIAL
        self.presupuesto_ia = PRESUPUESTO_IA_INICIAL
        self.tick = 0
        self.stats_ronda = {}
        self.celdas_al_inicio = 0
        self.algoritmo_por_tipo = dict(ALGORITMO_POR_TIPO)
        self.metricas = {}          # metricas acumuladas por algoritmo

    # ----------------------------------------------------------
    # Fase de preparacion (el jugador edita torres SOLO aqui)
    # ----------------------------------------------------------
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
        if self.fase != 'preparacion' or not self.es_construible(fila, col):
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

    # ----------------------------------------------------------
    # Rondas
    # ----------------------------------------------------------
    def generar_oleada(self):
        """Regla simple: la IA gasta todo su presupuesto ciclando tipos.
        (Aqui se puede mejorar luego con una estrategia mas inteligente.)"""
        ciclo = ['topo', 'mapache', 'jabali']
        i = 0
        tiempo = 1
        while True:
            tipo = ciclo[i % 3]
            costo = ESTADISTICAS_ENEMIGO[tipo]['costo']
            if costo > self.presupuesto_ia:
                tipo = 'topo'
                costo = ESTADISTICAS_ENEMIGO['topo']['costo']
                if costo > self.presupuesto_ia:
                    break
            self.presupuesto_ia -= costo
            self.cola_spawn.append([tiempo, tipo])
            tiempo += INTERVALO_SPAWN
            i += 1

    def iniciar_ronda(self):
        if self.fase != 'preparacion':
            return False
        self.tick = 0
        self.enemigos = []
        self.cola_spawn = []
        self.efectos = []
        self.stats_ronda = {'enviados': 0, 'llegaron': 0, 'saciados': 0,
                            'atascados': 0, 'celdas_nuevas': 0}
        self.celdas_al_inicio = self.memoria.celdas_conocidas()
        self.generar_oleada()
        self.stats_ronda['enviados'] = len(self.cola_spawn)
        self.fase = 'ronda'
        return True

    def siguiente_ronda(self):
        if self.fase != 'resumen':
            return False
        self.ronda += 1
        self.presupuesto_jugador += INGRESO_JUGADOR_RONDA
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
                e = Enemigo(item[1], ENTRADA[0], ENTRADA[1])
                self.memoria.revelar(self.mapa_real, e.fila, e.col, e.vision)
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

        m = self.metricas.setdefault(nombre, {'llamadas': 0, 'generados': 0, 'expandidos': 0,
                                              'frontera_max': 0, 'tiempo_ms': 0.0})
        m['llamadas'] += 1
        m['generados'] += res.generados
        m['expandidos'] += res.expandidos
        m['frontera_max'] = max(m['frontera_max'], res.frontera_max)
        m['tiempo_ms'] += res.tiempo_ms

    def _mover(self, e):
        e.espera -= 1
        if e.espera > 0:
            return
        e.espera = e.ticks_por_paso

        # replanificar si no hay ruta o si alguna celda de la ruta ya se supo que es pared
        conocido = self.memoria.mapa_conocido
        if not e.camino_asignado or any(conocido[c] == FUERA for c in e.camino_asignado):
            self._planificar(e)
            if not e.camino_asignado:
                return

        e.fila, e.col = e.camino_asignado.pop(0)
        self.memoria.revelar(self.mapa_real, e.fila, e.col, e.vision)
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
                if mejor is None or dist < mejor:
                    mejor = dist
                    objetivo = e
            if objetivo is None:
                continue
            objetivo.panza_actual += t.Dmg
            t.espera = t.cooldown - 1
            self.efectos.append([t.fila, t.col, objetivo.fila, objetivo.col, 3])
            if objetivo.panza_actual >= objetivo.panza_maxima:
                objetivo.estado = 'saciado'
                self.memoria.registrar_muerte(objetivo.tipo, (objetivo.fila, objetivo.col))

    def _limpiar(self):
        for e in self.enemigos:
            if e.estado == 'llego':
                self.vida_base -= 1
                self.stats_ronda['llegaron'] += 1
            elif e.estado == 'saciado':
                self.stats_ronda['saciados'] += 1
        self.enemigos = [e for e in self.enemigos if e.estado == 'vivo']
        self.efectos = [[a, b, c, d, v - 1] for a, b, c, d, v in self.efectos if v > 1]
        if self.vida_base <= 0:
            self.fase = 'derrota'

    def _terminar_ronda(self):
        self.memoria.terminar_ronda()
        nuevas = self.memoria.celdas_conocidas() - self.celdas_al_inicio
        self.stats_ronda['celdas_nuevas'] = nuevas
        self.presupuesto_ia += INGRESO_IA_RONDA + nuevas * BONO_EXPLORACION
        self.fase = 'resumen'
