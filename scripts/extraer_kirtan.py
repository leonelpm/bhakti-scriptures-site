#!/usr/bin/env python3
"""Indice de kīrtan por primer verso, de las dos ultimas paginas del PDF."""
import pdfplumber, re, json, os
from secciones import INDICE_KIRTAN

PDF = os.environ.get('SARANAGATI_PDF', 'SARANAGATI.pdf')
LINEA = re.compile(r'^(.+?)[\s.]{4,}(\d{1,3})$')

def extraer(dest='sitio'):
    pdf = pdfplumber.open(PDF)
    filas = []
    for n in range(INDICE_KIRTAN[0], INDICE_KIRTAN[1] + 1):
        for l in (pdf.pages[n - 1].extract_text() or '').split('\n'):
            l = l.strip()
            m = LINEA.match(l)
            if not m:
                continue
            primer = re.sub(r'\s*\.\s*$', '', m.group(1)).strip()
            filas.append({'verso': primer, 'pagina': int(m.group(2))})
    os.makedirs(os.path.join(dest, 'json'), exist_ok=True)
    json.dump(filas, open(os.path.join(dest, 'json', 'kirtan.json'), 'w',
                          encoding='utf-8'), ensure_ascii=False)
    print('INDICE DE KIRTAN', len(filas), 'entradas, paginas',
          min(f['pagina'] for f in filas), 'a', max(f['pagina'] for f in filas))
    return filas

if __name__ == '__main__':
    extraer(os.environ.get('DEST', 'sitio'))
