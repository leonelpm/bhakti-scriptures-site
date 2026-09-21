#!/usr/bin/env python3
"""Verifica el HTML ya generado, no el que creemos haber generado.

Tres pasadas:
  1. DOM    cada verso del JSON contra su <article> en la pagina: lineas
            bengalies, recortes, lineas de transliteracion, traduccion,
            entradas del glosario y piezas del comentario. Una vez se publico
            una version en blanco por un campo vacio que nadie conto.
  2. HOJA   las reglas que la interfaz da por sentadas: que no han vuelto los
            filetes del cuerpo, que Configuracion es pegajosa, que el indice
            lateral esta fuera del flujo.
  3. ANCHOS el indice lateral es fijo y la columna va centrada en la pantalla:
            a mano se comprueba que en ninguna anchura se monta sobre el texto.

    python3 verificar.py              todas las secciones extraidas
    python3 verificar.py dainyatmika  solo una
"""
import json, os, re, sys, hashlib
from bs4 import BeautifulSoup
from secciones import SECCIONES, archivo

DEST = os.environ.get('DEST', 'sitio')
REM = 16.0          # rem = tamano de raiz; --fs solo toca a body, no a html


def version_hoja():
    """La huella que deberia llevar el enlace a la hoja."""
    ruta = os.path.join(DEST, 'estilo.css')
    if not os.path.exists(ruta):
        return None
    return hashlib.sha1(open(ruta, 'rb').read()).hexdigest()[:10]


def revisa_enlace_hoja(S, quien, fallos):
    """El enlace a la hoja tiene que llevar detras la huella de su contenido.
    GitHub Pages la sirve con max-age=600: sin la huella, tras publicar el
    navegador junta el HTML nuevo con la hoja vieja que tiene guardada y la
    pagina se ve rota. Le paso a Firefox exactamente eso."""
    ver = version_hoja()
    link = S.find('link', rel='stylesheet', href=re.compile(r'estilo\.css'))
    if link is None:
        fallos.append(f'{quien}: no enlaza estilo.css')
        return
    href = link['href']
    if '?v=' not in href:
        fallos.append(f'{quien}: enlaza la hoja sin huella ({href}), '
                      'una cache rancia la puede romper al publicar')
    elif ver and href.split('?v=')[1] != ver:
        fallos.append(f'{quien}: la huella del enlace ({href.split("?v=")[1]}) '
                      f'no es la de estilo.css ({ver})')


def _texto(n):
    return re.sub(r'\s+', ' ', n.get_text(' ', strip=True)) if n else ''


