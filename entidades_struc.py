from datos import ESTADISTICAS_ENEMIGO, ESTADISTICAS_TORRE
"""
Aqui esta presente la estructura basica de los objetos que manejaremos, cada una importa desde el archivo de datos la informacion de objeto presento en sus estructuras para facilitar la modificacion de estos
sin correr el riesgo de dañar algo por accidente, estan guardados en diccionarios con nombre claros de como se interpreta cada valor

* el calculo de las distancias se hace a traves de la formula euclidiana pero en teminos de potencias ya que es mas barato computacionalmente
ademas tambien se revisa si una torre puede o no atacar un enemigo en caso de que este sea "invisible"
"""

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
        self.recompensa = stats['recompensa']
        self.espera = self.ticks_por_paso    
        self.estado = 'vivo'                  
        self.camino_asignado = []            


class Torre:
    def __init__(self, tipo, fila, col):
        stats = ESTADISTICAS_TORRE[tipo]
        self.tipo = tipo
        self.fila = fila
        self.col = col
        self.rango = stats['rango']
        self.cooldown = stats['cooldown']     
        self.Dmg = stats['rellenado']          
        self.costo = stats['costo']
        self.uniq = stats['uniq']             
        self.espera = 0

    def en_rango(self, fila, col):
        return (self.fila - fila) ** 2 + (self.col - col) ** 2 <= self.rango ** 2

    def puede_ver(self, enemigo):
        return (not enemigo.invisible) or self.uniq == 1
