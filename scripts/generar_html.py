#!/usr/bin/env python3
"""Genera la sección como HTML estático: el texto va escrito en el documento,
no se construye en el navegador. El único JavaScript obligatorio es el guardado
de preferencias (PREFS), diez líneas en el <head>; el buscador es opcional."""
import json, html, os
from iast2ben import linea_bengali

BD = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
esc = lambda s: html.escape(s, quote=False)

# Guardado de preferencias. Corre antes de pintar para que no parpadee el tema
# claro al entrar en una sección. Marca <html data-th> y <html data-tam>, que la
# hoja lee igual que los radios; con JavaScript apagado no pasa nada y la página
# arranca en los valores por defecto.
PREFS = r'''try{var D=document.documentElement,S=localStorage,K=['th','tam'];
K.forEach(function(k){var v=S.getItem('sar-'+k);if(v)D.setAttribute('data-'+k,v)});
addEventListener('change',function(e){var n=e.target.name;if(K.indexOf(n)<0)return;
var v=e.target.id.slice(n.length+1);D.setAttribute('data-'+n,v);
try{S.setItem('sar-'+n,v)}catch(x){}});
addEventListener('DOMContentLoaded',function(){K.forEach(function(k){
var v=D.getAttribute('data-'+k),i=v&&document.getElementById(k+'-'+v);
if(i)i.checked=true})})}catch(x){}'''

CABEZA = '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<script>%s</script>''' % PREFS

LUNA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M20.5 14.3A8.6 8.6 0 0 1 9.7 3.5a8.8 8.8 0 1 0 10.8 10.8Z"/></svg>')
SOL = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
       'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/>'
       '<path d="M12 2.4v2.2M12 19.4v2.2M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2.4 12h2.2'
       'M19.4 12h2.2M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/></svg>')