def dom(sec, D, fallos):
    ruta = os.path.join(DEST, archivo(sec))
    if not os.path.exists(ruta):
        fallos.append(f'{sec["slug"]}: falta {archivo(sec)}')
        return
    S = BeautifulSoup(open(ruta, encoding='utf-8').read(), 'html.parser')
    tot = dict(versos=0, ben=0, orig=0, tr=0, trad=0, wbw=0, com=0)

    canciones = S.select('section.song')
    if len(canciones) != len(D['canciones']):
        fallos.append(f'{sec["slug"]}: {len(D["canciones"])} canciones en el JSON, '
                      f'{len(canciones)} en el DOM')
    for c in D['canciones']:
        song = S.find('section', id=f'c{c["n"]}')
        if song is None:
            fallos.append(f'{sec["slug"]} c{c["n"]}: no esta en el DOM')
            continue
        for v in c['versos']:
            ref = f'{sec["slug"]} {c["n"]}.{v["n"]}'
            art = song.find('article', id=f'v{c["n"]}-{v["n"]}')
            if art is None:
                fallos.append(f'{ref}: verso ausente')
                continue
            tot['versos'] += 1

            n = len(art.select('.ben .benU'))
            tot['ben'] += n
            if n != len(v['ben']):
                fallos.append(f'{ref}: {len(v["ben"])} lineas bengalies, {n} en el DOM')
            recortes = art.select('.ben img.orig')
            tot['orig'] += len(recortes)
            for im in recortes:
                # el recorte tiene que existir de verdad y traer sus medidas,
                # o la pagina salta al cargar y la capa de auditoria miente
                src = im.get('src', '')
                if not src.startswith('data:') and not os.path.exists(
                        os.path.join(DEST, src.replace('/', os.sep))):
                    fallos.append(f'{ref}: falta el recorte {src}')
                if not (im.get('width') and im.get('height')):
                    fallos.append(f'{ref}: recorte sin medidas {src}')

            n = len(art.select('p.tr > span'))
            tot['tr'] += n
            if n != len(v['tr']):
                fallos.append(f'{ref}: {len(v["tr"])} lineas de transliteracion, {n} en el DOM')
            if len(v['ben']) != len(v['tr']):
                fallos.append(f'{ref}: {len(v["ben"])} lineas bengalies frente a '
                              f'{len(v["tr"])} de transliteracion')

            trad = art.select_one('.trad')
            if v['trad']:
                tot['trad'] += 1
                if trad is None:
                    fallos.append(f'{ref}: hay traduccion en el JSON y no en el DOM')
                elif not _texto(trad.find('p')):
                    fallos.append(f'{ref}: traduccion vacia en el DOM')
                elif not trad.find('h3'):
                    fallos.append(f'{ref}: traduccion sin rotulo')
            elif trad is not None:
                fallos.append(f'{ref}: traduccion en el DOM que no esta en el JSON')

            pane = art.select_one('.pane-wbw')
            if v['wbw']:
                tot['wbw'] += 1
                if pane is None:
                    fallos.append(f'{ref}: hay glosario en el JSON y no en el DOM')
                else:
                    n = len(pane.select('p.wbw > b'))
                    if n != len(v['wbw']):
                        fallos.append(f'{ref}: {len(v["wbw"])} entradas de glosario, '
                                      f'{n} en el DOM')
                    for w in v['wbw']:
                        if not w['t'].strip() or not w['gloss'].strip():
                            fallos.append(f'{ref}: entrada de glosario vacia {w!r}')
            elif pane is not None:
                fallos.append(f'{ref}: glosario en el DOM que no esta en el JSON')

            pane = art.select_one('.pane-com')
            if v['coment']:
                tot['com'] += 1
                if pane is None:
                    fallos.append(f'{ref}: hay comentario en el JSON y no en el DOM')
                else:
                    n = len(pane.select('blockquote.cita')) + len(pane.select('p.note'))
                    if n != len(v['coment']):
                        fallos.append(f'{ref}: {len(v["coment"])} piezas de comentario, '
                                      f'{n} en el DOM')
                    if not _texto(pane.select_one('.paneBody')):
                        fallos.append(f'{ref}: comentario vacio en el DOM')
            elif pane is not None:
                fallos.append(f'{ref}: comentario en el DOM que no esta en el JSON')

    esp_orig = tot['ben'] if S.select_one('#cap-orig') else 0
    if tot['orig'] != esp_orig:
        fallos.append(f'{sec["slug"]}: {esp_orig} recortes esperados, {tot["orig"]} en el DOM')

    # la barra tiene que llevar el boton de tema y los tres radios que mueve
    if not S.select_one('.bar .tema label.aLuna[for="th-noche"]'):
        fallos.append(f'{sec["slug"]}: falta la luna en la barra')
    if not S.select_one('.bar .tema label.aSol[for="th-dia"]'):
        fallos.append(f'{sec["slug"]}: falta el sol en la barra')
    for r in ('th-auto', 'th-dia', 'th-noche', 'tam-menor', 'tam-medio', 'tam-mayor'):
        if not S.find(id=r):
            fallos.append(f'{sec["slug"]}: falta el radio #{r}')
    # los valores por defecto: tema claro y letra grande
    for r, quien in (('th-dia', 'el tema claro'), ('tam-mayor', 'la letra grande')):
        el = S.find(id=r)
        if el is not None and not el.has_attr('checked'):
            fallos.append(f'{sec["slug"]}: {quien} no viene marcado por defecto (#{r})')
    if not S.select_one('a.arriba[href="#"]'):
        fallos.append(f'{sec["slug"]}: falta el botón de subir al principio')
    revisa_enlace_hoja(S, sec['slug'], fallos)
    if not S.select_one('.top .bar') or not S.select_one('.top details.cfg'):
        fallos.append(f'{sec["slug"]}: la barra y Configuración no van en el mismo bloque pegajoso')
    if S.select_one('details.cfg .cfgIn #th-dia'):
        fallos.append(f'{sec["slug"]}: el tema sigue enseñandose en Configuracion')
    if _texto(S.select_one('details.cfg > summary')) != 'Configuración':
        fallos.append(f'{sec["slug"]}: la pestaña no se llama Configuración')
    # el guardado tiene que ir inline en el <head> y antes de la hoja, o el tema
    # claro parpadea al entrar en la seccion
    js = [s for s in S.head.find_all('script') if s.string and 'localStorage' in s.string]
    if not js:
        fallos.append(f'{sec["slug"]}: el guardado de preferencias no esta en el <head>')
    else:
        orden = [t.name for t in S.head.find_all(['script', 'link'])]
        if 'link' in orden and orden.index('script') > orden.index('link'):
            fallos.append(f'{sec["slug"]}: el guardado va despues de la hoja, el tema parpadeara')
        for k in ('sar-th', 'sar-tam'):
            if f"'{k}'" not in js[0].string and f'"{k}"' not in js[0].string:
                if k.split('-')[1] not in js[0].string:
                    fallos.append(f'{sec["slug"]}: el guardado no toca {k}')

    print(f'  {archivo(sec):28s} versos {tot["versos"]:4d} | bengali {tot["ben"]:4d} | '
          f'recortes {tot["orig"]:4d} | translit {tot["tr"]:4d} | trad {tot["trad"]:4d} | '
          f'glosarios {tot["wbw"]:4d} | comentarios {tot["com"]:4d}')


