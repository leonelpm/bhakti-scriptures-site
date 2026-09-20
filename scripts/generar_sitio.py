#!/usr/bin/env python3
"""Monta la carpeta publicable: una pagina por seccion, hoja de estilo compartida
y un indice que enlaza las secciones y el indice de kirtan por primer verso.
Las secciones que todavia no se han extraido salen en el indice marcadas como
pendientes, no desaparecen."""
import json, os, html, sys
from secciones import SECCIONES, INDICE_KIRTAN, archivo, vecinas
from generar_html import CSS, construir, comprobar

DEST = os.environ.get('DEST', 'sitio')
esc = lambda s: html.escape(s, quote=False)


def cargar(sec):
    ruta = os.path.join(DEST, 'json', sec['slug'] + '.json')
    return json.load(open(ruta)) if os.path.exists(ruta) else None


def pagina_seccion(sec, D):
    ant, sig = vecinas(sec)
    nav = {'indice': 'indice.html'}
    if ant and cargar(ant):
        nav['ant'] = (archivo(ant), esc(ant['rom']))
    if sig and cargar(sig):
        nav['sig'] = (archivo(sig), esc(sig['rom']))
    doc = construir(D, con_buscador=False, con_original=True, css='estilo.css', nav=nav)
    print(' ', archivo(sec))
    ok = comprobar(doc, D)
    open(os.path.join(DEST, archivo(sec)), 'w').write(doc)
    return ok


def ancla_kirtan(fila, hechas):
    """Del numero de pagina impreso al enlace del verso, cuando la seccion existe."""
    for sec, D in hechas:
        if not (sec['p0'] <= fila['pagina'] <= sec['p1']):
            continue
        mejor = None
        for c in D['canciones']:
            pg = c['versos'][0].get('pagina')
            if pg and pg <= fila['pagina'] and (mejor is None or pg > mejor[1]):
                mejor = (c, pg)
        if mejor:
            return f"{archivo(sec)}#c{mejor[0]['n']}", sec
        return archivo(sec), sec
    return None, None


def indice(hechas):
    kir = os.path.join(DEST, 'json', 'kirtan.json')
    filas = json.load(open(kir)) if os.path.exists(kir) else []
    hechos = {s['slug'] for s, _ in hechas}

    secs = []
    for s in SECCIONES:
        n = f'<span class="num">{s["orden"]:02d}</span>'
        etiqueta = '' if s['canciones'] else '<span class="aviso">otro formato</span>'
        if s['slug'] in hechos:
            D = dict(hechas)[s['slug']] if False else cargar(s)
            cuenta = sum(len(c['versos']) for c in D['canciones'])
            secs.append(f'<li><a href="{archivo(s)}">{n}<b>{esc(s["rom"])}</b>'
                        f'<em>{esc(s["es"])}</em>'
                        f'<span class="meta">{len(D["canciones"])} canciones · {cuenta} versos</span></a></li>')
        else:
            secs.append(f'<li class="pend"><span>{n}<b>{esc(s["rom"])}</b>'
                        f'<em>{esc(s["es"])}</em>'
                        f'<span class="meta">pendiente · páginas {s["p0"]} a {s["p1"]} {etiqueta}</span></span></li>')

    ks = []
    for f in filas:
        href, sec = ancla_kirtan(f, hechas)
        if href:
            ks.append(f'<li><a href="{href}">{esc(f["verso"])}</a>'
                      f'<span class="pg">{f["pagina"]}</span></li>')
        else:
            ks.append(f'<li class="pend"><span>{esc(f["verso"])}</span>'
                      f'<span class="pg">{f["pagina"]}</span></li>')

    doc = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>&#346;ara&#7751;&#257;gati</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,500;0,600;1,400&amp;family=Archivo:wght@400;500;600&amp;family=Noto+Serif+Bengali:wght@400;500&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="estilo.css">