CSS = r'''
:root{
  box-sizing:border-box;
  padding-top:env(safe-area-inset-top,0px);
  padding-bottom:env(safe-area-inset-bottom,0px);
  --bg:#F3F4EF; --surface:#FAFAF7; --ink:#1A1C19; --ink2:#55594F; --ink3:#83887C;
  --rule:#DCDDD3; --accent:#35507D; --mark:#8E6A2A;
  --serif:"Noto Serif",Georgia,"Times New Roman",serif;
  --sans:"Archivo","Helvetica Neue",Arial,sans-serif;
  --beng:"Noto Serif Bengali","Noto Serif",serif;
  --benK:.55; --fs:17px; --wrap:37rem;
  /* alto del encabezado pegajoso: barra + tira de Configuracion */
  --barH:3.4rem; --cfgH:2.3rem; --topH:calc(var(--barH) + var(--cfgH));
  /* ritmo vertical. Sin filetes la jerarquia la marca el blanco: cada escalon
     tiene que leerse mayor que el de dentro */
  --sep1:1.35rem;  /* entre bengali y transliteracion, la misma capa */
  --sep2:2.2rem;   /* antes de un rotulo: traduccion, glosario, comentario */
  --sep3:4.6rem;   /* entre versos */
  --sep4:6.4rem;   /* entre canciones */
  --rail:11rem;
  color-scheme:light;
}
/* tema oscuro por preferencia del sistema, salvo que se haya pedido dia */
@media (prefers-color-scheme:dark){
  html:not([data-th="dia"]) body:not(:has(#th-dia:checked)){
    --bg:#101215; --surface:#161A1D; --ink:#E3E4DD; --ink2:#A2A79E; --ink3:#767C74;
    --rule:#282D31; --accent:#93A9D2; --mark:#C9A557; color-scheme:dark;
  }
}
/* tema oscuro pedido a mano. data-th lo pone PREFS; el radio manda sin JavaScript */
html[data-th="noche"] body,
body:has(#th-noche:checked){
  --bg:#101215; --surface:#161A1D; --ink:#E3E4DD; --ink2:#A2A79E; --ink3:#767C74;
  --rule:#282D31; --accent:#93A9D2; --mark:#C9A557; color-scheme:dark;
}
html[data-tam="menor"] body,
body:has(#tam-menor:checked){--fs:15.5px;--benK:.47}
html[data-tam="mayor"] body,
body:has(#tam-mayor:checked){--fs:19px;--benK:.64}
body:has(#cap-ben:not(:checked)) .ben,
body:has(#cap-tr:not(:checked)) .tr,
body:has(#cap-trad:not(:checked)) .trad,
body:has(#cap-wbw:not(:checked)) .pane-wbw,
body:has(#cap-com:not(:checked)) .pane-com{display:none}
body:has(#cap-orig:not(:checked)) .orig{display:none}

*,*::before,*::after{box-sizing:inherit}
html{scroll-padding-top:calc(env(safe-area-inset-top,0px) + var(--topH) + 1rem);
  -webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--serif);font-size:var(--fs);
  line-height:1.62;-webkit-font-smoothing:antialiased}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
.oculto{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}

/* barra */
.bar{position:sticky;top:0;z-index:40;background:color-mix(in srgb,var(--bg) 90%,transparent);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--rule)}
.barIn{display:flex;align-items:center;gap:.7rem;max-width:74rem;margin:0 auto;
  padding:.6rem clamp(.9rem,3vw,1.4rem);min-height:calc(var(--barH) - 1px)}
.brand{font-family:var(--sans);font-weight:600;font-size:.82rem;letter-spacing:.02em;line-height:1.25}
.brand em{display:block;font-style:normal;font-weight:400;font-size:.74rem;color:var(--ink3)}

/* boton de tema: dos etiquetas superpuestas, se ve la del tema contrario al que
   hay puesto. Mueve los mismos radios que estaban en Configuracion, asi que no
   puede contradecirlos */
.tema{display:flex;align-items:center;flex:none}
.tema>label{display:none;align-items:center;justify-content:center;
  width:1.9rem;height:1.9rem;border-radius:99px;cursor:pointer;color:var(--ink3)}
.tema>label:hover{color:var(--ink);background:var(--rule)}
.tema svg{width:1.05rem;height:1.05rem;display:block}
.tema .aLuna{display:flex}
@media (prefers-color-scheme:dark){
  html:not([data-th="dia"]) body:not(:has(#th-dia:checked)) .aLuna{display:none}
  html:not([data-th="dia"]) body:not(:has(#th-dia:checked)) .aSol{display:flex}
}
html[data-th="noche"] .aLuna,body:has(#th-noche:checked) .aLuna{display:none}
html[data-th="noche"] .aSol,body:has(#th-noche:checked) .aSol{display:flex}
html[data-th="dia"] .aLuna{display:flex}
html[data-th="dia"] .aSol{display:none}

.jump{display:flex;flex-wrap:nowrap;gap:.1rem;margin-left:auto;
  max-width:min(58%,24rem);overflow-x:auto;scrollbar-width:none}
.jump::-webkit-scrollbar{display:none}
.jump a{flex:none;font-family:var(--sans);font-size:.78rem;color:var(--ink3);text-decoration:none;
  padding:.3rem .5rem;border-radius:5px}
.jump a:hover{color:var(--ink);background:var(--rule)}

/* Configuracion: tira pegajosa justo debajo de la barra, acompana al lector.
   El panel va absoluto para que abrirlo no empuje el texto ni engorde la tira */
details.cfg{position:sticky;top:var(--barH);z-index:35;
  border-bottom:1px solid var(--rule);background:var(--surface)}
details.cfg>summary{list-style:none;cursor:pointer;max-width:74rem;margin:0 auto;
  padding:.55rem clamp(.9rem,3vw,1.4rem);min-height:calc(var(--cfgH) - 1px);
  font-family:var(--sans);font-size:.75rem;letter-spacing:.02em;color:var(--ink3);
  display:flex;align-items:center;gap:.45rem}
details.cfg>summary::-webkit-details-marker{display:none}
details.cfg>summary::before{content:"";width:.4rem;height:.4rem;border-right:1.4px solid currentColor;
  border-bottom:1.4px solid currentColor;transform:rotate(-45deg);margin-bottom:.12rem}
details.cfg[open]>summary::before{transform:rotate(45deg)}
details.cfg>summary:hover{color:var(--ink)}
.cfgIn{position:absolute;left:0;right:0;top:100%;background:var(--surface);
  border-bottom:1px solid var(--rule);box-shadow:0 12px 24px -16px rgba(0,0,0,.45);
  padding:.7rem max(clamp(.9rem,3vw,1.4rem),calc(50% - 37rem)) 1.1rem;
  display:flex;flex-wrap:wrap;gap:1.6rem;max-height:65vh;overflow:auto}
fieldset{border:0;margin:0;padding:0}
legend{font-family:var(--sans);font-size:.68rem;letter-spacing:.09em;color:var(--ink3);
  font-weight:600;padding:0 0 .45rem}
.opts{display:flex;flex-wrap:wrap;gap:.3rem}
.opts label{font-family:var(--sans);font-size:.8rem;color:var(--ink2);cursor:pointer;
  padding:.28rem .62rem;border:1px solid var(--rule);border-radius:99px;background:var(--bg)}
.opts input{position:absolute;opacity:0;width:0;height:0}
.opts input:checked+span{color:var(--ink)}
.opts label:has(input:checked){border-color:var(--mark);color:var(--ink);
  background:color-mix(in srgb,var(--mark) 12%,transparent)}
.opts label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:2px}

/* buscador: solo aparece si hay JavaScript */
.buscar{display:none}
html[data-js] .buscar{display:flex;align-items:center;gap:.5rem;flex:1;max-width:17rem;margin-left:auto}
.buscar input{width:100%;font-family:var(--serif);font-size:.9rem;color:var(--ink);background:var(--surface);
  border:1px solid var(--rule);border-radius:7px;padding:.36rem .6rem}
.buscar input::placeholder{color:var(--ink3)}
html[data-js] .jump{margin-left:0}
.vacio{display:none;padding:3rem 0;color:var(--ink3);font-family:var(--sans);font-size:.85rem}
body.filtrando .song:not(:has(.verse:not([hidden]))){display:none}

/* disposicion: la columna de lectura se centra en la pantalla y el indice
   lateral va fijo, fuera del flujo, para no descentrarla */
.shell{display:block}
main{padding:0 clamp(1rem,4vw,2rem) 6rem;max-width:var(--wrap);margin:0 auto}
.rail{display:none}
@media (min-width:1180px){
  .rail{display:block;position:fixed;z-index:15;
    top:calc(var(--topH) + 1.9rem);
    left:calc(50% - 32.5rem);
    width:var(--rail);
    max-height:calc(100vh - var(--topH) - 3.6rem);
    max-height:calc(100dvh - var(--topH) - 3.6rem);
    overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;
    padding:0 .4rem 1.2rem 0}
  .rail h2{font-family:var(--sans);font-size:.68rem;letter-spacing:.09em;color:var(--ink3);
    margin:0 0 .7rem;font-weight:600}
  .rail a{display:block;padding:.4rem 0 .4rem .7rem;font-size:.86rem;color:var(--ink2);
    text-decoration:none;border-left:2px solid transparent;line-height:1.35}
  .rail a:hover{color:var(--ink);border-left-color:var(--rule)}
  .rail a b{font-weight:500;color:var(--ink);font-variant-numeric:tabular-nums}
  .jump{display:none}
  .barIn .pasos{margin-left:auto}
}

/* portada */
.head{padding:3.4rem 0 0;margin-bottom:3.4rem}
.head .over{font-family:var(--sans);font-size:.72rem;letter-spacing:.1em;color:var(--ink3);margin:0 0 .9rem}
.head h1{font-size:2.1rem;font-weight:500;letter-spacing:-.01em;margin:0;line-height:1.15}
.head p{margin:.35rem 0 0;color:var(--ink2);font-size:1rem}

/* cancion */
.song{margin:0 0 var(--sep4)}
.songHead{position:sticky;top:var(--topH);z-index:20;display:flex;align-items:baseline;gap:.7rem;
  padding:.9rem 0 .75rem;margin-bottom:2.5rem;background:linear-gradient(var(--bg) 66%,transparent)}
.songHead .no{font-family:var(--beng);font-size:1.4rem;color:var(--mark);line-height:1}
.songHead h2{margin:0;font-size:.95rem;font-weight:400;font-style:italic;color:var(--ink2);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* verso */
.verse{position:relative;margin:0 0 var(--sep3);scroll-margin-top:calc(var(--topH) + 1.4rem)}
.vno{position:absolute;left:-2.9rem;top:.05rem;font-family:var(--beng);font-size:1rem;
  color:var(--ink3);line-height:1;display:none}
.vtop{display:flex;align-items:center;margin:0 0 1.1rem}
.vtop .n{font-family:var(--beng);font-size:1.05rem;color:var(--mark);line-height:1}
@media (min-width:1180px){.vno{display:block}.vtop{display:none}}

.ben{display:flex;flex-direction:column;align-items:center;gap:.55rem;margin:0 0 var(--sep1)}
.benRow{display:flex;flex-direction:column;align-items:center;gap:.1rem;width:100%}
.benU{font-family:var(--beng);font-size:1.34em;line-height:1.95;margin:0;text-align:center;font-weight:500}
.benU i{font-style:normal}
.benU i+i{margin-left:1.6em}
.benU .danda{color:var(--mark)}
@media (max-width:520px){.benU{font-size:1.2em}.benU i+i{margin-left:.9em}}
.orig{opacity:.4;width:min(100%,calc(var(--w) * var(--benK) * .74px))}
.benL{display:block;background-color:currentColor;opacity:.93;
  width:min(100%,calc(var(--w) * var(--benK) * 1px));aspect-ratio:var(--w) / var(--h);
  -webkit-mask-image:var(--m);mask-image:var(--m);
  -webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:100% 100%;mask-size:100% 100%}
.tr{margin:0 0 var(--sep2);text-align:center;font-weight:500;line-height:1.75;letter-spacing:.005em}
.tr span{display:block}
.tr span i{font-style:normal}
.tr span i+i{margin-left:1.5em}
@media (max-width:520px){.tr span i+i{margin-left:.9em}}

/* rotulos: cargan con la separacion que antes hacian los filetes */
.trad>h3,.pane h3{margin:0 0 .5rem;font-family:var(--sans);font-size:.68rem;
  letter-spacing:.1em;text-transform:uppercase;font-weight:600;color:var(--ink2);line-height:1.4}
.trad{margin:0 0 var(--sep2)}
.trad p{margin:0;line-height:1.72}
.pane{margin:0}
.pane+.pane{margin-top:var(--sep2)}
.paneBody{padding:0}
.wbw{font-size:.87rem;line-height:1.75;color:var(--ink2);margin:0}
.wbw b{font-weight:600;color:var(--ink);font-style:italic}
.wbw i{font-style:italic;color:var(--ink3)}
.wbw s{text-decoration:none;color:var(--ink3)}
.note{font-size:.93rem;line-height:1.68;color:var(--ink2);margin:0 0 .95rem}
.note:last-child{margin-bottom:0}
.note b{color:var(--ink);font-weight:600;font-style:italic}
/* el filete de las citas se queda: no separa capas, marca el verso ajeno que el
   comentarista trae de fuera y es lo unico que lo distingue de su propia prosa */
blockquote.cita{margin:1.15rem 0;padding-left:1rem;
  border-left:2px solid color-mix(in srgb,var(--accent) 45%,transparent);
  font-style:italic;font-size:.92rem;line-height:1.6;color:var(--ink2)}
blockquote.cita span{display:block}
/* un sloka de varias lineas llega partido en varias citas seguidas: se leen
   como un solo bloque, no como citas distintas */
blockquote.cita+blockquote.cita{margin-top:0}
blockquote.cita:first-child{margin-top:0}
blockquote.cita:last-child{margin-bottom:0}

.barIn .pasos{margin-left:.2rem}
.pasos{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center}
.pasos .ir{font-family:var(--sans);font-size:.78rem;color:var(--ink2);text-decoration:none;
  padding:.3rem .62rem;border:1px solid var(--rule);border-radius:99px;white-space:nowrap}
.pasos .ir:hover{color:var(--ink);border-color:var(--mark)}
main>.pasos{margin:3.4rem 0 0;justify-content:space-between}
.pie{margin:3rem 0 0;font-family:var(--sans);font-size:.78rem;line-height:1.6;color:var(--ink3)}
@media print{
  .bar,details.cfg,.rail,.vacio,.pasos{display:none}
  body{--fs:11pt;background:#fff;color:#000}
  .verse{break-inside:avoid}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
'''

