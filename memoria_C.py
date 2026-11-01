import numpy as np
from datos import DESCONOCIDO


class MemoriaIA:
    """Lo que sabe la IA. Es compartida por todos los enemigos.

    - mapa_conocido: nunca se olvida (empieza todo en DESCONOCIDO).
    - peligro: cuentas de muertes por (tipo, celda). Se reinicia cada ronda:
      durante una ronda se acumula en peligro_actual y la IA se guia por
      peligro_anterior (lo que aprendio en la ultima ronda).
    """

    def __init__(self, mapa_real):
        filas, cols = mapa_real.shape
        self.mapa_conocido = np.full((filas, cols), DESCONOCIDO)
        self.peligro_anterior = {}
        self.peligro_actual = {}

    def revelar(self, mapa_real, fila, col, radio):
        filas, cols = mapa_real.shape
        for f in range(fila - radio, fila + radio + 1):
            for c in range(col - radio, col + radio + 1):
                if 0 <= f < filas and 0 <= c < cols:
                    self.mapa_conocido[f][c] = mapa_real[f][c]

    def celdas_conocidas(self):
        return int(np.count_nonzero(self.mapa_conocido != DESCONOCIDO))

    def registrar_muerte(self, tipo, celda):
        clave = (tipo, celda)
        self.peligro_actual[clave] = self.peligro_actual.get(clave, 0) + 1

    def costo_celda(self, tipo, celda):
        # costo base 1 + muertes de ese tipo en esa celda en la ronda anterior
        return 1 + self.peligro_anterior.get((tipo, celda), 0)

    def terminar_ronda(self):
        self.peligro_anterior = self.peligro_actual
        self.peligro_actual = {}
