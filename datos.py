import numpy as np


FUERA = 0          # terreno fuera del camino (aqui se construyen los conejos)
CAMINO = 1         # camino por donde avanzan los enemigos
META = 2           # torre de zanahorias
DESCONOCIDO = -1   # solo existe en el mapa conocido de la IA (niebla de guerra)

# Mapa REAL. Los algoritmos nunca deben leerlo directamente:
# trabajan sobre el mapa conocido que guarda la memoria de la IA.
mapa_P = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
])

ENTRADA = (2,19)   # donde aparecen los enemigos (fila, columna)
META_POS = tuple(int(x) for x in np.argwhere(mapa_P == META)[0])
mapa_P.setflags(write=False)   # el mapa real no se puede modificar por accidente

# Estadisticas por tipo, cambiar numeros aqui = balancear el juego
# ticks_por_paso: cuantos ticks tarda en avanzar una celda (menor = mas rapido)
# vision: radio en celdas que revela alrededor del enemigo

ESTADISTICAS_ENEMIGO = {
    'topo':    {'panza_maxima': 20,  'ticks_por_paso': 2, 'vision': 2, 'costo': 10, 'invisible': True,  'recompensa': 10},
    'mapache': {'panza_maxima': 35,  'ticks_por_paso': 1, 'vision': 1, 'costo': 15, 'invisible': False, 'recompensa': 10},
    'jabali':  {'panza_maxima': 160, 'ticks_por_paso': 3, 'vision': 1, 'costo': 30, 'invisible': False, 'recompensa': 33},
}

RONDA_FINAL = 20

ESTADISTICAS_ENEMIGO['jefe'] = {'panza_maxima': 600, 'ticks_por_paso': 3, 'vision': 3,
                                'costo': 150, 'invisible': False, 'recompensa': 100}

# cooldown: cada cuantos ticks dispara. rellenado: cuanta panza llena cada disparo
# uniq = 1  es la unica torre que puede ver a los topos
ESTADISTICAS_TORRE = {
    'basica':         {'rango': 3, 'cooldown': 3, 'rellenado': 10,  'costo': 10, 'uniq': 0},
    'pesada':         {'rango': 3, 'cooldown': 4, 'rellenado': 60, 'costo': 70, 'uniq': 0},
    'reconocimiento': {'rango': 4.3, 'cooldown': 10, 'rellenado': 8, 'costo': 30, 'uniq': 1},
    'rapida':         {'rango': 3, 'cooldown': 1, 'rellenado': 10, 'costo': 60, 'uniq': 0},
}

# Economia y reglas generales
VIDA_BASE = 7
PRESUPUESTO_JUGADOR_INICIAL = 100
PRESUPUESTO_IA_INICIAL = 60
INGRESO_BASE_IA = 20            # dinero base que recibe la IA al empezar cada ronda nueva
CRECIMIENTO_IA_POR_RONDA = 10   # +se le incrementa esto por cada ronda avanzada 
RECOMPENSA_IA_LLEGADA = 15      # dinero de la IA por cada enemigo que llega a las zanahorias
PRESUPUESTO_IA_MINIMO = 10      # piso para que la IA siempre pueda enviar al menos un topo
BONO_EXPLORACION = 1        # dinero extra de la IA por cada celda nueva descubierta
VENTANA_RONDAS = 7        # cuantas rondas recuerda la IA el peligro
PESO_PELIGRO = 20           # cuanto sube el costo de una celda por cada panza completa rellenada ahi
INTERVALO_SPAWN = 6         # ticks entre un enemigo y el siguiente
LIMITE_TICKS_RONDA = 3000   # seguro contra enemigos atascados
TOPE_BONO_EXPLORACION = 60       # maximo bono de exploracion por ronda
INTERVALO_SPAWN_MIN = 2          # el intervalo de spawn nunca baja de esto
RONDAS_POR_REDUCCION_SPAWN = 4   # cada cuantas rondas baja 1 tick el intervalo
MAX_TORRES = 15 # maximo de torres que puede tener el jugador en el mapa

# Escalado de enemigos y mejoras de torres
ESCALA_PANZA_POR_RONDA = 0.05          # cada ronda la panza de los enemigos sube este porcentaje
MAX_NIVEL_TORRE = 3
MEJORA_RELLENADO = {2: 1.5, 3: 2.0}    # multiplicador del rellenado segun el nivel
MEJORA_COSTO = {2: 0.6, 3: 1.0}


# Comandante de la IA (agente de utilidad + Q-learning entre rondas)
# Cada mezcla es la fraccion del presupuesto de la oleada que intenta gastar en cada tipo
MEZCLAS = {
    'enjambre': {'topo': 0.40, 'mapache': 0.60, 'jabali': 0.00},
    'tanque':   {'topo': 0.15, 'mapache': 0.10, 'jabali': 0.75},
    'mixta':    {'topo': 0.34, 'mapache': 0.33, 'jabali': 0.33},
}
MEZCLA_INICIAL = 'mixta'   # estado de la tabla Q en la ronda 1 (todavia no hay ronda anterior)
PROB_MINIMA = 0.05         # piso de la probabilidad de llegar, para no descartar un tipo por completo
Q_ALFA = 0.5               # cuanto pesa lo nuevo (alto: sigue a un jugador que cambia sus torres)
Q_GAMMA = 0.3              # cuanto pesa la ronda siguiente
Q_EPSILON = 0.2            # probabilidad de probar una mezcla al azar (en la ronda final es 0)
Q_INICIAL = 1.0            # valor inicial optimista de la tabla Q (el premio va de 0 a 1)
TOPE_POR_TIPO = 0.60       # ningun tipo recibe mas de esta fraccion del presupuesto de la oleada
VALOR_LLEGADA = 60         # cuanto esta dispuesta a pagar la IA por que UNA tropa llegue (umbral de compra)

# Dificultades (se eligen desde el juego). 'normal' es el balance de referencia.
# dinero_ia multiplica el presupuesto inicial de la IA y su ingreso por ronda.
# escala_panza: cuanto crece la panza de los enemigos por ronda.
# valor_llegada: cuanto paga la IA por que una tropa llegue (alto = compra mas y mas arriesgado).
DIFICULTADES = {
    'facil':   {'nombre': 'Facil', 'vida_base': 10, 'dinero_ia': 0.80, 'escala_panza': 0.04,
                'valor_llegada': 45, 'ia': 'Cautelosa', 'descripcion': 'Para aprender las torres'},
    'normal':  {'nombre': 'Normal', 'vida_base': VIDA_BASE, 'dinero_ia': 1.00,
                'escala_panza': ESCALA_PANZA_POR_RONDA, 'valor_llegada': VALOR_LLEGADA,
                'ia': 'Equilibrada', 'descripcion': 'El balance de referencia'},
    'dificil': {'nombre': 'Dificil', 'vida_base': 5, 'dinero_ia': 1.35, 'escala_panza': 0.07,
                'valor_llegada': 80, 'ia': 'Agresiva', 'descripcion': 'La IA ataca con todo'},
}
PESO_PROGRESO = 0.5        # premio de Q-learning por una tropa saciada: este peso x lo cerca que llego del nucleo (llegar vale 1)