JS = r'''
document.documentElement.dataset.js = '1';
const fold = s => s.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase();
const versos = [...document.querySelectorAll('.verse')].map(n => ({n, t: fold(n.textContent)}));
const campo = document.getElementById('q');
const vacio = document.getElementById('vacio');
campo.addEventListener('input', () => {
  const q = fold(campo.value.trim());
  const filtrando = q.length >= 2;
  document.body.classList.toggle('filtrando', filtrando);
  let hallados = 0;
  for (const v of versos) {
    const ok = !filtrando || v.t.includes(q);
    v.n.hidden = !ok;
    if (ok && filtrando) hallados++;
  }
  vacio.style.display = filtrando && !hallados ? 'block' : 'none';
});
'''

def radios(nombre, items):
    out = []
    for iid, label, chk in items:
        c = ' checked' if chk else ''
        out.append(f'<label><input type="radio" name="{nombre}" id="{iid}"{c}><span>{label}</span></label>')
    return '\n'.join(out)

def checks(items):
    out = []
    for iid, label in items:
        out.append(f'<label><input type="checkbox" id="{iid}" checked><span>{label}</span></label>')
    return '\n'.join(out)

def rango_txt(r):
    if not r: return ''
    return f'versos {r[0]} y {r[1]}' if len(r) == 2 else f'versos {r[0]} a {r[-1]}'

