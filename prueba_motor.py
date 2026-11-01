"""Corre varias rondas SIN pygame, solo con el motor. Sirve para probar y,
mas adelante, como base del benchmark de algoritmos."""
from motor import Juego

juego = Juego()
juego.colocar_torre('reconocimiento', 4, 5)
juego.colocar_torre('basica', 4, 8)

for _ in range(5):
    juego.iniciar_ronda()
    ticks = 0
    while juego.fase == 'ronda' and ticks < 5000:
        juego.paso()
        ticks += 1
    print('Ronda', juego.ronda, '|', juego.stats_ronda, '| vida base:', juego.vida_base,
          '| celdas conocidas:', juego.memoria.celdas_conocidas())
    if juego.fase == 'derrota':
        print('Derrota')
        break
    juego.siguiente_ronda()

print('Metricas:', juego.metricas)
