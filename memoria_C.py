import numpy as np
from datos import DESCONOCIDO, VENTANA_RONDAS, PESO_PELIGRO


class MemoriaIA:
    """Lo que sabe la IA. Es compartida por todos los enemigos.

    - mapa_conocido: nunca se olvida (empieza todo en DESCONOCIDO).
    - peligro: para cada (tipo, celda), la fraccion de panza que las torres
      rellenaron ahi (1.0 = una panza llena = un enemigo saciado). Durante una
      ronda se acumula en peligro_actual; la IA se guia por peligro_anterior,
      que suma las ultimas VENTANA_RONDAS rondas.
    """

    def __init__(self, mapa_real):
        filas, cols = mapa_real.shape
        self.mapa_conocido = np.full((filas, cols), DESCONOCIDO)
        self.peligro_anterior = {}   # suma de las ultimas VENTANA_RONDAS rondas
        self.peligro_actual = {}
        self.historial = []          # peligro de cada una de esas rondas

    def revelar(self, mapa_real, fila, col, radio):
        filas, cols = mapa_real.shape
        for f in range(fila - radio, fila + radio + 1):
            for c in range(col - radio, col + radio + 1):
                if 0 <= f < filas and 0 <= c < cols:
                    self.mapa_conocido[f][c] = mapa_real[f][c]

    def celdas_conocidas(self):
        return int(np.count_nonzero(self.mapa_conocido != DESCONOCIDO))

    def registrar_golpe(self, tipo, celda, fraccion):
        # fraccion = rellenado de la torre / panza maxima del enemigo
        clave = (tipo, celda)
        self.peligro_actual[clave] = self.peligro_actual.get(clave, 0) + fraccion

    def costo_celda(self, tipo, celda):
<<<<<<< HEAD
        if tipo == 'jefe':
            tipo = 'jabali'
=======
>>>>>>> 5ff211f74b08821e74b5ff072bc1db55ade26f7f
        # costo base 1 + PESO_PELIGRO por cada panza completa rellenada a ese tipo
        # en esa celda (dentro de las ultimas VENTANA_RONDAS rondas)
        return 1 + PESO_PELIGRO * self.peligro_anterior.get((tipo, celda), 0)

    def terminar_ronda(self):
        self.historial.append(self.peligro_actual)
        self.historial = self.historial[-VENTANA_RONDAS:]
        self.peligro_actual = {}
        self.peligro_anterior = {}
        for ronda in self.historial:
            for clave, n in ronda.items():
<<<<<<< HEAD
                self.peligro_anterior[clave] = self.peligro_anterior.get(clave, 0) + n
=======
                self.peligro_anterior[clave] = self.peligro_anterior.get(clave, 0) + n
>>>>>>> 5ff211f74b08821e74b5ff072bc1db55ade26f7f
