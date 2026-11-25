from datos import (ESTADISTICAS_ENEMIGO, ESTADISTICAS_TORRE, ESCALA_PANZA_POR_RONDA,
                   MAX_NIVEL_TORRE, MEJORA_RELLENADO, MEJORA_COSTO)
"""
Aqui esta presente la estructura basica de los objetos que manejaremos, cada una importa desde el archivo de datos la informacion de objeto presento en sus estructuras para facilitar la modificacion de estos
sin correr el riesgo de dañar algo por accidente, estan guardados en diccionarios con nombre claros de como se interpreta cada valor

* el calculo de las distancias se hace a traves de la formula euclidiana pero en teminos de potencias ya que es mas barato computacionalmente
ademas tambien se revisa si una torre puede o no atacar un enemigo en caso de que este sea "invisible"
"""

class Enemigo:
    def __init__(self, tipo, fila_inicio, col_inicio, ronda=1, escala=ESCALA_PANZA_POR_RONDA):
        stats = ESTADISTICAS_ENEMIGO[tipo]
        self.tipo = tipo
        self.fila = fila_inicio
        self.col = col_inicio
        self.panza_actual = 0
        # la panza crece un poco cada ronda (los enemigos escalan con el tiempo)
        self.panza_maxima = int(stats['panza_maxima'] * (1 + escala * (ronda - 1)))
        self.ticks_por_paso = stats['ticks_por_paso']
        self.vision = stats['vision']
        self.invisible = stats['invisible']
        self.espera = self.ticks_por_paso     # cuenta regresiva para el siguiente paso
        self.estado = 'vivo'                  # 'vivo', 'saciado' o 'llego'
        self.camino_asignado = []             # celdas que le faltan por recorrer
        self.explorando = False               # True = su camino lleva a una frontera, hay que replanificar
        self.direccion = 'abajo'              # hacia donde mira (para el sprite)


class Torre:
    def __init__(self, tipo, fila, col):
        stats = ESTADISTICAS_TORRE[tipo]
        self.tipo = tipo
        self.fila = fila
        self.col = col
        self.rango = stats['rango']
        self.cooldown = stats['cooldown']      # antes vel_atk
        self.Dmg = stats['rellenado']          # cuanta panza llena cada disparo
        self.costo = stats['costo']
        self.uniq = stats['uniq']              # 1 = puede ver a los topos
        self.espera = 0                        # cuenta regresiva para disparar
        self.nivel = 1                         # sube con mejorar()

    def en_rango(self, fila, col):
        return (self.fila - fila) ** 2 + (self.col - col) ** 2 <= self.rango ** 2

    def puede_ver(self, enemigo):
        return (not enemigo.invisible) or self.uniq == 1
    def costo_mejora(self):
        # costo de subir al siguiente nivel; None si ya esta al maximo
        if self.nivel >= MAX_NIVEL_TORRE:
            return None
        return int(self.costo * MEJORA_COSTO[self.nivel + 1])

    def mejorar(self):
        self.nivel += 1
        self.Dmg = int(ESTADISTICAS_TORRE[self.tipo]['rellenado'] * MEJORA_RELLENADO[self.nivel])
