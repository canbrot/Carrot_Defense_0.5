"""
Simulador libre de formaciones (banco de pruebas contra la IA).

Permite colocar cualquier combinacion de hasta MAX_TORRES (15) torretas y
subirlas de nivel sin restriccion de presupuesto, dejar que la IA simule
oleadas de forma continua hasta vencer la formacion y analizar que algoritmo
tuvo mejor desempeno junto con todo el Panel de la IA (TAB).
"""

import time
import pygame

from datos import (
    MAX_TORRES,
    MAX_NIVEL_TORRE,
    RONDA_FINAL,
    mapa_P,
    ESTADISTICAS_TORRE,
    DIFICULTADES,
)
from entidades import Torre
from motor import Juego
import interfaz
import panel_ia

CELDA = interfaz.CELDA
FILAS, COLS = mapa_P.shape
ANCHO_PANEL = 340
ANCHO = COLS * CELDA + ANCHO_PANEL
ALTO = max(FILAS * CELDA, 620)
TICK_MS = interfaz.TICK_MS

VELOCIDADES = [1, 4, 16, 128]
ETIQUETAS_VEL = {1: 'x1', 4: 'x4', 16: 'x16', 128: 'Turbo'}
DIFICULTADES_ORDEN = ['facil', 'normal', 'dificil']
MAX_RONDAS_SEGURIDAD = 100


def texto(pantalla, fuente, s, x, y, color=interfaz.COLOR_TEXTO):
    """Dibuja texto en pantalla."""
    pantalla.blit(fuente.render(s, True, color), (x, y))


def restaurar_formacion(juego, formacion):
    """Carga una lista de (tipo, fila, col, nivel) en `juego` sin costo."""
    juego.torres = []
    for tipo, fila, col, nivel in formacion:
        if juego.es_construible(fila, col) and len(juego.torres) < MAX_TORRES:
            torre = Torre(tipo, fila, col)
            while torre.nivel < nivel and torre.nivel < MAX_NIVEL_TORRE:
                torre.mejorar()
            juego.torres.append(torre)


def ranking_algoritmos(juego):
    """Evalua los algoritmos activos y devuelve una lista ordenada del mejor
    al peor segun enemigos que llegaron a la meta, tasa de exito y velocidad.
    """
    enviados_por_alg = {}
    for tipo, alg in juego.algoritmo_por_tipo.items():
        enviados = juego.resultado_por_tipo.get(tipo, {}).get('enviados', 0)
        enviados_por_alg[alg] = enviados_por_alg.get(alg, 0) + enviados

    ranking = []
    for alg in panel_ia.ALGORITMOS_MOSTRADOS:
        res = juego.resultado_por_algoritmo.get(alg, {})
        met = juego.metricas.get(alg, {})
        llegaron = res.get('llegaron', 0)
        saciados = res.get('saciados', 0)
        enviados = enviados_por_alg.get(alg, llegaron + saciados)
        tasa = (100.0 * llegaron / enviados) if enviados > 0 else 0.0
        llamadas = met.get('llamadas', 0)
        ms_llamada = (met.get('tiempo_ms', 0.0) / llamadas) if llamadas else 0.0
        ranking.append(
            {
                'clave': alg,
                'nombre': panel_ia.NOMBRE_ALGORITMO.get(alg, alg),
                'color': panel_ia.COLOR_ALGORITMO.get(alg, interfaz.COLOR_TEXTO),
                'enviados': enviados,
                'llegaron': llegaron,
                'saciados': saciados,
                'tasa': tasa,
                'ms_llamada': ms_llamada,
            }
        )

    ranking.sort(
        key=lambda r: (r['llegaron'], r['tasa'], -r['ms_llamada']),
        reverse=True,
    )
    return ranking


