#!/usr/bin/env python3
"""Ida y vuelta: transliteración impresa -> bengalí Unicode -> transliteración.
Si alguna línea no coincide tras normalizar, la regla está mal."""
import json
from iast2ben import linea_bengali, bengali_a_iast, normaliza

D = json.load(open('data.json'))
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
print(f'lineas {ok+mal} | coinciden {ok} | difieren {mal}')