PROHIBIDOS = [
    ('.songHead', 'border-bottom', 'la raya del encabezado de cancion'),
    ('.pane', 'border-top', 'la raya entre traduccion, glosario y comentario'),
    ('.vtop .line', None, 'la raya del numero de verso'),
    ('.note', 'border-left', 'el filete gris del comentario'),
    ('.head', 'border-bottom', 'la raya bajo el titulo de seccion'),
]


def reglas(css):
    """(selector, declaraciones, condicion del @media) de toda la hoja."""
    import tinycss2
    out = []
    def anda(nodos, media):
        for r in nodos:
            if r.type == 'qualified-rule':
                out.append((re.sub(r'\s+', ' ', tinycss2.serialize(r.prelude)).strip(),
                            tinycss2.serialize(r.content), media))
            elif r.type == 'at-rule' and r.content:
                anda(tinycss2.parse_rule_list(r.content),
                     media + ' ' + tinycss2.serialize(r.prelude).replace(' ', ''))
    anda(tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True), '')
    return out


def hoja(fallos):
    ruta = os.path.join(DEST, 'estilo.css')
    css = open(ruta, encoding='utf-8').read()
    bloques = reglas(css)
    def cuerpo(sel):
        junto = ''
        for s, b, _ in bloques:
            if sel in [re.sub(r'\s+', ' ', x).strip() for x in s.split(',')]:
                junto += b
        return junto or None

    for sel, prop, nombre in PROHIBIDOS:
        b = cuerpo(sel)
        if b is None:
            continue
        if prop is None or re.search(re.escape(prop) + r'\s*:', b):
            fallos.append(f'estilo.css: ha vuelto {nombre} ({sel})')

    def exige(sel, trozo, nombre):
        b = cuerpo(sel)
        if b is None or trozo not in b.replace(' ', ''):
            fallos.append(f'estilo.css: {nombre} ({sel} deberia llevar {trozo})')

    exige('.top', 'position:sticky', 'la barra y Configuracion no acompañan al scroll')
    exige('.top', 'top:0', 'el bloque de arriba no va pegado al borde')
    exige('.cfgIn', 'position:absolute', 'el panel de Configuracion empuja el texto')
    exige('.rail', 'position:fixed', 'el indice lateral sigue en el flujo')
    exige('main', 'margin:0auto', 'la columna de lectura no va centrada')
    exige('.arriba', 'position:fixed', 'el boton de subir no acompaña al scroll')
    # el recorte impreso va como <img>: con mascara CSS Chrome no lo carga desde file://
    for sel in ('.orig', '.benL'):
        b = cuerpo(sel) or ''
        if 'mask-image' in b:
            fallos.append(f'estilo.css: el recorte impreso ha vuelto a ser una mascara CSS ({sel}), '
                          'no se vera al abrir la pagina con file://')
    exige('.orig', 'filter:var(--inv)', 'el recorte impreso no se invierte en tema oscuro')
    if 'blockquote.cita' not in css or 'border-left' not in cuerpo('blockquote.cita'):
        fallos.append('estilo.css: las citas se han quedado sin su filete de acento')
    print(f'  estilo.css                   sin filetes en el cuerpo, '
          f'Configuracion pegajosa, indice lateral fijo')


