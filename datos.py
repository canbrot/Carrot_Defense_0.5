import numpy as np


FUERA = 0          # terreno fuera del camino (aqui se construyen los conejos)
CAMINO = 1         # camino por donde avanzan los enemigos
META = 2           # torre de zanahorias
DESCONOCIDO = -1   # solo existe en el mapa conocido de la IA (niebla de guerra)

# Mapa REAL. Los algoritmos nunca deben leerlo directamente:
# trabajan sobre el mapa conocido que guarda la memoria de la IA.
mapa_P = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
])
ENTRADA = (1,19)   # donde aparecen los enemigos (fila, columna)
META_POS = tuple(int(x) for x in np.argwhere(mapa_P == META)[0])
mapa_P.setflags(write=False)   # el mapa real no se puede modificar por accidente

# Estadisticas por tipo, cambiar numeros aqui = balancear el juego
# ticks_por_paso: cuantos ticks tarda en avanzar una celda (menor = mas rapido)
# vision: radio en celdas que revela alrededor del enemigo

ESTADISTICAS_ENEMIGO = {
    'topo':    {'panza_maxima': 20,  'ticks_por_paso': 2, 'vision': 2, 'costo': 10, 'invisible': True,  'recompensa': 8},
    'mapache': {'panza_maxima': 35,  'ticks_por_paso': 1, 'vision': 1, 'costo': 15, 'invisible': False, 'recompensa': 10},
    'jabali':  {'panza_maxima': 160, 'ticks_por_paso': 3, 'vision': 1, 'costo': 30, 'invisible': False, 'recompensa': 20},
}

<<<<<<< HEAD
RONDA_FINAL = 20
=======
RONDA_FINAL = 35
>>>>>>> 5ff211f74b08821e74b5ff072bc1db55ade26f7f

ESTADISTICAS_ENEMIGO['jefe'] = {'panza_maxima': 600, 'ticks_por_paso': 3, 'vision': 3,
                                'costo': 150, 'invisible': False, 'recompensa': 100}

# cooldown: cada cuantos ticks dispara. rellenado: cuanta panza llena cada disparo
# uniq = 1  es la unica torre que puede ver a los topos
ESTADISTICAS_TORRE = {
    'basica':         {'rango': 3, 'cooldown': 4, 'rellenado': 10,  'costo': 20, 'uniq': 0},
    'pesada':         {'rango': 3, 'cooldown': 4, 'rellenado': 45, 'costo': 40, 'uniq': 0},
    'reconocimiento': {'rango': 5, 'cooldown': 8, 'rellenado': 10, 'costo': 30, 'uniq': 1},
    'rapida':         {'rango': 3, 'cooldown': 1, 'rellenado': 8,  'costo': 30, 'uniq': 0},
}

# Economia y reglas generales
VIDA_BASE = 5
PRESUPUESTO_JUGADOR_INICIAL = 100
PRESUPUESTO_IA_INICIAL = 60
INGRESO_BASE_IA = 20            # dinero base que recibe la IA al empezar cada ronda nueva
CRECIMIENTO_IA_POR_RONDA = 10   # +se le incrementa esto por cada ronda avanzada 
RECOMPENSA_IA_LLEGADA = 15      # dinero de la IA por cada enemigo que llega a las zanahorias
PRESUPUESTO_IA_MINIMO = 10      # piso para que la IA siempre pueda enviar al menos un topo
BONO_EXPLORACION = 1        # dinero extra de la IA por cada celda nueva descubierta
VENTANA_RONDAS = 5        # cuantas rondas recuerda la IA el peligro
PESO_PELIGRO = 20           # cuanto sube el costo de una celda por cada panza completa rellenada ahi
INTERVALO_SPAWN = 6         # ticks entre un enemigo y el siguiente
LIMITE_TICKS_RONDA = 3000   # seguro contra enemigos atascados
FRACCION_GASTO_IA = 0.6          # fraccion del presupuesto que la IA gasta por ronda
TOPE_BONO_EXPLORACION = 60       # maximo bono de exploracion por ronda
INTERVALO_SPAWN_MIN = 2          # el intervalo de spawn nunca baja de esto
RONDAS_POR_REDUCCION_SPAWN = 4   # cada cuantas rondas baja 1 tick el intervalo
<<<<<<< HEAD
MAX_TORRES = 10 # maximo de torres que puede tener el jugador en el mapa
=======
MAX_TORRES = 10 # maximo de torres que puede tener el jugador en el mapa
>>>>>>> 5ff211f74b08821e74b5ff072bc1db55ade26f7f
