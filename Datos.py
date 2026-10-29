import numpy as np

FUERA = 0          
CAMINO = 1        
META = 2          
DESCONOCIDO = -1   


mapa_P = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [2, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
])
mapa_P.setflags(write=False)  

ENTRADA = (3, 10)   
META_POS = tuple(np.argwhere(mapa_P == META)[0])

ESTADISTICAS_ENEMIGO = {
    'topo':    {'panza_maxima': 50,  'ticks_por_paso': 2, 'vision': 2, 'costo': 10, 'invisible': True,  'recompensa': 10},
    'mapache': {'panza_maxima': 30,  'ticks_por_paso': 1, 'vision': 1, 'costo': 15, 'invisible': False, 'recompensa': 8},
    'jabali':  {'panza_maxima': 100, 'ticks_por_paso': 3, 'vision': 1, 'costo': 30, 'invisible': False, 'recompensa': 15},
}

# cooldown: cada cuantos ticks dispara. saciacion: cuanta panza llena cada disparo
# uniq = 1 -> es la unica torre que puede ver a los topos
ESTADISTICAS_TORRE = {
    'basica':         {'rango': 3, 'cooldown': 4, 'rellenado': 6,  'costo': 20, 'uniq': 0},
    'pesada':         {'rango': 2, 'cooldown': 5, 'rellenado': 35, 'costo': 40, 'uniq': 0},
    'reconocimiento': {'rango': 5, 'cooldown': 8, 'saciacion': 15, 'costo': 35, 'uniq': 1},
    'rapida':         {'rango': 3, 'cooldown': 1, 'saciacion': 3,  'costo': 30, 'uniq': 0},
}

VIDA_BASE = 10
PRESUPUESTO_JUGADOR_INICIAL = 100
PRESUPUESTO_IA_INICIAL = 60
INGRESO_IA_RONDA = 20
BONO_EXPLORACION = 1        
INTERVALO_SPAWN = 6         
LIMITE_TICKS_RONDA = 3000   