def _espec(sel):
    """Especificidad aproximada. :not() y :has() son transparentes, asi que sus
    argumentos cuentan; basta para las formas que usa la hoja."""
    s = re.sub(r':(not|has)\(', '(', sel)
    ids = len(re.findall(r'#[\w-]+', s))
    cls = (len(re.findall(r'\.[\w-]+', s)) + len(re.findall(r'\[[^\]]*\]', s))
           + len(re.findall(r'(?<!:):[\w-]+', s)))
    ele = len(re.findall(r'(?:^|[\s>+~(,])([a-z]+)', s))
    return ids, cls, ele


def _casa(sel, media_oscuro, est):
    """Evalua un selector de tema contra un estado (sistema, data-th, radio)."""
    if media_oscuro and not est['sistema_oscuro']:
        return False
    for v in re.findall(r'html:not\(\[data-th="([^"]+)"\]\)', sel):
        if est['data_th'] == v:
            return False
    resto = re.sub(r'html:not\(\[data-th="[^"]+"\]\)', '', sel)
    for v in re.findall(r'html\[data-th="([^"]+)"\]', resto):
        if est['data_th'] != v:
            return False
    for i in re.findall(r'body:not\(:has\(#([\w-]+):checked\)\)', sel):
        if est['radio'] == i:
            return False
    resto = re.sub(r'body:not\(:has\(#[\w-]+:checked\)\)', '', sel)
    for i in re.findall(r'body:has\(#([\w-]+):checked\)', resto):
        if est['radio'] != i:
            return False
    return True


def tema(fallos, defecto='th-dia'):
    """El boton de la barra y los tres radios tienen que decir siempre lo mismo.
    Se recorren todos los estados posibles y se comprueba que se ve un solo icono
    y que es el del tema contrario al que esta puesto. `defecto` es el radio que
    viene marcado en el HTML, que es el que manda hasta que PREFS restaura el
    guardado al cargar el DOM."""
    css = open(os.path.join(DEST, 'estilo.css'), encoding='utf-8').read()
    oscuro, iconos = [], []
    import tinycss2
    def anda(nodos, media_oscuro):
        for r in nodos:
            if r.type == 'qualified-rule':
                sel = re.sub(r'\s+', ' ', tinycss2.serialize(r.prelude)).strip()
                cuerpo = tinycss2.serialize(r.content)
                for parte in [p.strip() for p in sel.split(',')]:
                    if '--bg:#1' in cuerpo.replace(' ', ''):
                        oscuro.append((parte, media_oscuro, _espec(parte)))
                    m = re.search(r'\.(aLuna|aSol)\b', parte)
                    d = re.search(r'display\s*:\s*([\w-]+)', cuerpo)
                    if m and d:
                        iconos.append((parte, media_oscuro, _espec(parte),
                                       m.group(1), d.group(1)))
            elif r.type == 'at-rule' and r.content:
                anda(tinycss2.parse_rule_list(r.content),
                     media_oscuro or 'prefers-color-scheme:dark'
                     in tinycss2.serialize(r.prelude).replace(' ', ''))
    anda(tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True), False)

    if not oscuro or not iconos:
        fallos.append('estilo.css: no se encuentran las reglas del tema')
        return

    def es_oscuro(est):
        return any(_casa(s, m, est) for s, m, _ in oscuro)

    def visible(est, cual):
        gana, val = (-1, -1, -1), ('none' if cual == 'aSol' else 'flex')
        for i, (s, m, e, c, d) in enumerate(iconos):
            if c == cual and _casa(s, m, est) and e >= gana:
                gana, val = e, d
        return val != 'none'

    # estados alcanzables: sin JavaScript (data-th ausente) o con el, antes de
    # que DOMContentLoaded marque el radio (radio por defecto) y despues (van a la par)
    estados = []
    for sis in (False, True):
        for radio in ('th-auto', 'th-dia', 'th-noche'):
            estados.append(dict(sistema_oscuro=sis, data_th=None, radio=radio))
        for dth in ('auto', 'dia', 'noche'):
            estados.append(dict(sistema_oscuro=sis, data_th=dth, radio=defecto))
            estados.append(dict(sistema_oscuro=sis, data_th=dth, radio='th-' + dth))
    # sin nada guardado y sin tocar nada tiene que verse el claro
    if es_oscuro(dict(sistema_oscuro=True, data_th=None, radio=defecto)):
        fallos.append('tema: sin preferencia guardada y con el sistema en oscuro '
                      'la pagina no arranca en claro')

    n = 0
    for est in estados:
        n += 1
        marca = f"sistema={'oscuro' if est['sistema_oscuro'] else 'claro'} " \
                f"data-th={est['data_th']} radio={est['radio']}"
        osc = es_oscuro(est)
        luna, sol = visible(est, 'aLuna'), visible(est, 'aSol')
        if luna == sol:
            fallos.append(f'tema: {marca} -> se ven {"los dos iconos" if luna else "cero iconos"}')
            continue
        if osc != sol:
            fallos.append(f'tema: {marca} -> tema {"oscuro" if osc else "claro"} '
                          f'con el icono de {"sol" if sol else "luna"}')
        # pulsar el icono visible tiene que dar el tema contrario
        pide = 'dia' if sol else 'noche'
        tras = dict(sistema_oscuro=est['sistema_oscuro'], data_th=pide, radio='th-' + pide)
        if es_oscuro(tras) == osc:
            fallos.append(f'tema: {marca} -> pulsar no cambia el tema')
        sinjs = dict(sistema_oscuro=est['sistema_oscuro'], data_th=None, radio='th-' + pide)
        if es_oscuro(sinjs) == osc:
            fallos.append(f'tema: {marca} -> sin JavaScript pulsar no cambia el tema')
    print(f'  {n} estados                  un solo icono, siempre el del tema contrario, '
          f'y pulsarlo cambia el tema con y sin JavaScript')


