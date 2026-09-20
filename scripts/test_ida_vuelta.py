#!/usr/bin/env python3
"""Ida y vuelta: transliteración impresa -> bengalí Unicode -> transliteración.
Si alguna línea no coincide tras normalizar, la regla está mal.
Sin argumentos recorre todas las secciones extraídas; con argumentos, solo esas."""
import json, os, sys
from secciones import SECCIONES
from iast2ben import linea_bengali, bengali_a_iast, normaliza

DEST = os.environ.get('DEST', 'sitio')


def revisar(slug):
    ruta = os.path.join(DEST, 'json', slug + '.json')
    if not os.path.exists(ruta):
        return None
    D = json.load(open(ruta, encoding='utf-8'))
    ok = mal = 0
    for c in D['canciones']:
        for v in c['versos']:
            for i, (segs, leg) in enumerate(zip(v['tr'], v['legacy'])):
                ben = linea_bengali(segs, leg)
                a = normaliza(' '.join(segs))
                b = normaliza(' '.join(bengali_a_iast(p) for p in ben))
                if a == b:
                    ok += 1
                else:
                    mal += 1
                    print(f"  DIFERENCIA canción {c['n']} verso {v['n']} línea {i+1}")
                    print('   impreso :', a)
                    print('   vuelta  :', b)
    print(f'{slug:24s} lineas {ok+mal:4d} | coinciden {ok:4d} | difieren {mal:4d}')
    return mal


def main():
    pedidas = sys.argv[1:] or [s['slug'] for s in SECCIONES]
    total = mal = 0
    vistas = 0
    for slug in pedidas:
        r = revisar(slug)
        if r is None:
            continue
        vistas += 1
        mal += r
    if not vistas:
        print('no hay ninguna sección extraída en', os.path.join(DEST, 'json'))
        return 1
    print('IDA Y VUELTA', 'superada' if mal == 0 else f'FALLIDA ({mal} líneas)')
    return 0 if mal == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
