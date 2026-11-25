"""
Panel detallado de la IA (se abre con TAB desde el juego).
Solo LEE el estado del juego (juego.memoria, juego.rastros, juego.metricas...)
y dibuja. No cambia nada de la partida.

Pestanas (de la mas simple a la mas compleja):
    1. Mapa de la IA   -> lo que conoce y donde cree que hay peligro
    2. Rutas           -> por donde camina cada algoritmo
    3. Metricas        -> tablas y graficas de rendimiento
    4. Comandante      -> que tropas manda la IA y que mezcla aprendio
"""
import pygame

from datos import mapa_P, CAMINO, META, DESCONOCIDO, ENTRADA, META_POS, RONDA_FINAL
from agente_ia import NOMBRES_MEZCLA

FILAS, COLS = mapa_P.shape

# ---------------------------------------------------------------
# Colores y nombres
# ---------------------------------------------------------------
FONDO = (28, 28, 36)
PANEL = (40, 40, 52)
BORDE = (80, 80, 100)
BOTON = (70, 70, 85)
ACENTO = (60, 130, 200)
TEXTO = (235, 235, 235)
SUAVE = (160, 160, 175)

COLOR_FUERA = (96, 160, 80)
COLOR_CAMINO = (196, 164, 110)
COLOR_META = (240, 140, 30)
COLOR_DESCONOCIDO = (20, 20, 26)
COLOR_TORRE = {'basica': (240, 240, 240), 'pesada': (120, 120, 210),
               'reconocimiento': (230, 200, 60), 'rapida': (240, 150, 200)}
COLOR_ENEMIGO = {'topo': (150, 100, 60), 'mapache': (170, 170, 180),
                 'jabali': (190, 50, 50), 'jefe': (170, 40, 170)}
COLOR_ALGORITMO = {'bfs_exploracion': (110, 190, 255), 'a_estrella': (255, 190, 80),
                   'dijkstra_pesimista': (120, 220, 140),
                   'q_learning': (200, 120, 255), 'bfs': (170, 170, 170)}
NOMBRE_ALGORITMO = {'bfs_exploracion': 'BFS exploracion', 'a_estrella': 'A*',
                    'dijkstra_pesimista': 'Dijkstra pesimista',
                    'q_learning': 'Q-learning', 'bfs': 'BFS'}

PESTANAS = ['1. Mapa de la IA', '2. Rutas', '3. Metricas', '4. Comandante']
FILTROS = ['todos', 'topo', 'mapache', 'jabali']
ALGORITMOS_MOSTRADOS = ['bfs_exploracion', 'a_estrella', 'dijkstra_pesimista']

AYUDA = [
    'T: cambiar el tipo de enemigo del riesgo  |  1-4 o flechas izq/der: pestanas  |  TAB: volver al juego',
    'R: acumulado / solo esta ronda  |  V: mostrar celdas visitadas  |  1-4 o flechas izq/der: pestanas  |  TAB: volver',
    '1-4 o flechas izq/der: pestanas  |  TAB: volver al juego',
    'Estado = mezcla de la ronda anterior  |  Accion = mezcla de esta ronda  |  1-4 o flechas izq/der: pestanas  |  TAB: volver',
]


def estado_inicial():
    return {'pestana': 0, 'filtro': 0, 'acumulado': True, 'visitados': True}


def crear_fuentes():
    return {'normal': pygame.font.SysFont(None, 26), 'peq': pygame.font.SysFont(None, 21),
            'mini': pygame.font.SysFont(None, 18), 'titulo': pygame.font.SysFont(None, 30)}


# ---------------------------------------------------------------
# Utilidades de dibujo
# ---------------------------------------------------------------
def texto(pantalla, fuente, s, x, y, color=TEXTO):
    pantalla.blit(fuente.render(s, True, color), (x, y))


def formato(v):
    if abs(v) >= 10:
        return f'{v:.0f}'
    if abs(v) >= 1:
        return f'{v:.1f}'
    return f'{v:.2f}'