def anchos(fallos):
    """El indice lateral es fijo: que en ninguna anchura pise el texto ni el
    numero de verso. Las medidas se leen de la hoja, no se dan por sabidas;
    son todo calc() en rem, asi que la cuenta sale exacta."""
    css = open(os.path.join(DEST, 'estilo.css'), encoding='utf-8').read()
    bloques = reglas(css)

    def busca(sel, prop, dentro=None):
        for s, b, media in bloques:
            if sel not in [x.strip() for x in s.split(',')]:
                continue
            if dentro is not None and dentro not in media:
                continue
            m = re.search(re.escape(prop) + r'\s*:\s*([^;}]+)', b)
            if m:
                return m.group(1).strip()
        return None

    def rem(txt, patron):
        m = re.search(patron, (txt or '').replace(' ', ''))
        return float(m.group(1)) * REM if m else None

    corte = None
    for s, b, media in bloques:
        if '.rail' in s and 'position:fixed' in b.replace(' ', ''):
            m = re.search(r'min-width:(\d+)px', media)
            corte = int(m.group(1)) if m else None
    ancho = rem(busca(':root', '--rail'), r'([\d.]+)rem')
    wrap = rem(busca(':root', '--wrap'), r'([\d.]+)rem')
    hueco = rem(busca('.rail', 'left', dentro='min-width'), r'50%-([\d.]+)rem')
    vno = rem(busca('.vno', 'left'), r'-([\d.]+)rem')
    pad_min, pad_vw, pad_max = None, None, None
    m = re.search(r'clamp\(([\d.]+)rem,([\d.]+)vw,([\d.]+)rem\)',
                  (busca('main', 'padding') or '').replace(' ', ''))
    if m:
        pad_min, pad_vw, pad_max = float(m.group(1)) * REM, float(m.group(2)), float(m.group(3)) * REM
    if None in (corte, ancho, wrap, hueco, vno, pad_min):
        fallos.append('estilo.css: no se pueden leer las medidas del indice lateral '
                      f'(corte={corte} ancho={ancho} wrap={wrap} hueco={hueco} vno={vno})')
        return

    peor, izq_min = None, None
    for W in range(corte, 3841):
        pad = min(max(pad_min, pad_vw / 100 * W), pad_max)
        texto_izq = max(0.0, (W - wrap) / 2) + pad
        num_izq = texto_izq - vno            # .vno se enseña a partir de 1180px
        izq = W / 2 - hueco
        der = izq + ancho
        libre = num_izq - der
        if peor is None or libre < peor[1]:
            peor = (W, libre)
        if izq_min is None or izq < izq_min[1]:
            izq_min = (W, izq)
        if libre < REM:
            fallos.append(f'estilo.css: a {W}px el indice lateral deja solo '
                          f'{libre:.0f}px hasta el texto; sube el punto de ruptura')
            break
        if izq < REM:
            fallos.append(f'estilo.css: a {W}px el indice lateral se sale por la '
                          f'izquierda ({izq:.0f}px); sube el punto de ruptura')
            break
    print(f'  {corte}-3840px                 indice de {ancho/REM:.0f}rem | margen izquierdo '
          f'minimo {izq_min[1]:.0f}px a {izq_min[0]}px | holgura minima con el texto '
          f'{peor[1]:.0f}px a {peor[0]}px')


