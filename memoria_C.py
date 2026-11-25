import numpy as np
from datos import DESCONOCIDO, VENTANA_RONDAS, PESO_PELIGRO


class MemoriaIA:
    """Lo que sabe la IA. Es compartida por todos los enemigos.

    - mapa_conocido: nunca se olvida (empieza todo en DESCONOCIDO).
    - peligro: para cada (tipo, celda), la fraccion de panza que las torres
      rellenaron ahi (1.0 = una panza llena). Es una SUMA sobre todos los enemigos.
    - pasadas: para cada (tipo, celda), cuantos enemigos pasaron por ahi.
    - riesgo = peligro / pasadas: la fraccion de panza que se le llena, EN PROMEDIO,
      a un enemigo de ese tipo que pasa por la celda. Asi una ruta muy usada no parece
      peligrosa solo por tener mas trafico.
    Durante una ronda se acumula en *_actual; el riesgo suma las ultimas VENTANA_RONDAS
    rondas (*_anterior) mas lo que va de la ronda actual (asi la IA aprende dentro de la ronda).
    """

    def __init__(self, mapa_real):
        filas, cols = mapa_real.shape
        self.mapa_conocido = np.full((filas, cols), DESCONOCIDO)
        self.peligro_anterior = {}   # suma de las ultimas VENTANA_RONDAS rondas
        self.peligro_actual = {}
        self.pasadas_anterior = {}
        self.pasadas_actual = {}
        self.historial = []          # peligro de cada una de esas rondas
        self.historial_pasadas = []  # pasadas de cada una de esas rondas

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

    def registrar_pasada(self, tipo, celda):
        clave = (tipo, celda)
        self.pasadas_actual[clave] = self.pasadas_actual.get(clave, 0) + 1

    def riesgo(self, tipo, celda):
        if tipo == 'jefe':
            tipo = 'jabali'          # el jefe solo sale una vez: usa lo que la IA sabe del jabali
        clave = (tipo, celda)
        pasadas = self.pasadas_anterior.get(clave, 0) + self.pasadas_actual.get(clave, 0)
        if pasadas == 0:
            return 0.0               # nadie ha pasado por ahi: se asume seguro (la IA es optimista)
        peligro = self.peligro_anterior.get(clave, 0) + self.peligro_actual.get(clave, 0)
        return peligro / pasadas

    def costo_celda(self, tipo, celda):
        # costo base 1 + PESO_PELIGRO por cada panza completa que se le llena en promedio
        return 1 + PESO_PELIGRO * self.riesgo(tipo, celda)

    def terminar_ronda(self):
        self.historial.append(self.peligro_actual)
        self.historial_pasadas.append(self.pasadas_actual)
        self.historial = self.historial[-VENTANA_RONDAS:]
        self.historial_pasadas = self.historial_pasadas[-VENTANA_RONDAS:]
        self.peligro_actual = {}
        self.pasadas_actual = {}
        self.peligro_anterior = self._sumar(self.historial)
        self.pasadas_anterior = self._sumar(self.historial_pasadas)

    def _sumar(self, rondas):
        total = {}
        for ronda in rondas:
            for clave, n in ronda.items():
                total[clave] = total.get(clave, 0) + n
        return total
