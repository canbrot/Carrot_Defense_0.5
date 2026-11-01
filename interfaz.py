import os
import pygame

from datos import (mapa_P, FUERA, CAMINO, META, DESCONOCIDO,
                   ESTADISTICAS_TORRE, ESTADISTICAS_ENEMIGO)
from motor import Juego

# ---------------------------------------------------------------
# Configuracion visual
# ---------------------------------------------------------------
CELDA = 48            # tamano en pantalla de cada celda (si usan sprites de 32x32
                      # y quieren pixel perfecto, pongan 32 o 64)
FILAS, COLS = mapa_P.shape
ANCHO_PANEL = 260
ANCHO = COLS * CELDA + ANCHO_PANEL
ALTO = max(FILAS * CELDA, 560)
TICK_MS = 150         # duracion de un tick de simulacion a velocidad x1
CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

COLOR_FUERA = (96, 160, 80)
COLOR_CAMINO = (196, 164, 110)
COLOR_META = (240, 140, 30)
COLOR_PANEL = (40, 40, 48)
COLOR_TEXTO = (235, 235, 235)
COLOR_BOTON = (70, 70, 85)
COLOR_BOTON_SEL = (60, 130, 200)
COLOR_TORRE = {'basica': (240, 240, 240), 'pesada': (120, 120, 210),
               'reconocimiento': (230, 200, 60), 'rapida': (240, 150, 200)}
COLOR_ENEMIGO = {'topo': (110, 70, 40), 'jabali': (140, 30, 30), 'mapache': (130, 130, 140)}


# ---------------------------------------------------------------
# Sprites (si existe el PNG en assets/ se usa; si no, se dibuja una figura simple)
# Nombres esperados: terreno_fuera, terreno_camino, terreno_meta,
# torre_<tipo>, enemigo_<tipo>   (ver assets/LEEME.txt)
# ---------------------------------------------------------------
def cargar_sprite(nombre):
    ruta = os.path.join(CARPETA_ASSETS, nombre + '.png')
    if not os.path.exists(ruta):
        return None
    imagen = pygame.image.load(ruta).convert_alpha()
    return pygame.transform.scale(imagen, (CELDA, CELDA))   # sin suavizado


def cargar_sprites():
    nombres = ['terreno_fuera', 'terreno_camino', 'terreno_meta']
    nombres += ['torre_' + t for t in ESTADISTICAS_TORRE]
    nombres += ['enemigo_' + e for e in ESTADISTICAS_ENEMIGO]
    return {n: cargar_sprite(n) for n in nombres}


# ---------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------
def rect_celda(fila, col):
    # OJO: la matriz es (fila, col) y pygame es (x, y): x = col, y = fila
    return pygame.Rect(col * CELDA, fila * CELDA, CELDA, CELDA)