def verso_html(c, v, con_original=True):
    p = []
    p.append(f'<article class="verse" id="v{c["n"]}-{v["n"]}">')
    p.append(f'<div class="vno" aria-hidden="true">{str(v["n"]).translate(BD)}</div>')
    p.append('<div class="vtop">'
             f'<span class="n" aria-hidden="true">{str(v["n"]).translate(BD)}</span></div>')
    lineas = [linea_bengali(seg, leg) for seg, leg in zip(v['tr'], v['legacy'])]
    lineas[-1][-1] += ' <danda>॥' + str(v['n']).translate(BD) + '॥</danda>'
    p.append('<div class="ben">')
    for partes, im in zip(lineas, v['ben']):
        cuerpo = ' '.join('<i>' + esc(x).replace('&lt;danda&gt;', '<b class="danda">')
                         .replace('&lt;/danda&gt;', '</b>') + '</i>' for x in partes)
        p.append('<div class="benRow"><p class="benU" lang="bn">' + cuerpo + '</p>')
        if con_original:
            u = im['src'] if 'src' in im else f'data:image/png;base64,{im["png"]}'
            p.append(f'<span class="benL orig" style="--w:{im["w"]};--h:{im["h"]};'
                     f'--m:url({u})"></span>')
        p.append('</div>')
    p.append('</div>')

    p.append('<p class="tr">')
    for linea in v['tr']:
        segs = ''.join(f'<i>{esc(s)}</i>' for s in linea)
        p.append(f'<span>{segs}</span>')
    p.append('</p>')

    if v['trad']:
        r = rango_txt(v.get('trad_rango'))
        p.append(f'<div class="trad"><h3>Traducción{" · " + r if r else ""}</h3>'
                 f'<p>{esc(v["trad"])}</p></div>')

    if v['wbw']:
        piezas = []
        for w in v['wbw']:
            t = f'<b>{esc(w["t"])}</b>'
            if w['v']:
                t += f' <i>({esc(w["v"])})</i>'
            piezas.append(t + ' ' + esc(w['gloss']))
        eh = ' · ' + rango_txt(v.get('wbw_rango')) if v.get('wbw_rango') else ''
        p.append(f'<section class="pane pane-wbw"><h3>Palabra por palabra{eh}</h3>'
                 '<div class="paneBody"><p class="wbw">'
                 + '<s> · </s>'.join(piezas) + '</p></div></section>')

    if v['coment']:
        cuerpo = []
        for it in v['coment']:
            if it['t'] == 'cita':
                lineas = ''.join(f'<span>{esc(x)}</span>' for x in it['x'])
                cuerpo.append(f'<blockquote class="cita">{lineas}</blockquote>')
            else:
                txt = it['x']
                corte = txt.find(':')
                if 2 < corte < 70:
                    cuerpo.append(f'<p class="note"><b>{esc(txt[:corte])}</b>:{esc(txt[corte+1:])}</p>')
                else:
                    cuerpo.append(f'<p class="note">{esc(txt)}</p>')
        p.append('<section class="pane pane-com"><h3>Comentario</h3><div class="paneBody">'
                 + ''.join(cuerpo) + '</div></section>')

    p.append('</article>')
    return '\n'.join(p)

