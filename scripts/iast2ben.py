#!/usr/bin/env python3
"""IAST (esquema del Śrī Chaitanya Sāraswat Maṭh) -> bengalí Unicode."""
import re, unicodedata

VIR = '\u09CD'   # হসন্ত
CBIN = '\u0981'  # চন্দ্রবিন্দু

CONS = [
    ('kṣ','ক্ষ'), ('jñ','জ্ঞ'),
    ('chh','ছ'), ('ch','চ'), ('jh','ঝ'),
    ('kh','খ'), ('gh','ঘ'), ('ṅ','ঙ'), ('ñ','ঞ'),
    ('ṭh','ঠ'), ('ḍh','ঢ'), ('ṭ','ট'), ('ḍ','ড'), ('ṇ','ণ'),
    ('th','থ'), ('dh','ধ'), ('ph','ফ'), ('bh','ভ'),
    ('k','ক'), ('g','গ'), ('j','জ'),
    ('t','ত'), ('d','দ'), ('n','ন'),
    ('p','প'), ('b','ব'), ('v','ব'), ('m','ম'),
    ('y','য'), ('r','র'), ('l','ল'),
    ('ś','শ'), ('ṣ','ষ'), ('s','স'), ('h','হ'),
]
VOW = [   # (iast, independiente, matra)
    ('ai','ঐ','ৈ'), ('au','ঔ','ৌ'),
    ('ā','আ','া'), ('ī','ঈ','ী'), ('ū','ঊ','ূ'), ('ṛ','ঋ','ৃ'),
    ('a','অ',''), ('i','ই','ি'), ('u','উ','ু'), ('e','এ','ে'), ('o','ও','ো'),
]
SIGNOS = {'ṁ':'ং', 'ḥ':'ঃ'}
VOW_INI = tuple(v[0] for v in VOW)

def palabra(w):
    out = []          # lista de piezas
    i = 0
    pend = False      # acabamos de poner una consonante sin vocal
    ini_cons = None   # índice en out donde empezó esa consonante
    inicio = True     # estamos al principio de una sílaba nueva
    while i < len(w):
        c = w[i]

        # chandrabindu: nasaliza la sílaba anterior, así que va antes de la consonante
        if c == '\u0310':
            if ini_cons is not None: out.insert(ini_cons, CBIN)
            else: out.append(CBIN)
            i += 1; continue

        if c in SIGNOS:
            out.append(SIGNOS[c]); pend = False; inicio = False; i += 1; continue

        if c == '-':
            # guion ante vocal: corte silábico del traductor, no se imprime en bengalí
            resto = w[i+1:]
            if resto.startswith(VOW_INI):
                pass          # corte silábico del traductor: no se imprime ni altera la sílaba
            else:
                out.append('-'); pend = False; inicio = True
            i += 1; continue

        if c in "'’":
            out.append('’'); pend = False; inicio = True; i += 1; continue

        # consonante
        hit = next((p for p in CONS if w.startswith(p[0], i)), None)
        if hit:
            iast, ben = hit
            if iast == 'y' and not (inicio and not pend):
                pass  # য dentro de conjunto (ya-phala)
            if iast == 'y' and not pend and not inicio:
                ben = 'য়'          # entre vocales
            if iast == 'ḍ' and not pend and not inicio:
                ben = 'ড়'
            if iast == 'ḍh' and not pend and not inicio:
                ben = 'ঢ়'
            if pend:
                out.append(VIR)
            ini_cons = len(out)
            out.append(ben)
            pend = True; inicio = False; i += len(iast); continue

        # vocal
        hit = next((p for p in VOW if w.startswith(p[0], i)), None)
        if hit:
            iast, indep, matra = hit
            out.append(matra if pend else indep)
            pend = False; inicio = False; ini_cons = None; i += len(iast); continue

        out.append(c); pend = False; inicio = True; i += 1
    return ''.join(out)

def iast_a_bengali(texto):
    piezas = re.split(r'(\s+|[,;.!?…"“”()])', texto)
    return ''.join(p if (not p.strip() or re.fullmatch(r'[\s,;.!?…"“”()]+', p)) else palabra(p)
                   for p in piezas)

BD = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')