def color_calor(v):
    # v entre 0 y 1: verde (poco) -> amarillo -> rojo (mucho)
    v = max(0.0, min(1.0, v))
    return (int(255 * min(1.0, 2 * v)), int(255 * min(1.0, 2 * (1 - v))), 40)


def rect_celda_mapa(origen, tam, fila, col):
    return pygame.Rect(origen[0] + col * tam, origen[1] + fila * tam, tam, tam)


def centro_celda_mapa(origen, tam, celda):
    return (origen[0] + celda[1] * tam + tam // 2, origen[1] + celda[0] * tam + tam // 2)


def dibujar_terreno(pantalla, origen, tam, mapa=None):
    # mapa=None: dibuja el mapa real. Si se pasa el mapa conocido, lo desconocido sale oscuro.
    for f in range(FILAS):
        for c in range(COLS):
            valor = mapa_P[f][c] if mapa is None else mapa[f][c]
            if valor == CAMINO:
                color = COLOR_CAMINO
            elif valor == META:
                color = COLOR_META
            elif valor == DESCONOCIDO:
                color = COLOR_DESCONOCIDO
            else:
                color = COLOR_FUERA
            r = rect_celda_mapa(origen, tam, f, c)
            pygame.draw.rect(pantalla, color, r)
            if tam >= 14:
                pygame.draw.rect(pantalla, (30, 30, 30), r, 1)


def pintar_celda(pantalla, origen, tam, celda, color, alfa):
    capa = pygame.Surface((tam, tam), pygame.SRCALPHA)
    capa.fill((color[0], color[1], color[2], alfa))
    pantalla.blit(capa, rect_celda_mapa(origen, tam, celda[0], celda[1]))


def marcar_entrada_meta(pantalla, origen, tam):
    for celda in (ENTRADA, META_POS):
        pygame.draw.circle(pantalla, (255, 255, 255), centro_celda_mapa(origen, tam, celda),
                           max(3, tam // 2 - 2), 2)


def barra_progreso(pantalla, rect, fraccion, color):
    pygame.draw.rect(pantalla, (60, 60, 75), rect)
    ancho = int(rect.width * max(0.0, min(1.0, fraccion)))
    pygame.draw.rect(pantalla, color, (rect.x, rect.y, ancho, rect.height))


def leyenda_calor(pantalla, x, y, ancho, fuentes, texto_izq, texto_der, invertir=False):
    for i in range(ancho):
        v = i / ancho
        pygame.draw.line(pantalla, color_calor(1 - v if invertir else v), (x + i, y), (x + i, y + 10))
    texto(pantalla, fuentes['mini'], texto_izq, x, y + 14, SUAVE)
    t = fuentes['mini'].render(texto_der, True, SUAVE)
    pantalla.blit(t, (x + ancho - t.get_width(), y + 14))


def flecha(pantalla, centro, dx, dy, largo, color):
    # dx, dy = direccion (x = columna, y = fila)
    cx, cy = centro
    punta = (cx + dx * largo, cy + dy * largo)
    cola = (cx - dx * largo, cy - dy * largo)
    pygame.draw.line(pantalla, color, cola, punta, 2)
    px, py = -dy, dx
    base = (punta[0] - dx * largo * 0.7, punta[1] - dy * largo * 0.7)
    pygame.draw.polygon(pantalla, color, [punta,
                                          (base[0] + px * largo * 0.5, base[1] + py * largo * 0.5),
                                          (base[0] - px * largo * 0.5, base[1] - py * largo * 0.5)])


def caja(pantalla, rect):
    pygame.draw.rect(pantalla, PANEL, rect)
    pygame.draw.rect(pantalla, BORDE, rect, 1)


def grafica_lineas(pantalla, rect, titulo, series, fuentes):
    # series: lista de (nombre, valores, color)
    caja(pantalla, rect)
    texto(pantalla, fuentes['peq'], titulo, rect.x + 8, rect.y + 6)
    graf = pygame.Rect(rect.x + 50, rect.y + 30, rect.width - 64, rect.height - 58)
    todos = [v for _, valores, _ in series for v in valores]
    if not todos:
        texto(pantalla, fuentes['mini'], 'Sin datos todavia', graf.x, graf.centery, SUAVE)
        return
    maximo = max(todos)
    minimo = min(todos)
    if maximo == minimo:
        maximo = minimo + 1          # evita dividir por cero
    pygame.draw.line(pantalla, BORDE, graf.bottomleft, graf.bottomright)
    pygame.draw.line(pantalla, BORDE, graf.topleft, graf.bottomleft)
    texto(pantalla, fuentes['mini'], formato(maximo), rect.x + 6, graf.y - 6, SUAVE)
    texto(pantalla, fuentes['mini'], formato(minimo), rect.x + 6, graf.bottom - 10, SUAVE)

    lx = rect.x + 10
    for nombre, valores, color in series:
        n = len(valores)
        paso = max(1, n // 400)          # si hay demasiados puntos se dibujan menos
        puntos = []
        for i in range(0, n, paso):
            x = graf.x + (graf.width * i / (n - 1) if n > 1 else graf.width / 2)
            y = graf.bottom - graf.height * (valores[i] - minimo) / (maximo - minimo)
            puntos.append((x, y))
        if len(puntos) >= 2:
            pygame.draw.lines(pantalla, color, False, puntos, 2)
        if n <= 40:
            for p in puntos:
                pygame.draw.circle(pantalla, color, (int(p[0]), int(p[1])), 3)
        pygame.draw.rect(pantalla, color, (lx, rect.bottom - 18, 9, 9))
        texto(pantalla, fuentes['mini'], nombre, lx + 13, rect.bottom - 21, SUAVE)
        lx += 24 + fuentes['mini'].size(nombre)[0]


def grafica_barras(pantalla, rect, titulo, datos, fuentes):
    # datos: lista de (nombre, valor, color)
    caja(pantalla, rect)
    texto(pantalla, fuentes['peq'], titulo, rect.x + 8, rect.y + 6)
    if not datos or max(v for _, v, _ in datos) <= 0:
        texto(pantalla, fuentes['mini'], 'Sin datos todavia', rect.x + 10, rect.y + 40, SUAVE)
        return
    maximo = max(v for _, v, _ in datos)
    ancho_max = rect.width - 120 - 70
    y = rect.y + 30
    for nombre, valor, color in datos:
        texto(pantalla, fuentes['mini'], nombre, rect.x + 8, y + 3)
        w = int(ancho_max * valor / maximo)
        pygame.draw.rect(pantalla, color, (rect.x + 115, y, max(w, 2), 18))
        texto(pantalla, fuentes['mini'], formato(valor), rect.x + 115 + w + 6, y + 3)
        y += 26


def tabla(pantalla, x, y, columnas, filas, colores, fuentes):
    # columnas: [(titulo, ancho)]; filas: lista de listas de textos; colores: color de la 1a columna
    ancho_total = sum(a for _, a in columnas)
    alto = 28 + 26 * max(len(filas), 1)
    caja(pantalla, pygame.Rect(x, y, ancho_total, alto))
    cx = x
    for titulo, ancho in columnas:
        texto(pantalla, fuentes['mini'], titulo, cx + 8, y + 7, SUAVE)
        cx += ancho
    pygame.draw.line(pantalla, BORDE, (x, y + 26), (x + ancho_total, y + 26))
    fy = y + 32
    for i, fila in enumerate(filas):
        cx = x
        for j, valor in enumerate(fila):
            color = colores[i] if j == 0 else TEXTO
            texto(pantalla, fuentes['peq'], valor, cx + 8, fy, color)
            cx += columnas[j][1]
        fy += 26


def media_movil(valores, ventana):
    resultado = []
    for i in range(len(valores)):
        trozo = valores[max(0, i - ventana + 1):i + 1]
        resultado.append(sum(trozo) / len(trozo))
    return resultado


# ---------------------------------------------------------------
# Pestana 1: mapa de la IA
# ---------------------------------------------------------------
def peligro_por_celda(memoria, tipo):
    # riesgo por celda: fraccion de panza que se le llena, en promedio, a cada enemigo que pasa
    tipos = ['topo', 'mapache', 'jabali'] if tipo == 'todos' else [tipo]
    celdas = set()
    for fuente in (memoria.pasadas_anterior, memoria.pasadas_actual):
        for (t, celda) in fuente:
            if t in tipos:
                celdas.add(celda)
    riesgo = {}
    for celda in celdas:
        valor = max(memoria.riesgo(t, celda) for t in tipos)
        if valor > 0:
            riesgo[celda] = valor
    return riesgo


def pestana_mapa(pantalla, juego, estado, fuentes, area):
    memoria = juego.memoria
    tam = max(6, min((area.width - 340) // COLS, (area.height - 20) // FILAS))
    origen = (area.x + 10, area.y + 10)
    dibujar_terreno(pantalla, origen, tam, memoria.mapa_conocido)

    tipo = FILTROS[estado['filtro']]
    peligro = peligro_por_celda(memoria, tipo)
    for celda, valor in peligro.items():
        pintar_celda(pantalla, origen, tam, celda, color_calor(min(1.0, valor)), 190)

    for t in juego.torres:
        r = rect_celda_mapa(origen, tam, t.fila, t.col).inflate(-tam // 3, -tam // 3)
        pygame.draw.rect(pantalla, COLOR_TORRE[t.tipo], r)
        pygame.draw.rect(pantalla, (0, 0, 0), r, 1)
    for e in juego.enemigos:
        centro = centro_celda_mapa(origen, tam, (e.fila, e.col))
        pygame.draw.circle(pantalla, COLOR_ENEMIGO[e.tipo], centro, max(3, tam // 3))
        pygame.draw.circle(pantalla, (0, 0, 0), centro, max(3, tam // 3), 1)
    marcar_entrada_meta(pantalla, origen, tam)

    # columna de informacion
    x = origen[0] + COLS * tam + 20
    y = area.y + 10
    ancho = area.right - x - 10
    texto(pantalla, fuentes['titulo'], 'Lo que sabe la IA', x, y)
    y += 34
    texto(pantalla, fuentes['peq'], f'Ronda {juego.ronda}  |  fase: {juego.fase}', x, y)
    texto(pantalla, fuentes['peq'], f'Dinero de la IA: {juego.presupuesto_ia}', x, y + 22)
    y += 54
    conocidas = memoria.celdas_conocidas()
    total = FILAS * COLS
    texto(pantalla, fuentes['peq'], f'Mapa conocido: {conocidas} / {total}  ({100 * conocidas // total}%)', x, y)
    barra_progreso(pantalla, pygame.Rect(x, y + 22, ancho, 10), conocidas / total, ACENTO)
    y += 48

    texto(pantalla, fuentes['peq'], f'Riesgo mostrado: {tipo}  (T para cambiar)', x, y)
    texto(pantalla, fuentes['mini'], 'Promedio por enemigo: ventana de rondas + ronda actual', x, y + 20, SUAVE)
    y += 44
    texto(pantalla, fuentes['peq'], f'Celdas con riesgo: {len(peligro)}', x, y)
    y += 24
    texto(pantalla, fuentes['mini'], 'Mas riesgosas (1.0 = la panza se llena ahi):', x, y, SUAVE)
    y += 20
    top = sorted(peligro.items(), key=lambda kv: kv[1], reverse=True)[:5]
    if not top:
        texto(pantalla, fuentes['mini'], 'Todavia no hay riesgo registrado', x, y)
        y += 18
    for celda, valor in top:
        texto(pantalla, fuentes['mini'], f'  fila {celda[0]}, col {celda[1]}:   {valor:.2f}', x, y)
        y += 18
    y += 12

    composicion = juego.stats_ronda.get('composicion')
    if composicion:
        partes = [f'{n} {t}' for t, n in composicion.items()]
        texto(pantalla, fuentes['mini'], 'Ultima oleada: ' + ', '.join(partes), x, y)
        y += 24

    leyenda_calor(pantalla, x, y, ancho, fuentes, 'poco riesgo', 'mucho')
    y += 44
    for linea in ['Zona oscura: la IA aun no la conoce', 'Cuadros: torres  |  Circulos: enemigos',
                  'Anillo blanco: entrada y meta']:
        texto(pantalla, fuentes['mini'], linea, x, y, SUAVE)
        y += 18


# ---------------------------------------------------------------
# Pestana 2: rutas por algoritmo
# ---------------------------------------------------------------
def pestana_rutas(pantalla, juego, estado, fuentes, area):
    ancho_col = (area.width - 40) // 3
    tam = max(4, min(ancho_col // COLS, (area.height - 190) // FILAS))
    rastros = juego.rastros if estado['acumulado'] else juego.rastros_ronda
    modo = 'acumulado' if estado['acumulado'] else 'solo esta ronda'

    for i, nombre in enumerate(ALGORITMOS_MOSTRADOS):
        x = area.x + 10 + i * (ancho_col + 10)
        y = area.y + 10
        color = COLOR_ALGORITMO[nombre]
        texto(pantalla, fuentes['normal'], NOMBRE_ALGORITMO[nombre], x, y, color)
        origen = (x, y + 28)
        dibujar_terreno(pantalla, origen, tam)

        celdas = rastros.get(nombre, {})
        maximo = max(celdas.values()) if celdas else 0
        for celda, veces in celdas.items():
            pintar_celda(pantalla, origen, tam, celda, color_calor(veces / maximo), 200)

        ultima = juego.ultima_busqueda.get(nombre)
        if ultima:
            if estado['visitados']:
                for celda in ultima['visitados']:
                    centro = centro_celda_mapa(origen, tam, celda)
                    pygame.draw.circle(pantalla, color, centro, max(1, tam // 6))
            puntos = [centro_celda_mapa(origen, tam, ultima['inicio'])]
            for celda in ultima['camino']:
                puntos.append(centro_celda_mapa(origen, tam, celda))
            if len(puntos) >= 2:
                pygame.draw.lines(pantalla, (255, 255, 255), False, puntos, 2)
        marcar_entrada_meta(pantalla, origen, tam)

        ty = origen[1] + FILAS * tam + 8
        tipos = [t for t, a in juego.algoritmo_por_tipo.items() if a == nombre]
        resultado = juego.resultado_por_algoritmo.get(nombre, {})
        lineas = [f'Lo usan: {", ".join(tipos) if tipos else "nadie"}']
        if celdas:
            lineas.append(f'Celdas distintas pisadas: {len(celdas)}  ({modo})')
            lineas.append(f'Pasos totales: {sum(celdas.values())}')
        else:
            lineas.append(f'Sin pasos registrados ({modo})')
        if ultima:
            lineas.append(f'Ultima busqueda: {len(ultima["visitados"])} celdas, camino de '
                          f'{len(ultima["camino"])} (ronda {ultima["ronda"]})')
        lineas.append(f'Llegaron: {resultado.get("llegaron", 0)}  |  Saciados: {resultado.get("saciados", 0)}')
        for linea in lineas:
            texto(pantalla, fuentes['mini'], linea, x, ty, TEXTO)
            ty += 18

    leyenda_calor(pantalla, area.x + 10, area.bottom - 34, 220, fuentes, 'poco pisada', 'muy pisada')
    texto(pantalla, fuentes['mini'], 'Linea blanca: ultima ruta planeada  |  Puntos: celdas que la busqueda genero',
          area.x + 250, area.bottom - 32, SUAVE)


# ---------------------------------------------------------------
# Pestana 3: metricas
# ---------------------------------------------------------------
def pestana_metricas(pantalla, juego, estado, fuentes, area):
    nombres = [n for n in ALGORITMOS_MOSTRADOS if n in juego.metricas]
    nombres += [n for n in juego.metricas if n not in nombres]

    columnas = [('Algoritmo', 140), ('Llamadas', 85), ('Generados', 100), ('Expandidos', 105),
                ('Frontera max.', 110), ('Tiempo total (ms)', 135), ('ms / llamada', 100),
                ('Llegaron', 85), ('Saciados', 85)]
    filas = []
    colores = []
    for nombre in nombres:
        m = juego.metricas[nombre]
        promedio = m['tiempo_ms'] / m['llamadas'] if m['llamadas'] else 0
        r = juego.resultado_por_algoritmo.get(nombre, {})
        filas.append([NOMBRE_ALGORITMO.get(nombre, nombre), str(m['llamadas']), str(m['generados']),
                      str(m['expandidos']), str(m['frontera_max']), f'{m["tiempo_ms"]:.1f}',
                      f'{promedio:.2f}', str(r.get('llegaron', 0)), str(r.get('saciados', 0))])
        colores.append(COLOR_ALGORITMO.get(nombre, TEXTO))
    y = area.y + 10
    tabla(pantalla, area.x + 10, y, columnas, filas, colores, fuentes)
    if not filas:
        texto(pantalla, fuentes['peq'], 'Aun no hay busquedas: inicia una ronda.', area.x + 20, y + 32, SUAVE)
    y += 28 + 26 * max(len(filas), 1) + 8
    texto(pantalla, fuentes['mini'], "Dijkstra pesimista: si no conoce ruta a la meta, va a la frontera mas barata "
          "(jabali y jefe comparten esta fila).", area.x + 10, y, SUAVE)

    # barras
    y += 24
    ancho_b = (area.width - 30) // 2
    tiempo = []
    generados = []
    for nombre in nombres[:4]:
        m = juego.metricas[nombre]
        if m['llamadas']:
            color = COLOR_ALGORITMO.get(nombre, TEXTO)
            tiempo.append((NOMBRE_ALGORITMO.get(nombre, nombre), m['tiempo_ms'] / m['llamadas'], color))
            generados.append((NOMBRE_ALGORITMO.get(nombre, nombre), m['generados'] / m['llamadas'], color))
    grafica_barras(pantalla, pygame.Rect(area.x + 10, y, ancho_b, 135), 'Tiempo por llamada (ms)', tiempo, fuentes)
    grafica_barras(pantalla, pygame.Rect(area.x + 20 + ancho_b, y, ancho_b, 135),
                   'Nodos generados por llamada', generados, fuentes)

    # lineas por ronda
    y += 145
    alto = area.bottom - y - 6
    ancho_l = (area.width - 40) // 3
    h = juego.historial_rondas
    graficas = [
        ('Llegaron y saciados por ronda',
         [('llegaron', [r['llegaron'] for r in h], (230, 80, 80)),
          ('saciados', [r['saciados'] for r in h], (80, 200, 100))]),
        ('Dinero por ronda',
         [('IA', [r['presupuesto_ia'] for r in h], (255, 170, 60)),
          ('jugador', [r['presupuesto_jugador'] for r in h], (90, 160, 255))]),
        ('Celdas que conoce la IA',
         [('conocidas', [r['celdas_conocidas'] for r in h], (110, 190, 255))]),
    ]
    for i, (titulo, series) in enumerate(graficas):
        grafica_lineas(pantalla, pygame.Rect(area.x + 10 + i * (ancho_l + 10), y, ancho_l, alto),
                       titulo, series, fuentes)


# ---------------------------------------------------------------
# Pestana 4: comandante
# ---------------------------------------------------------------
def texto_oleada(composicion):
    # {'topo': 3, 'mapache': 2} -> 'T3 M2'
    letras = {'topo': 'T', 'mapache': 'M', 'jabali': 'J', 'jefe': 'JEFE'}
    return ' '.join(letras[t] + str(n) for t, n in composicion.items())


def pestana_comandante(pantalla, juego, estado, fuentes, area):
    c = juego.comandante
    x = area.x + 10
    y = area.y + 10
    texto(pantalla, fuentes['titulo'], 'Comandante de la IA', x, y, ACENTO)
    y += 34

    # ---- agente de utilidad: evaluacion previa de la ultima oleada ----
    texto(pantalla, fuentes['peq'], 'Evaluacion previa (la ruta que elegiria cada tropa)', x, y)
    y += 22
    columnas = [('Tipo', 80), ('Algoritmo', 140), ('Pasos', 50), ('Llegada', 65), ('Riesgo', 60), ('P(llegar)', 75), ('Compra', 70)]
    filas = []
    colores = []
    for tipo in ('topo', 'mapache', 'jabali', 'jefe'):
        nombre = NOMBRE_ALGORITMO.get(juego.algoritmo_por_tipo[tipo], juego.algoritmo_por_tipo[tipo])
        ev = c.evaluacion.get(tipo)
        if ev:
            compra = '-' if tipo == 'jefe' else ('si' if ev['compra'] else 'ahorra')
            filas.append([tipo, nombre, str(ev['largo']), str(ev['eta']), f"{ev['riesgo']:.2f}", f"{ev['prob']:.2f}", compra])
        else:
            filas.append([tipo, nombre, '-', '-', '-', '-', '-'])
        colores.append(COLOR_ENEMIGO[tipo])
    tabla(pantalla, x, y, columnas, filas, colores, fuentes)
    y += 28 + 26 * 4 + 6
    texto(pantalla, fuentes['mini'], f'P(llegar) = 1 - riesgo acumulado  |  se compra un tipo si P x {c.valor_llegada} cubre su costo; si no, ahorra',
          x, y, SUAVE)
    y += 30

    # ---- agente de refuerzo: tabla Q ----
    texto(pantalla, fuentes['peq'], 'Tabla Q: estado (mezcla anterior) x accion (mezcla nueva)', x, y)
    y += 22
    ancho_et = 120
    ancho_c = 130
    caja(pantalla, pygame.Rect(x, y, ancho_et + 3 * ancho_c, 32 + 28 * 3))
    for j, mezcla in enumerate(NOMBRES_MEZCLA):
        texto(pantalla, fuentes['mini'], mezcla, x + ancho_et + j * ancho_c + 8, y + 8, SUAVE)
    for i, s in enumerate(NOMBRES_MEZCLA):
        fy = y + 34 + i * 28
        color_et = ACENTO if s == c.mezcla_anterior else TEXTO
        texto(pantalla, fuentes['peq'], s, x + 8, fy + 2, color_et)
        mejor = max(c.q[s].values())
        for j, a in enumerate(NOMBRES_MEZCLA):
            v = c.q[s][a]
            rect = pygame.Rect(x + ancho_et + j * ancho_c + 4, fy - 3, ancho_c - 8, 24)
            pygame.draw.rect(pantalla, color_calor(1 - min(1.0, max(0.0, v))), rect)
            if v == mejor:
                pygame.draw.rect(pantalla, (255, 255, 255), rect, 2)
            texto(pantalla, fuentes['peq'], f'{v:.2f}', rect.x + 8, rect.y + 4, (20, 20, 20))
    y += 32 + 28 * 3 + 8
    actual = c.mezcla_actual or (c.historial[-1]['mezcla'] if c.historial else '-')
    for linea in [f'alpha {c.alfa}  |  gamma {c.gamma}  |  epsilon {c.epsilon}  (en la ronda {RONDA_FINAL}: 0)',
                  f'Estado actual: {c.mezcla_anterior}  |  mezcla de la ultima oleada: {actual}',
                  'Verde = valor alto  |  Borde blanco = la accion que elegiria sin azar']:
        texto(pantalla, fuentes['mini'], linea, x, y, SUAVE)
        y += 18

    # ---- columna derecha: historial y premio ----
    x2 = x + 555
    ancho2 = area.right - x2 - 10
    y2 = area.y + 10
    texto(pantalla, fuentes['peq'], 'Rondas jugadas por el comandante', x2, y2 + 6)
    y2 += 30
    ultimas = c.historial[-8:]
    columnas = [('Ronda', 50), ('Estado', 80), ('Mezcla', 80), ('Premio', 55), ('Gasto', 55), ('Caja', 55), ('Oleada', ancho2 - 375)]
    filas = []
    for h in ultimas:
        filas.append([str(h['ronda']), h['estado'], h['mezcla'], f"{h['premio']:.2f}", str(h['gasto']), str(h['caja']), texto_oleada(h['composicion'])])
    tabla(pantalla, x2, y2, columnas, filas, [TEXTO] * len(filas), fuentes)
    if not filas:
        texto(pantalla, fuentes['mini'], 'Todavia no hay rondas terminadas.', x2 + 8, y2 + 34, SUAVE)
    y2 += 28 + 26 * max(len(ultimas), 1) + 10

    premios = [h['premio'] for h in c.historial]
    alto = area.bottom - y2 - 6
    grafica_lineas(pantalla, pygame.Rect(x2, y2, ancho2, alto), 'Premio por ronda (llegadas + cercania al nucleo)',
                   [('premio', premios, (110, 190, 255))], fuentes)


# ---------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------
def dibujar_panel_ia(pantalla, juego, estado, fuentes):
    ancho, alto = pantalla.get_size()
    pantalla.fill(FONDO)
    for i, rect in enumerate(rects_pestanas()):
        pygame.draw.rect(pantalla, ACENTO if i == estado['pestana'] else BOTON, rect)
        texto(pantalla, fuentes['peq'], PESTANAS[i], rect.x + 12, rect.y + 9)
    texto(pantalla, fuentes['peq'], 'Panel de la IA', ancho - 140, 15, SUAVE)

    area = pygame.Rect(0, 44, ancho, alto - 44 - 26)
    pestana = estado['pestana']
    if pestana == 0:
        pestana_mapa(pantalla, juego, estado, fuentes, area)
    elif pestana == 1:
        pestana_rutas(pantalla, juego, estado, fuentes, area)
    elif pestana == 2:
        pestana_metricas(pantalla, juego, estado, fuentes, area)
    else:
        pestana_comandante(pantalla, juego, estado, fuentes, area)
    texto(pantalla, fuentes['mini'], AYUDA[pestana], 10, alto - 20, SUAVE)


def rects_pestanas():
    return [pygame.Rect(10 + i * 175, 6, 165, 32) for i in range(len(PESTANAS))]


def pestana_en(pos):
    for i, rect in enumerate(rects_pestanas()):
        if rect.collidepoint(pos):
            return i
    return None


def manejar_tecla(juego, estado, tecla):
    numeros = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
    if tecla in numeros:
        estado['pestana'] = numeros[tecla]
    elif tecla == pygame.K_RIGHT:
        estado['pestana'] = (estado['pestana'] + 1) % len(PESTANAS)
    elif tecla == pygame.K_LEFT:
        estado['pestana'] = (estado['pestana'] - 1) % len(PESTANAS)
    elif tecla == pygame.K_t:
        estado['filtro'] = (estado['filtro'] + 1) % len(FILTROS)
    elif tecla == pygame.K_r:
        estado['acumulado'] = not estado['acumulado']
    elif tecla == pygame.K_v:
        estado['visitados'] = not estado['visitados']