def rects_ui():
    """Rectangulos de los botones del panel derecho del simulador."""
    x = COLS * CELDA + 14
    ancho = ANCHO_PANEL - 28
    rects = {}

    y = 86
    ancho_t = (ancho - 6) // 2
    for i, tipo in enumerate(ESTADISTICAS_TORRE):
        col = i % 2
        fila = i // 2
        rects['torre_' + tipo] = pygame.Rect(
            x + col * (ancho_t + 6), y + fila * 32, ancho_t, 28
        )

    y += 70
    rects['dificultad'] = pygame.Rect(x, y, ancho_t, 28)
    rects['modo_rondas'] = pygame.Rect(x + ancho_t + 6, y, ancho_t, 28)

    y += 34
    rects['limpiar'] = pygame.Rect(x, y, ancho_t, 28)
    rects['reiniciar'] = pygame.Rect(x + ancho_t + 6, y, ancho_t, 28)

    y += 36
    rects['iniciar'] = pygame.Rect(x, y, ancho, 36)

    y += 42
    rects['velocidad'] = pygame.Rect(x, y, ancho_t, 30)
    rects['panel_ia'] = pygame.Rect(x + ancho_t + 6, y, ancho_t, 30)

    return rects


def dibujar_hover_libre(pantalla, juego, seleccionada, pos_mouse, modo):
    """Muestra la previsualizacion de colocacion o mejora en modo edicion."""
    x, y = pos_mouse
    if x >= COLS * CELDA or modo != 'edicion':
        return
    fila, col = y // CELDA, x // CELDA
    if not (0 <= fila < FILAS and 0 <= col < COLS):
        return
    torre = juego.torre_en(fila, col)
    if torre is not None:
        pygame.draw.rect(
            pantalla, (255, 230, 90), interfaz.rect_celda(fila, col), 2
        )
        pygame.draw.circle(
            pantalla,
            (255, 230, 90),
            interfaz.centro_celda(fila, col),
            int(torre.rango * CELDA),
            1,
        )
        return

    valida = juego.es_construible(fila, col) and len(juego.torres) < MAX_TORRES
    color = (255, 255, 255) if valida else (220, 40, 40)
    pygame.draw.rect(pantalla, color, interfaz.rect_celda(fila, col), 2)
    if valida:
        rango = ESTADISTICAS_TORRE[seleccionada]['rango']
        pygame.draw.circle(
            pantalla,
            (255, 255, 255),
            interfaz.centro_celda(fila, col),
            int(rango * CELDA),
            1,
        )


