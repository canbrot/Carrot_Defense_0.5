from datos import ESTADISTICAS_ENEMIGO, ESTADISTICAS_TORRE


class Enemigo:
    def __init__(self, tipo, fila_inicio, col_inicio):
        stats = ESTADISTICAS_ENEMIGO[tipo]
        self.tipo = tipo
        self.fila = fila_inicio
        self.col = col_inicio
        self.panza_actual = 0
        self.panza_maxima = stats['panza_maxima']
        self.ticks_por_paso = stats['ticks_por_paso']
        self.vision = stats['vision']
        self.invisible = stats['invisible']
        self.espera = self.ticks_por_paso     # cuenta regresiva para el siguiente paso
        self.estado = 'vivo'                  # 'vivo', 'saciado' o 'llego'
        self.camino_asignado = []             # celdas que le faltan por recorrer


class Torre:
    def __init__(self, tipo, fila, col):
        stats = ESTADISTICAS_TORRE[tipo]
        self.tipo = tipo
        self.fila = fila
        self.col = col
        self.rango = stats['rango']
        self.cooldown = stats['cooldown']      # antes vel_atk
        self.Dmg = stats['saciacion']          # cuanta panza llena cada disparo
        self.costo = stats['costo']
        self.uniq = stats['uniq']              # 1 = puede ver a los topos
        self.espera = 0                        # cuenta regresiva para disparar

    def en_rango(self, fila, col):
        return (self.fila - fila) ** 2 + (self.col - col) ** 2 <= self.rango ** 2

    def puede_ver(self, enemigo):
        return (not enemigo.invisible) or self.uniq == 1