def centro_celda(fila, col):
    return (col * CELDA + CELDA // 2, fila * CELDA + CELDA // 2)


def texto(pantalla, fuente, s, x, y, color=COLOR_TEXTO):
    pantalla.blit(fuente.render(s, True, color), (x, y))


def rects_panel():
    x = COLS * CELDA + 15
    ancho = ANCHO_PANEL - 30
    rects = {}
    y = 170
    for tipo in ESTADISTICAS_TORRE:
        rects['torre_' + tipo] = pygame.Rect(x, y, ancho, 32)
        y += 38
    rects['accion'] = pygame.Rect(x, y + 8, ancho, 40)
    return rects


def rects_menu():
    cx = ANCHO // 2
    return {'jugar': pygame.Rect(cx - 100, 260, 200, 50),
            'salir': pygame.Rect(cx - 100, 330, 200, 50)}


# ---------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------
def dibujar_mapa(pantalla, juego, sprites):
    for f in range(FILAS):
        for c in range(COLS):
            valor = juego.mapa_real[f][c]
            if valor == CAMINO:
                nombre, color = 'terreno_camino', COLOR_CAMINO
            elif valor == META:
                nombre, color = 'terreno_meta', COLOR_META
            else:
                nombre, color = 'terreno_fuera', COLOR_FUERA
            r = rect_celda(f, c)
            if sprites[nombre]:
                pantalla.blit(sprites[nombre], r)
            else:
                pygame.draw.rect(pantalla, color, r)
                pygame.draw.rect(pantalla, (0, 0, 0), r, 1)


def dibujar_vista_ia(pantalla, juego):
    """Tecla F: oscurece lo que la IA aun no conoce y marca celdas con peligro."""
    velo = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
    velo.fill((0, 0, 0, 170))
    for f in range(FILAS):
        for c in range(COLS):
            if juego.memoria.mapa_conocido[f][c] == DESCONOCIDO:
                pantalla.blit(velo, rect_celda(f, c))
    for peligro in (juego.memoria.peligro_anterior, juego.memoria.peligro_actual):
        for (tipo, celda) in peligro:
            pygame.draw.rect(pantalla, (220, 40, 40), rect_celda(celda[0], celda[1]), 3)


def dibujar_torres(pantalla, juego, sprites, fuente):
    for t in juego.torres:
        r = rect_celda(t.fila, t.col)
        sprite = sprites.get('torre_' + t.tipo)
        if sprite:
            pantalla.blit(sprite, r)
        else:
            pygame.draw.rect(pantalla, COLOR_TORRE[t.tipo], r.inflate(-10, -10))
            pygame.draw.rect(pantalla, (0, 0, 0), r.inflate(-10, -10), 2)
            texto(pantalla, fuente, t.tipo[0].upper(), r.x + 17, r.y + 14, (0, 0, 0))


def dibujar_enemigos(pantalla, juego, sprites):
    for e in juego.enemigos:
        r = rect_celda(e.fila, e.col)
        sprite = sprites.get('enemigo_' + e.tipo)
        if sprite:
            pantalla.blit(sprite, r)
        else:
            pygame.draw.circle(pantalla, COLOR_ENEMIGO[e.tipo], r.center, CELDA // 3)
            pygame.draw.circle(pantalla, (0, 0, 0), r.center, CELDA // 3, 2)
        # barra de panza
        ancho = CELDA - 10
        lleno = int(ancho * min(e.panza_actual / e.panza_maxima, 1))
        pygame.draw.rect(pantalla, (60, 60, 60), (r.x + 5, r.y + 2, ancho, 5))
        pygame.draw.rect(pantalla, (80, 220, 80), (r.x + 5, r.y + 2, lleno, 5))


def dibujar_efectos(pantalla, juego):
    for f1, c1, f2, c2, vida in juego.efectos:
        pygame.draw.line(pantalla, (255, 240, 120), centro_celda(f1, c1), centro_celda(f2, c2), 2)


def dibujar_hover(pantalla, juego, seleccionada, pos_mouse):
    x, y = pos_mouse
    if x >= COLS * CELDA or juego.fase != 'preparacion':
        return
    fila, col = y // CELDA, x // CELDA
    valida = juego.es_construible(fila, col)
    color = (255, 255, 255) if valida else (220, 40, 40)
    pygame.draw.rect(pantalla, color, rect_celda(fila, col), 2)
    if valida:
        rango = ESTADISTICAS_TORRE[seleccionada]['rango']
        pygame.draw.circle(pantalla, (255, 255, 255), centro_celda(fila, col), rango * CELDA, 1)


def dibujar_panel(pantalla, juego, fuente, fuente_peq, seleccionada, velocidad, ver_ia):
    x0 = COLS * CELDA
    pygame.draw.rect(pantalla, COLOR_PANEL, (x0, 0, ANCHO_PANEL, ALTO))
    x = x0 + 15
    texto(pantalla, fuente, 'Ronda ' + str(juego.ronda), x, 12)
    texto(pantalla, fuente, 'Fase: ' + juego.fase, x, 36)
    texto(pantalla, fuente, 'Vida de la base: ' + str(juego.vida_base), x, 60)
    texto(pantalla, fuente, 'Dinero: ' + str(juego.presupuesto_jugador), x, 84)
    if ver_ia:
        texto(pantalla, fuente, 'Dinero IA: ' + str(juego.presupuesto_ia), x, 108)
    texto(pantalla, fuente, 'Torres:', x, 142)

    rects = rects_panel()
    for tipo, stats in ESTADISTICAS_TORRE.items():
        r = rects['torre_' + tipo]
        pygame.draw.rect(pantalla, COLOR_BOTON_SEL if tipo == seleccionada else COLOR_BOTON, r)
        pygame.draw.rect(pantalla, COLOR_TORRE[tipo], (r.x, r.y, 8, r.height))
        texto(pantalla, fuente_peq, tipo + '  ($' + str(stats['costo']) + ')', r.x + 16, r.y + 9)

    etiquetas = {'preparacion': 'Iniciar ronda', 'ronda': 'Velocidad x' + str(velocidad),
                 'resumen': 'Siguiente ronda', 'derrota': 'Reiniciar partida'}
    r = rects['accion']
    pygame.draw.rect(pantalla, (50, 150, 80), r)
    texto(pantalla, fuente, etiquetas[juego.fase], r.x + 12, r.y + 11)

    s = ESTADISTICAS_TORRE[seleccionada]
    y = r.bottom + 14
    texto(pantalla, fuente_peq, 'Rango ' + str(s['rango']) + ' | Cooldown ' + str(s['cooldown']), x, y)
    texto(pantalla, fuente_peq, 'Sacia ' + str(s['saciacion']) + ' | Ve topos: ' +
          ('si' if s['uniq'] else 'no'), x, y + 18)

    y += 50
    for linea in ['Clic izq: colocar torre', 'Clic der: quitar torre',
                  'F: ver lo que sabe la IA', 'ESPACIO: boton principal', 'ESC: menu']:
        texto(pantalla, fuente_peq, linea, x, y, (170, 170, 180))
        y += 18

    if juego.fase in ('resumen', 'derrota') and juego.stats_ronda:
        st = juego.stats_ronda
        y += 8
        texto(pantalla, fuente_peq, 'Llegaron: ' + str(st['llegaron']) + '  Saciados: ' +
              str(st['saciados']), x, y)
        texto(pantalla, fuente_peq, 'Celdas nuevas (IA): ' + str(st['celdas_nuevas']), x, y + 18)


def dibujar_menu(pantalla, fuente, fuente_grande):
    pantalla.fill(COLOR_PANEL)
    titulo = fuente_grande.render('Conejos Guardianes', True, COLOR_TEXTO)
    pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 160))
    rects = rects_menu()
    for clave, etiqueta in (('jugar', 'Jugar'), ('salir', 'Salir')):
        pygame.draw.rect(pantalla, COLOR_BOTON_SEL, rects[clave])
        t = fuente.render(etiqueta, True, COLOR_TEXTO)
        pantalla.blit(t, (rects[clave].centerx - t.get_width() // 2, rects[clave].y + 14))


# ---------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------
def accion_principal(juego, velocidad):
    if juego.fase == 'preparacion':
        juego.iniciar_ronda()
    elif juego.fase == 'ronda':
        velocidad = {1: 2, 2: 4, 4: 1}[velocidad]
    elif juego.fase == 'resumen':
        juego.siguiente_ronda()
    elif juego.fase == 'derrota':
        juego = Juego()
    return juego, velocidad


def ejecutar():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption('Huerto: humano vs maquina')
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 26)
    fuente_peq = pygame.font.SysFont(None, 21)
    fuente_grande = pygame.font.SysFont(None, 64)
    sprites = cargar_sprites()

    juego = Juego()
    estado = 'menu'            # 'menu' o 'juego'
    seleccionada = 'basica'
    ver_ia = False
    velocidad = 1
    acumulado = 0
    corriendo = True

    while corriendo:
        dt = reloj.tick(60)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                corriendo = False

            elif estado == 'menu':
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    rects = rects_menu()
                    if rects['jugar'].collidepoint(ev.pos):
                        estado = 'juego'
                    elif rects['salir'].collidepoint(ev.pos):
                        corriendo = False

            elif estado == 'juego':
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        estado = 'menu'
                    elif ev.key == pygame.K_f:
                        ver_ia = not ver_ia
                    elif ev.key == pygame.K_SPACE:
                        juego, velocidad = accion_principal(juego, velocidad)

                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    x, y = ev.pos
                    if x < COLS * CELDA:                      # clic sobre el tablero
                        fila, col = y // CELDA, x // CELDA
                        if ev.button == 1:
                            juego.colocar_torre(seleccionada, fila, col)
                        elif ev.button == 3:
                            juego.quitar_torre(fila, col)
                    elif ev.button == 1:                      # clic sobre el panel
                        rects = rects_panel()
                        for tipo in ESTADISTICAS_TORRE:
                            if rects['torre_' + tipo].collidepoint(ev.pos):
                                seleccionada = tipo
                        if rects['accion'].collidepoint(ev.pos):
                            juego, velocidad = accion_principal(juego, velocidad)

        # avance de la simulacion (ticks discretos, independientes de los fps)
        if estado == 'juego' and juego.fase == 'ronda':
            acumulado += dt * velocidad
            while acumulado >= TICK_MS and juego.fase == 'ronda':
                acumulado -= TICK_MS
                juego.paso()

        # dibujo
        if estado == 'menu':
            dibujar_menu(pantalla, fuente, fuente_grande)
        else:
            pantalla.fill(COLOR_PANEL)
            dibujar_mapa(pantalla, juego, sprites)
            if ver_ia:
                dibujar_vista_ia(pantalla, juego)
            dibujar_torres(pantalla, juego, sprites, fuente)
            dibujar_enemigos(pantalla, juego, sprites)
            dibujar_efectos(pantalla, juego)
            dibujar_hover(pantalla, juego, seleccionada, pygame.mouse.get_pos())
            dibujar_panel(pantalla, juego, fuente, fuente_peq, seleccionada, velocidad, ver_ia)

        pygame.display.flip()

    pygame.quit()