def portada(fallos):
    """La portada lleva el mismo boton de tema y los mismos radios que las
    secciones, o se queda colgada del tema del sistema sin poder cambiarlo."""
    ruta = os.path.join(DEST, 'index.html')
    if not os.path.exists(ruta):
        fallos.append('falta index.html')
        return None
    S = BeautifulSoup(open(ruta, encoding='utf-8').read(), 'html.parser')
    if not S.select_one('.top .bar .tema label.aLuna[for="th-noche"]'):
        fallos.append('index.html: la portada no lleva el botón de tema')
    for r in ('th-dia', 'th-noche', 'th-auto'):
        if not S.find(id=r):
            fallos.append(f'index.html: falta el radio #{r}')
    el = S.find(id='th-dia')
    if el is not None and not el.has_attr('checked'):
        fallos.append('index.html: el tema claro no viene marcado por defecto')
    if not S.select_one('a.arriba[href="#"]'):
        fallos.append('index.html: falta el botón de subir al principio')
    revisa_enlace_hoja(S, 'index.html', fallos)
    js = [s for s in S.head.find_all('script') if s.string and 'localStorage' in s.string]
    if not js:
        fallos.append('index.html: la portada no restaura el tema guardado')
    print(f'  index.html                   botón de tema, tres radios, '
          f'restaura lo guardado, botón de subir, hoja con huella')
    return S


MEDIDAS = [(1400, 950), (1180, 900), (900, 800), (390, 844)]


