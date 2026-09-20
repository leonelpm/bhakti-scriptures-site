#!/usr/bin/env python3
"""Muestra de tres versos en HTML+CSS puro, sin una linea de JavaScript.
Reutiliza el mismo generador que la seccion completa: si cambia una regla alli,
cambia aqui tambien."""
import json, os, copy
from generar_html import construir, comprobar

CANCION = 2      # primera cancion de Dainyatmika
VERSOS = (1, 2, 3)

D = json.load(open('data.json'))
M = copy.deepcopy(D)
M['canciones'] = [c for c in M['canciones'] if c['n'] == CANCION]
M['canciones'][0]['versos'] = [v for v in M['canciones'][0]['versos'] if v['n'] in VERSOS]

doc = construir(
    M,
    con_buscador=False,
    con_original=False,   # sin el recorte impreso: solo el texto de lectura
    nota='Muestra de tres versos. Pagina estatica sin JavaScript: las capas, '
         'el cuerpo de letra y el tema dia y noche son CSS con casillas y :has().')

print('MUESTRA cancion', CANCION, 'versos', VERSOS)
ok = comprobar(doc, M)
assert '<script' not in doc.lower(), 'se ha colado JavaScript en la muestra'
print('  sin <script>: ok')

os.makedirs('/mnt/user-data/outputs', exist_ok=True)
open('/mnt/user-data/outputs/muestra.html', 'w').write(doc)
print('HTML', round(len(doc) / 1e6, 2), 'MB')