def dibujar_panel_simulador(
    pantalla,
    fuente,
    fuente_peq,
    fuente_mini,
    juego,
    modo,
    pausado,
    seleccionada,
    velocidad,
    sin_limite,
    ticks_totales,
    tiempo_sim_s,
):
    """Dibuja el panel de control y metricas de la simulacion."""
    x0 = COLS * CELDA
    pygame.draw.rect(pantalla, interfaz.COLOR_PANEL, (x0, 0, ANCHO_PANEL, ALTO))
    x = x0 + 14

    texto(pantalla, fuente, 'Simulador Libre (15 Torretas)', x, 10)
    estado_txt = {
        'edicion': 'Edicion libre',
        'simulando': 'Pausado' if pausado else 'Simulando...',
        'finalizado': 'Simulacion terminada',
    }[modo]
    color_estado = (
        (110, 210, 130)
        if modo == 'simulando' and not pausado
        else (240, 200, 80)
    )
    texto(
        pantalla,
        fuente_peq,
        f'Estado: {estado_txt}  |  Ronda {juego.ronda}',
        x,
        36,
        color_estado,
    )
    texto(
        pantalla,
        fuente_peq,
        f'Torretas: {len(juego.torres)}/{MAX_TORRES}  |  '
        f'Base: {juego.vida_base}/{juego.vida_maxima}',
        x,
        58,
    )

    rects = rects_ui()
    bloqueado = modo != 'edicion'

    for tipo in ESTADISTICAS_TORRE:
        r = rects['torre_' + tipo]
        if bloqueado:
            color_b = (55, 55, 65)
        elif tipo == seleccionada:
            color_b = interfaz.COLOR_BOTON_SEL
        else:
            color_b = interfaz.COLOR_BOTON
        pygame.draw.rect(pantalla, color_b, r)
        pygame.draw.rect(pantalla, interfaz.COLOR_TORRE[tipo], (r.x, r.y, 7, r.height))
        texto(pantalla, fuente_mini, tipo, r.x + 12, r.y + 7)

    # Dificultad y limite de rondas
    r_dif = rects['dificultad']
    pygame.draw.rect(
        pantalla, (55, 55, 65) if bloqueado else interfaz.COLOR_BOTON, r_dif
    )
    texto(
        pantalla,
        fuente_mini,
        f'IA: {juego.ajustes["nombre"]}',
        r_dif.x + 8,
        r_dif.y + 7,
    )

    r_mod = rects['modo_rondas']
    pygame.draw.rect(
        pantalla, (55, 55, 65) if bloqueado else interfaz.COLOR_BOTON, r_mod
    )
    limite_txt = 'Hasta vencer' if sin_limite else f'Max {RONDA_FINAL} rondas'
    texto(pantalla, fuente_mini, limite_txt, r_mod.x + 8, r_mod.y + 7)

    # Limpiar y Reiniciar
    r_lim = rects['limpiar']
    pygame.draw.rect(
        pantalla, (55, 55, 65) if bloqueado else (130, 60, 60), r_lim
    )
    texto(pantalla, fuente_mini, 'Limpiar todo', r_lim.x + 8, r_lim.y + 7)

    r_rei = rects['reiniciar']
    pygame.draw.rect(pantalla, (150, 100, 45), r_rei)
    texto(pantalla, fuente_mini, 'Reiniciar form.', r_rei.x + 8, r_rei.y + 7)

    # Boton principal Iniciar / Pausar / Reanudar
    r_ini = rects['iniciar']
    if modo == 'edicion':
        color_ini, lbl_ini = (50, 155, 85), 'Iniciar simulacion (ESPACIO)'
    elif modo == 'simulando':
        if pausado:
            color_ini, lbl_ini = (50, 155, 85), 'Reanudar (ESPACIO)'
        else:
            color_ini, lbl_ini = (180, 130, 45), 'Pausar (ESPACIO)'
    else:
        color_ini, lbl_ini = (60, 130, 200), 'Reiniciar misma formacion'
    pygame.draw.rect(pantalla, color_ini, r_ini)
    texto(pantalla, fuente_peq, lbl_ini, r_ini.x + 12, r_ini.y + 10)

    # Velocidad y Panel IA
    r_vel = rects['velocidad']
    pygame.draw.rect(pantalla, interfaz.COLOR_BOTON, r_vel)
    texto(
        pantalla,
        fuente_peq,
        f'Vel: {ETIQUETAS_VEL[velocidad]}',
        r_vel.x + 10,
        r_vel.y + 7,
    )

    r_pia = rects['panel_ia']
    pygame.draw.rect(pantalla, (60, 130, 200), r_pia)
    texto(pantalla, fuente_peq, 'Panel IA (TAB)', r_pia.x + 10, r_pia.y + 7)

    # Resumen de tiempos y mejor algoritmo
    y = r_vel.bottom + 14
    pygame.draw.line(pantalla, (80, 80, 95), (x, y), (x + ANCHO_PANEL - 28, y))
    y += 10

    if modo == 'finalizado':
        if juego.vida_base <= 0:
            veredicto = f'IA vencio en {juego.ronda} rondas'
            col_v = (240, 100, 100)
        elif sin_limite and juego.ronda >= MAX_RONDAS_SEGURIDAD:
            veredicto = f'Formacion resistio {juego.ronda} rondas'
            col_v = (100, 220, 130)
        else:
            veredicto = f'Formacion resistio {RONDA_FINAL} rondas'
            col_v = (100, 220, 130)
        texto(pantalla, fuente, veredicto, x, y, col_v)
    else:
        texto(pantalla, fuente_peq, 'Metricas de la simulacion', x, y, (180, 200, 230))
    y += 24

    texto(
        pantalla,
        fuente_mini,
        f'Rondas jugadas: {juego.ronda}  |  Ticks: {ticks_totales}',
        x,
        y,
    )
    y += 18
    texto(
        pantalla,
        fuente_mini,
        f'Tiempo real: {tiempo_sim_s:.2f} s  |  Dinero IA: {juego.presupuesto_ia}',
        x,
        y,
    )
    y += 24

    ranking = ranking_algoritmos(juego)
    tiene_datos = any(r['enviados'] > 0 for r in ranking)
    if tiene_datos:
        mejor = ranking[0]
        texto(
            pantalla,
            fuente_peq,
            f'Mejor algoritmo: {mejor["nombre"]}',
            x,
            y,
            mejor['color'],
        )
        y += 22
        for idx, r in enumerate(ranking, start=1):
            linea = (
                f'{idx}. {r["nombre"]}: {r["llegaron"]}/{r["enviados"]} '
                f'({r["tasa"]:.0f}%) | {r["ms_llamada"]:.2f}ms'
            )
            texto(pantalla, fuente_mini, linea, x, y, r['color'])
            y += 18
    else:
        texto(
            pantalla,
            fuente_mini,
            'Coloca hasta 15 torretas y pulsa Iniciar.',
            x,
            y,
            (170, 170, 185),
        )
        y += 22

    y += 8
    for guia in [
        'Clic izq vacio: poner torreta (gratis)',
        'Clic izq torreta: subir nivel 1-3',
        'Clic der torreta: quitar torreta',
        'F: niebla IA  |  TAB: ver todo Panel IA',
    ]:
        texto(pantalla, fuente_mini, guia, x, y, (160, 160, 175))
        y += 17