# ---- verificación estructural contra los glifos de la fuente heredada ----
MATRAS = set('ািীুূৃেৈোৌ')
IND = set('অআইঈউঊঋএঐওঔ')
CONSU = set('কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়')
SIGNU = set('ংঃঁ')

def unidades(s):
    """cuántos bloques visuales tendría esta línea en la fuente heredada"""
    n = 0
    for i, ch in enumerate(s):
        if ch in CONSU:
            if i >= 1 and s[i-1] == VIR:  # el conjunto es un solo glifo
                continue
            n += 1
        elif ch in MATRAS or ch in IND or ch in SIGNU:
            n += 1
        elif ch in '-’':
            n += 1
    return n

# ---- vuelta atrás: bengalí -> IAST, para comparar con lo que imprimió el editor ----
REV_C = {unicodedata.normalize('NFD',k)[0]:v for k,v in {'ক':'k','খ':'kh','গ':'g','ঘ':'gh','ঙ':'ṅ','চ':'ch','ছ':'chh','জ':'j','ঝ':'jh','ঞ':'ñ',
 'ট':'ṭ','ঠ':'ṭh','ড':'ḍ','ঢ':'ḍh','ণ':'ṇ','ত':'t','থ':'th','দ':'d','ধ':'dh','ন':'n',
 'প':'p','ফ':'ph','ব':'b','ভ':'bh','ম':'m','য':'y','র':'r','ল':'l','শ':'ś','ষ':'ṣ','স':'s','হ':'h',
 }.items()}
REV_M = {'া':'ā','ি':'i','ী':'ī','ু':'u','ূ':'ū','ৃ':'ṛ','ে':'e','ৈ':'ai','ো':'o','ৌ':'au'}
REV_I = {'অ':'a','আ':'ā','ই':'i','ঈ':'ī','উ':'u','ঊ':'ū','ঋ':'ṛ','এ':'e','ঐ':'ai','ও':'o','ঔ':'au'}

def bengali_a_iast(s):
    s=unicodedata.normalize('NFC', s)   # ো y ৌ deben ir compuestas
    out=[];i=0
    while i < len(s):
        c=s[i]
        if c in REV_C:
            out.append(REV_C[c]); i+=1
            if i<len(s) and s[i]=='\u09BC': i+=1   # punto suscrito: ড় ঢ় য়
            if i<len(s) and s[i]==VIR: i+=1
            elif i<len(s) and s[i] in REV_M: out.append(REV_M[s[i]]); i+=1
            elif i<len(s) and s[i]==CBIN:
                i+=1
                if i<len(s) and s[i] in REV_M: out.append(REV_M[s[i]]); i+=1
                else: out.append('a')
            else: out.append('a')
            continue
        if c in REV_I: out.append(REV_I[c]); i+=1; continue
        if c=='ং': out.append('ṁ'); i+=1; continue
        if c=='ঃ': out.append('ḥ'); i+=1; continue
        if c==CBIN or c==VIR: i+=1; continue
        out.append(c); i+=1
    return ''.join(out)

def normaliza(s):
    s=s.lower()
    for a,b in [('v','b'),('-',''),('’',''),("'",''),('\u0310','')]: s=s.replace(a,b)
    return re.sub(r'[^a-zāīūṛṁḥṅñṭḍṇśṣ]','',s)

MARCA = {',': ',', ']': '।'}

def linea_bengali(segmentos, legacy):
    """convierte una línea y coloca la puntuación donde la puso el editor"""
    partes = [iast_a_bengali(s).replace(',', '').strip() for s in segmentos]
    crudo = re.sub(r'<[^<>]{1,4}<\s*$', '', legacy.strip())
    seq = [ch for ch in crudo if not ch.isspace()]
    marcas = []
    vistos = 0
    for ch in seq:
        if ch in MARCA: marcas.append((vistos, MARCA[ch]))
        else: vistos += 1
    total = max(vistos, 1)
    us = [unidades(p) for p in partes]
    acum, s = [], 0
    for u in us:
        s += u; acum.append(s / max(sum(us), 1))
    usados = set()
    for pos, mk in marcas:
        f = pos / total
        cand = sorted(range(len(acum)), key=lambda j: (abs(acum[j] - f), j))
        for j in cand:
            if j not in usados:
                partes[j] = partes[j] + mk; usados.add(j); break
    return partes