</head>
<body class="portada">
<main>
  <div class="head">
    <p class="over">Bhaktivinod &#7788;h&#257;kur &#183; &#346;r&#299; Laghu-chandrik&#257;-bh&#257;&#7779;ya</p>
    <h1>&#346;ara&#7751;&#257;gati</h1>
    <p>Edici&#243;n espa&#241;ola del &#346;r&#299; Chaitanya S&#257;raswat Ma&#7789;h</p>
  </div>

  <h2 class="rot">Secciones</h2>
  <ol class="secs">{''.join(secs)}</ol>

  <h2 class="rot">&#205;ndice de k&#299;rtan</h2>
  <p class="sub">Por primer verso. El n&#250;mero es la p&#225;gina del libro impreso.</p>
  <ul class="kir">{''.join(ks)}</ul>
</main>
</body>
</html>
'''
    open(os.path.join(DEST, 'indice.html'), 'w').write(doc)
    enlazadas = sum(1 for k in ks if 'pend' not in k)
    print(f'  indice.html | {len(hechos)} de {len(SECCIONES)} secciones | '
          f'{enlazadas} de {len(filas)} kīrtans enlazados')


EXTRA = r'''
/* portada */
body.portada main{max-width:44rem;padding-bottom:5rem}
.rot{font-family:var(--sans);font-size:.7rem;letter-spacing:.1em;color:var(--ink3);
  font-weight:600;margin:2.8rem 0 .2rem}
.sub{margin:.1rem 0 1rem;font-size:.86rem;color:var(--ink3)}
.secs{list-style:none;margin:.6rem 0 0;padding:0}
.secs li{border-bottom:1px solid var(--rule)}
.secs a,.secs>li>span{display:grid;grid-template-columns:2.2rem 1fr;gap:.2rem .6rem;
  padding:.85rem .3rem;text-decoration:none;color:var(--ink)}
.secs a:hover{background:var(--surface)}
.secs .num{font-family:var(--sans);font-size:.78rem;color:var(--ink3);
  font-variant-numeric:tabular-nums;grid-row:span 3;padding-top:.22rem}
.secs b{font-weight:500;font-size:1.02rem}
.secs em{font-style:normal;color:var(--ink2);font-size:.9rem}
.secs .meta{font-family:var(--sans);font-size:.72rem;color:var(--ink3)}
.secs .pend>span{color:var(--ink3)}
.secs .pend b{font-weight:400}
.aviso{color:var(--mark)}
.kir{list-style:none;margin:.4rem 0 0;padding:0;font-size:.94rem}
.kir li{display:flex;align-items:baseline;gap:.5rem;padding:.3rem 0;
  border-bottom:1px dotted var(--rule)}
.kir li>*:first-child{flex:1}
.kir a{color:var(--ink);text-decoration:none}
.kir a:hover{color:var(--accent);text-decoration:underline}
.kir .pend>span{color:var(--ink3)}
.kir .pg{font-family:var(--sans);font-size:.75rem;color:var(--ink3);
  font-variant-numeric:tabular-nums}
'''


def main():
    os.makedirs(DEST, exist_ok=True)
    open(os.path.join(DEST, 'estilo.css'), 'w').write(CSS + EXTRA)
    pedidas = sys.argv[1:]
    hechas, todo_ok = [], True
    for s in SECCIONES:
        if pedidas and s['slug'] not in pedidas:
            D = cargar(s)
            if D: hechas.append((s, D))
            continue
        D = cargar(s)
        if D is None:
            continue
        hechas.append((s, D))
    for s, D in hechas:
        todo_ok &= pagina_seccion(s, D)
    indice(hechas)
    print('  estilo.css', round(os.path.getsize(os.path.join(DEST, 'estilo.css')) / 1024, 1), 'KB')
    print('SITIO', 'listo' if todo_ok else 'CON FALLOS')


if __name__ == '__main__':
    main()