def navegador(fallos, paginas):
    """Pasada en un navegador de verdad, con file://, que es como se mira el
    sitio en local. Se salta sola si no hay playwright instalado:

        pip install playwright && playwright install chromium

    Comprueba lo que ninguna lectura del HTML puede ver: que los recortes
    cargan (con mascara CSS no cargaban desde file:// y la capa de auditoria
    desaparecia entera), que el alto real del bloque de arriba coincide con
    --topH y por tanto el encabezado de cancion no se esconde detras, que no
    aparece scroll horizontal, y que el boton de tema hace lo que dice."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('  playwright no instalado, se omite la pasada en navegador')
        return
    raiz = 'file:///' + os.path.abspath(DEST).replace(os.sep, '/').lstrip('/')
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for arch in paginas:
            for an, al in MEDIDAS:
                pg = nav.new_page(viewport={'width': an, 'height': al}, color_scheme='dark')
                rotas = []
                pg.on('requestfailed', lambda r: rotas.append(r.url.rsplit('/', 1)[-1]))
                pg.goto(f'{raiz}/{arch}')
                pg.wait_for_timeout(500)
                pg.mouse.wheel(0, 2600)
                pg.wait_for_timeout(500)
                d = pg.evaluate("""() => {
                  const q=s=>document.querySelector(s), D=document.documentElement;
                  const px=v=>{const e=document.createElement('div');e.style.height=v;
                    document.body.appendChild(e);
                    const h=e.getBoundingClientRect().height;e.remove();return h};
                  const cs=getComputedStyle(document.body), top=q('.top');
                  const imgs=[...document.querySelectorAll('img.orig')];
                  const cab=top?top.getBoundingClientRect().bottom:0;
                  const sh=[...document.querySelectorAll('.songHead')]
                      .map(e=>e.getBoundingClientRect())
                      .filter(r=>r.top>-40 && r.top<cab+40)[0];
                  return {topReal: top?top.getBoundingClientRect().height:0,
                          topVar: px(cs.getPropertyValue('--topH')),
                          tapado: sh? +(cab - sh.top).toFixed(1) : 0,
                          rotas: imgs.filter(i=>{
                              const r=i.getBoundingClientRect();
                              if(r.bottom<-300||r.top>innerHeight+300) return false;
                              return !(i.complete && i.naturalWidth>0);}).length,
                          imgs: imgs.length,
                          scrollX: D.scrollWidth > D.clientWidth + 1,
                          bg: cs.backgroundColor, fs: cs.fontSize};
                }""")
                ref = f'{arch} a {an}px'
                if rotas:
                    fallos.append(f'{ref}: no cargan {len(set(rotas))} recursos, '
                                  f'p.ej. {sorted(set(rotas))[:2]}')
                if d['rotas']:
                    fallos.append(f"{ref}: {d['rotas']} recortes a la vista no pintan (de {d['imgs']} en la pagina)")
                if abs(d['topReal'] - d['topVar']) > 1.5:
                    fallos.append(f"{ref}: el bloque de arriba mide {d['topReal']:.1f}px "
                                  f"y --topH dice {d['topVar']:.1f}px")
                if d['tapado'] > 1.5:
                    fallos.append(f"{ref}: el encabezado de canción queda {d['tapado']}px "
                                  f'por detrás de la barra')
                if d['scrollX']:
                    fallos.append(f'{ref}: la página se desborda a lo ancho')
                # el sistema esta en oscuro y aun asi tiene que salir el claro
                if d['bg'] != 'rgb(243, 244, 239)':
                    fallos.append(f"{ref}: no arranca en tema claro ({d['bg']})")
                if d['fs'] != '19px':
                    fallos.append(f"{ref}: no arranca en letra grande ({d['fs']})")
                if an == 1400:
                    pg.click('.tema label.aLuna')
                    pg.wait_for_timeout(400)
                    n = pg.evaluate("""() => {
                      const im=document.querySelector('img.orig');
                      return {bg:getComputedStyle(document.body).backgroundColor,
                              th:document.documentElement.getAttribute('data-th'),
                              inv:im?getComputedStyle(im).filter:'invert(1)',
                              sol:getComputedStyle(document.querySelector('.aSol')).display};
                    }""")
                    if n['bg'] == 'rgb(243, 244, 239)' or n['th'] != 'noche':
                        fallos.append(f'{ref}: pulsar la luna no pone el tema oscuro')
                    if n['sol'] == 'none':
                        fallos.append(f'{ref}: en oscuro no aparece el sol')
                    if n['inv'] != 'invert(1)':
                        fallos.append(f'{ref}: en oscuro el recorte no se invierte')
                pg.close()
        nav.close()
    print(f'  {len(paginas)} páginas × {len(MEDIDAS)} anchos   recortes cargados, '
          f'--topH cuadra con lo pintado, sin desbordes, tema claro y letra grande de salida')


def main():
    pedidas = sys.argv[1:]
    fallos = []
    vistas = 0
    print('DOM')
    for s in SECCIONES:
        if pedidas and s['slug'] not in pedidas:
            continue
        ruta = os.path.join(DEST, 'json', s['slug'] + '.json')
        if not os.path.exists(ruta):
            continue
        vistas += 1
        dom(s, json.load(open(ruta, encoding='utf-8')), fallos)
    print('PORTADA')
    S = portada(fallos)
    defecto = 'th-dia'
    for r in ('th-dia', 'th-noche', 'th-auto'):
        el = S.find(id=r) if S else None
        if el is not None and el.has_attr('checked'):
            defecto = r
    print('HOJA')
    hoja(fallos)
    print('TEMA')
    tema(fallos, defecto)
    print('ANCHOS')
    anchos(fallos)
    print('NAVEGADOR')
    navegador(fallos, [archivo(s) for s in SECCIONES
                       if os.path.exists(os.path.join(DEST, archivo(s)))
                       and (not pedidas or s['slug'] in pedidas)][:2] + ['index.html'])
    if not vistas:
        print('no hay ninguna sección extraída en', os.path.join(DEST, 'json'))
        return 1
    if fallos:
        print('\nFALLOS')
        for f in fallos:
            print(' ', f)
        print('VERIFICACION FALLIDA |', len(fallos), 'fallos')
        return 1
    print('VERIFICACION superada |', vistas, 'secciones')
    return 0


if __name__ == '__main__':
    sys.exit(main())