def construir(D, con_buscador=True, nota=None, con_original=True, css='inline', nav=None):
    """Arma el documento. con_buscador=False deja la pagina sin mas JavaScript
    que PREFS, las diez lineas del <head> que recuerdan tamano y tema."""
    sec = D['seccion']
    rail = '\n'.join(f'<a href="#c{c["n"]}"><b>{c["n"]}</b>  {esc(c["titulo"])}</a>' for c in D['canciones'])
    jump = '\n'.join(f'<a href="#c{c["n"]}">{c["n"]}</a>' for c in D['canciones'])

    canciones = []
    for c in D['canciones']:
        versos = '\n'.join(verso_html(c, v, con_original) for v in c['versos'])
        canciones.append(
            f'<section class="song" id="c{c["n"]}">'
            f'<div class="songHead"><span class="no" aria-hidden="true">{str(c["n"]).translate(BD)}</span>'
            f'<h2>{esc(c["titulo"])}</h2></div>\n{versos}</section>')

    buscador = ('<div class="buscar">'
                '<label class="oculto" for="q">Buscar en la seccion</label>'
                '<input id="q" type="search" placeholder="Buscar" autocomplete="off" spellcheck="false">'
                '</div>') if con_buscador else ''
    vacio = '<p class="vacio" id="vacio">Ningun verso coincide con la busqueda.</p>' if con_buscador else ''
    script = f'<script>{JS}</script>' if con_buscador else ''
    pie = f'<p class="pie">{esc(nota)}</p>' if nota else ''
    items = [('cap-ben', 'Bengali')]
    if con_original:
        items.append(('cap-orig', 'Original impreso'))
    items += [('cap-tr', 'Transliteracion'), ('cap-trad', 'Traduccion'),
              ('cap-wbw', 'Palabra por palabra'), ('cap-com', 'Comentario')]
    capas = checks(items)
    # Los radios de tema ya no se ensenan en Configuracion: los mueve el boton de
    # la barra. Siguen en el documento porque son ellos los que llevan el tema
    # cuando no hay JavaScript.
    tema = ('<div class="tema">'
            '<fieldset class="oculto"><legend>Tema</legend><div class="opts">'
            + radios('th', [('th-auto', 'Automatico', True), ('th-dia', 'Dia', False),
                            ('th-noche', 'Noche', False)])
            + '</div></fieldset>'
            f'<label class="aLuna" for="th-noche" title="Tema oscuro">{LUNA}'
            '<span class="oculto">Tema oscuro</span></label>'
            f'<label class="aSol" for="th-dia" title="Tema claro">{SOL}'
            '<span class="oculto">Tema claro</span></label>'
            '</div>')
    hoja = f'<style>{CSS}</style>' if css == 'inline' else f'<link rel="stylesheet" href="{css}">'
    nav = nav or {}
    enlaces = ['<a class="ir" href="%s">Índice</a>' % nav['indice']] if nav.get('indice') else []
    if nav.get('ant'):
        enlaces.append('<a class="ir" href="%s" rel="prev">&#8592; %s</a>' % nav['ant'])
    if nav.get('sig'):
        enlaces.append('<a class="ir" href="%s" rel="next">%s &#8594;</a>' % nav['sig'])
    pasos = '<nav class="pasos" aria-label="Secciones">' + ''.join(enlaces) + '</nav>' if enlaces else ''

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
{CABEZA}
<title>&#346;ara&#7751;&#257;gati &#183; {esc(sec["rom"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,500;0,600;1,400&amp;family=Archivo:wght@400;500;600&amp;family=Noto+Serif+Bengali:wght@400;500&amp;display=swap" rel="stylesheet">
{hoja}
</head>
<body>