def ejecutar():
    """Bucle principal del simulador libre."""
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption('Simulador Libre de Formaciones - Panel IA')
    reloj = pygame.time.Clock()

    fuente = pygame.font.SysFont(None, 26)
    fuente_peq = pygame.font.SysFont(None, 21)
    fuente_mini = pygame.font.SysFont(None, 18)
    sprites = interfaz.cargar_sprites()

    fuentes_ia = panel_ia.crear_fuentes()
    estado_ia = panel_ia.estado_inicial()
    ver_panel = False
    ver_niebla = False

    dif_idx = 1  # 'normal'
    sin_limite = True
    seleccionada = 'basica'
    velocidad = 4
    acumulado = 0.0

    juego = Juego(DIFICULTADES_ORDEN[dif_idx])
    formacion_guardada = []
    modo = 'edicion'  # 'edicion', 'simulando', 'finalizado'
    pausado = False
    ticks_totales = 0
    tiempo_sim_s = 0.0

    def reiniciar_a_edicion():
        nonlocal juego, modo, pausado, ticks_totales, tiempo_sim_s, acumulado
        nonlocal estado_ia
        juego = Juego(DIFICULTADES_ORDEN[dif_idx])
        restaurar_formacion(juego, formacion_guardada)
        estado_ia = panel_ia.estado_inicial()
        modo = 'edicion'
        pausado = False
        ticks_totales = 0
        tiempo_sim_s = 0.0
        acumulado = 0.0

    def iniciar_simulacion():
        nonlocal formacion_guardada, modo, pausado, ticks_totales, tiempo_sim_s
        nonlocal acumulado
        formacion_guardada = [
            (t.tipo, t.fila, t.col, t.nivel) for t in juego.torres
        ]
        ticks_totales = 0
        tiempo_sim_s = 0.0
        acumulado = 0.0
        pausado = False
        modo = 'simulando'
        juego.iniciar_ronda()

    corriendo = True
    while corriendo:
        dt = reloj.tick(60)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                corriendo = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_TAB:
                    ver_panel = not ver_panel
                elif ev.key == pygame.K_ESCAPE:
                    if ver_panel:
                        ver_panel = False
                    else:
                        corriendo = False
                elif ver_panel:
                    panel_ia.manejar_tecla(juego, estado_ia, ev.key)
                elif ev.key == pygame.K_f:
                    ver_niebla = not ver_niebla
                elif ev.key == pygame.K_SPACE:
                    if modo == 'edicion':
                        iniciar_simulacion()
                    elif modo == 'simulando':
                        pausado = not pausado
                    elif modo == 'finalizado':
                        reiniciar_a_edicion()

            elif ev.type == pygame.MOUSEBUTTONDOWN and ver_panel:
                if ev.button == 1:
                    i = panel_ia.pestana_en(ev.pos)
                    if i is not None:
                        estado_ia['pestana'] = i

            elif ev.type == pygame.MOUSEBUTTONDOWN and not ver_panel:
                x, y = ev.pos
                if x < COLS * CELDA and modo == 'edicion':
                    fila, col = y // CELDA, x // CELDA
                    if 0 <= fila < FILAS and 0 <= col < COLS:
                        if ev.button == 1:
                            torre = juego.torre_en(fila, col)
                            if torre is not None:
                                if torre.nivel < MAX_NIVEL_TORRE:
                                    torre.mejorar()
                            elif (
                                juego.es_construible(fila, col)
                                and len(juego.torres) < MAX_TORRES
                            ):
                                juego.torres.append(
                                    Torre(seleccionada, fila, col)
                                )
                        elif ev.button == 3:
                            torre = juego.torre_en(fila, col)
                            if torre is not None:
                                juego.torres.remove(torre)

                elif ev.button == 1 and x >= COLS * CELDA:
                    rects = rects_ui()
                    if modo == 'edicion':
                        for tipo in ESTADISTICAS_TORRE:
                            if rects['torre_' + tipo].collidepoint(ev.pos):
                                seleccionada = tipo
                        if rects['dificultad'].collidepoint(ev.pos):
                            dif_idx = (dif_idx + 1) % len(DIFICULTADES_ORDEN)
                            actuales = [
                                (t.tipo, t.fila, t.col, t.nivel)
                                for t in juego.torres
                            ]
                            juego = Juego(DIFICULTADES_ORDEN[dif_idx])
                            restaurar_formacion(juego, actuales)
                        elif rects['modo_rondas'].collidepoint(ev.pos):
                            sin_limite = not sin_limite
                        elif rects['limpiar'].collidepoint(ev.pos):
                            juego.torres = []
                            formacion_guardada = []

                    if rects['reiniciar'].collidepoint(ev.pos):
                        if modo == 'edicion':
                            formacion_guardada = [
                                (t.tipo, t.fila, t.col, t.nivel)
                                for t in juego.torres
                            ]
                        reiniciar_a_edicion()
                    elif rects['iniciar'].collidepoint(ev.pos):
                        if modo == 'edicion':
                            iniciar_simulacion()
                        elif modo == 'simulando':
                            pausado = not pausado
                        elif modo == 'finalizado':
                            reiniciar_a_edicion()
                    elif rects['velocidad'].collidepoint(ev.pos):
                        idx_v = VELOCIDADES.index(velocidad)
                        velocidad = VELOCIDADES[(idx_v + 1) % len(VELOCIDADES)]
                    elif rects['panel_ia'].collidepoint(ev.pos):
                        ver_panel = True

        # Avance continuo de la simulacion
        if modo == 'simulando' and not pausado:
            tiempo_sim_s += dt / 1000.0
            acumulado += dt * velocidad
            pasos_frame = 0
            max_pasos = 600 if velocidad >= 128 else 64

            while (
                acumulado >= TICK_MS
                and modo == 'simulando'
                and pasos_frame < max_pasos
            ):
                acumulado -= TICK_MS
                pasos_frame += 1

                if juego.fase == 'ronda':
                    juego.paso()
                    ticks_totales += 1

                if juego.fase == 'derrota':
                    modo = 'finalizado'
                elif juego.fase == 'victoria':
                    if sin_limite and juego.ronda < MAX_RONDAS_SEGURIDAD:
                        juego.fase = 'resumen'
                        juego.siguiente_ronda()
                        juego.iniciar_ronda()
                    else:
                        modo = 'finalizado'
                elif juego.fase == 'resumen':
                    if sin_limite and juego.ronda >= MAX_RONDAS_SEGURIDAD:
                        modo = 'finalizado'
                    else:
                        juego.siguiente_ronda()
                        juego.iniciar_ronda()

        # Renderizado
        if ver_panel:
            panel_ia.dibujar_panel_ia(pantalla, juego, estado_ia, fuentes_ia)
        else:
            pantalla.fill(interfaz.COLOR_PANEL)
            interfaz.dibujar_mapa(pantalla, juego, sprites)
            if ver_niebla:
                interfaz.dibujar_vista_ia(pantalla, juego)
            interfaz.dibujar_torres(pantalla, juego, sprites, fuente)
            interfaz.dibujar_enemigos(pantalla, juego, sprites)
            interfaz.dibujar_efectos(pantalla, juego)
            dibujar_hover_libre(
                pantalla, juego, seleccionada, pygame.mouse.get_pos(), modo
            )
            dibujar_panel_simulador(
                pantalla,
                fuente,
                fuente_peq,
                fuente_mini,
                juego,
                modo,
                pausado,
                seleccionada,
                velocidad,
                sin_limite,
                ticks_totales,
                tiempo_sim_s,
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    ejecutar()