<header class="bar">
  <div class="barIn">
    <div class="brand">&#346;ara&#7751;&#257;gati<em>{esc(sec["rom"])}</em></div>
    {tema}
    {buscador}
    <nav class="jump" aria-label="Canciones">{jump}</nav>
    {pasos}
  </div>
</header>

<details class="cfg">
  <summary>Configuraci&#243;n</summary>
  <div class="cfgIn">
    <fieldset><legend>CAPAS</legend><div class="opts">
      {capas}
    </div></fieldset>
    <fieldset><legend>TAMANO</legend><div class="opts">
      {radios('tam',[('tam-menor','Menor',False),('tam-medio','Medio',True),('tam-mayor','Mayor',False)])}
    </div></fieldset>
  </div>
</details>

<div class="shell">
  <nav class="rail" aria-label="Canciones"><h2>CANCIONES</h2>{rail}</nav>
  <main>
    <div class="head">
      <p class="over">&#346;r&#299; Laghu-chandrik&#257;-bh&#257;&#7779;ya</p>
      <h1>{esc(sec["rom"])}</h1>
      <p>{esc(sec["es"])}</p>
    </div>
    {''.join(canciones)}
    {vacio}
    {pasos}
    {pie}
  </main>
</div>

{script}
</body>
</html>
'''


def comprobar(doc, D):
    """Cuenta en el DOM lo que deberia haber segun el JSON."""
    from html.parser import HTMLParser
    clases, vacios = [], []

    class P(HTMLParser):
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if 'class' in a:
                clases.extend(a['class'].split())
    P().feed(doc)

    for c in D['canciones']:
        # un verso puede no traer glosario ni traduccion propios si los comparte
        # con el vecino, como el (3-4) de Mangalacharana
        cub = {n for v in c['versos'] for n in (v.get('trad_rango') or [])}
        for v in c['versos']:
            for campo in ('ben', 'legacy', 'tr', 'trad'):
                if not v[campo] and not (campo == 'trad' and v['n'] in cub):
                    vacios.append(f'{c["n"]}.{v["n"]}:{campo}')
            if len(v['ben']) != len(v['tr']):
                vacios.append(f'{c["n"]}.{v["n"]}:lineas')

    esp = {
        'verse': sum(len(c['versos']) for c in D['canciones']),
        'benU': sum(len(v['tr']) for c in D['canciones'] for v in c['versos']),
        'trad': sum(1 for c in D['canciones'] for v in c['versos'] if v['trad']),
        'pane-wbw': sum(1 for c in D['canciones'] for v in c['versos'] if v['wbw']),
        'pane-com': sum(1 for c in D['canciones'] for v in c['versos'] if v['coment']),
        'song': len(D['canciones']),
    }
    ok = True
    for k, n in esp.items():
        hay = clases.count(k)
        marca = 'ok' if hay == n else 'MAL'
        if hay != n:
            ok = False
        print(f'  {k:10s} esperados {n:4d}  en el DOM {hay:4d}  {marca}')
    if vacios:
        ok = False
        print('  campos vacios:', vacios)
    print('  comprobacion', 'superada' if ok else 'FALLIDA')
    return ok


if __name__ == '__main__':
    D = json.load(open('data.json', encoding='utf-8'))
    doc = construir(D)
    comprobar(doc, D)
    os.makedirs('salida', exist_ok=True)
    open('salida/saranagati.html', 'w', encoding='utf-8', newline='\n').write(doc)
    print('HTML', round(len(doc)/1e6, 2), 'MB')
