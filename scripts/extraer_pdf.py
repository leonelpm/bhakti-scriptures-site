import pdfplumber, re, json, os, subprocess
PDF = os.environ.get('SARANAGATI_PDF', '/mnt/user-data/uploads/SARANAGATI.pdf')
pdf = pdfplumber.open(PDF)
DIG={'!':'1','@':'2','#':'3','$':'4','%':'5','^':'6','&':'7','*':'8','(':'9',')':'0'}
PAGES = 'pages300'

def rasterizar(p0, p1):
    """Deja en pages300/ las paginas del rango a 300 DPI, solo las que falten."""
    os.makedirs(PAGES, exist_ok=True)
    faltan = [n for n in range(p0, p1 + 1) if not os.path.exists(f'{PAGES}/p-{n:03d}.png')]
    if not faltan: return
    a, b = min(faltan), max(faltan)
    subprocess.run(['pdftoppm', '-r', '300', '-png', '-f', str(a), '-l', str(b),
                    PDF, f'{PAGES}/p'], check=True)

MK_T=r'\[(\d+)(?:\s*[\u2013\u2014-]\s*(\d+))?\]'   # [3] o [3-4] del glosario
MK_P=r'\((\d+)(?:\s*[\u2013\u2014-]\s*(\d+))?\)'   # (3) o (3-4) de traduccion y comentario

def rango(m):
    a=int(m.group(1)); b=int(m.group(2)) if m.group(2) else a
    return list(range(a, b+1))

def get_lines(p,tol=3.0):
    out=[]
    for ch in sorted(p.chars,key=lambda c:(c['top'],c['x0'])):
        if out and abs(ch['top']-out[-1]['top'])<=tol: out[-1]['chars'].append(ch)
        else: out.append({'top':ch['top'],'chars':[ch]})
    res=[]
    for l in out:
        chs=sorted(l['chars'],key=lambda c:c['x0'])
        first=[c for c in chs if c['text'].strip()]
        res.append({'page':p.page_number,'top':min(c['top'] for c in chs),'bottom':max(c['bottom'] for c in chs),
          'x0':min(c['x0'] for c in chs),'x1':max(c['x1'] for c in chs),
          'text':''.join(c['text'] for c in chs),'chars':chs,
          'fonts':[c['fontname'].split('+')[-1] for c in chs],'size':round(max(c['size'] for c in chs),1)})
    return res


def segs(l, gap=6.0):
    """divide una línea latina en segmentos separados por espacios anchos (cesura del verso)"""
    out=[];cur=''
    prev=None
    for c in sorted(l['chars'], key=lambda c:c['x0']):
        if prev is not None and c['x0']-prev>gap and cur.strip(): out.append(cur.strip()); cur=''
        cur+=c['text']; prev=c['x1']
    if cur.strip(): out.append(cur.strip())
    return [re.sub(r'\s*\[\d+\]\s*$','',s) for s in out if re.sub(r'\s*\[\d+\]\s*$','',s).strip()]

def kind(l):
    ben=any('Bengkeys' in f for f in l['fonts']); s=l['size']; t=l['text'].strip()
    bf=sum('Bold' in f for f in l['fonts'])/max(len(l['fonts']),1)
    if ben and s>=13: return 'section_ben'
    if ben: return 'song_num_ben' if (l['x1']-l['x0'])<45 else 'bengali'
    if s>=13: return 'section_rom'
    if s==8.0: return 'nota_pie'
    if re.fullmatch(r'\(\d+\)',t) and s>=10.2: return 'song_num'
    if s>=10.2 and bf>0.5: return 'translit'
    if s<=9.2: return 'small'
    return 'prosa'

MODO=['archivo']; DEST=['.']; SLUG=['']

def extraer(sec, modo='archivo', dest='.'):
    """Extrae una seccion completa y devuelve su diccionario."""
    MODO[0]=modo; DEST[0]=dest; SLUG[0]=sec['slug']
    P0, P1 = sec['p0'], sec['p1']
    print('SECCION', sec['rom'], 'paginas', P0, 'a', P1)
    rasterizar(P0, P1)
    stream=[]
    for pno in range(P0,P1+1):
        for l in get_lines(pdf.pages[pno-1]):
            if l['top']<45: continue
            l['kind']=kind(l); stream.append(l)

    open_w=False; esperando=False
    cierra=lambda t: bool(re.search(MK_T+r'\s*$', t.rstrip()))
    for l in stream:
        k=l['kind']; t=l['text']
        if k=='translit':
            open_w=False; esperando=cierra(t); continue
        if k not in ('small','prosa'):
            open_w=False; esperando=False; continue
        if open_w:
            l['kind']='wbw'; open_w=not cierra(t); continue
        if t.count('–')>=2 and (k=='small' or esperando):
            l['kind']='wbw'; open_w=not cierra(t); esperando=False
        else:
            l['kind']='prosa'; open_w=False
            if t.strip(): esperando=False

    # --- párrafos dentro de la prosa ---
    def bold_after_marker(l):
        m=re.match(r'^'+MK_P+r'\s*',l['text'])
        if not m: return False
        cs=[c for c in l['chars'] if c['text'].strip()][m.end():m.end()+4]
        return bool(cs) and sum('Bold' in c['fontname'] for c in cs)>=2

    RIGHT=308.0
    def paragraphs(lines):
        paras=[];cur=None;prev=None
        for l in lines:
            allbold=all('Bold' in f for f in l['fonts'] if f)
            cita=allbold and l['x0']>44
            brk = (cur is None or re.match(r'^'+MK_P,l['text']) or cita!=cur['cita']
                   or (prev and prev['x1']<RIGHT-12))
            if brk:
                cur={'lines':[l],'cita':cita,'x0':l['x0'],'boldmark':bold_after_marker(l)}
                paras.append(cur)
            else: cur['lines'].append(l)
            prev=l
        return paras

    def join(lines):
        out=''
        for l in lines:
            t=l['text'].rstrip()
            if out.endswith('-') and not out.endswith(' -'): out=out[:-1]+t.lstrip()
            else: out=(out+' '+t.lstrip()).strip()
        return re.sub(r'\s+',' ',out)

    def ben_num(t):
        m=re.search(r'<([^<>]{1,4})<\s*$',t.strip())
        if not m: return None
        d=''.join(DIG.get(c,'') for c in m.group(1))
        return int(d) if d else None

    # --- agrupar en bloques homogéneos ---
    blocks=[];
    for l in stream:
        k='prosa' if l['kind'] in ('prosa','nota_pie') else l['kind']
        if blocks and blocks[-1]['k']==k and k not in ('song_num','song_num_ben','section_rom','section_ben'):
            blocks[-1]['lines'].append(l)
        else: blocks.append({'k':k,'lines':[l]})

    songs=[];cur=None;pending_ben=[]
    def newsong(n):
        return {'num':n,'versos':{}, 'notas':[]}
    def V(s,n):
        return s['versos'].setdefault(n,{'n':n,'ben':[],'tr':[],'wbw':'','trad':'',
                                         'wbw_rango':None,'trad_rango':None,'notas':[]})

    for b in blocks:
        k=b['k']
        if k=='song_num_ben': pending_ben=[]; continue
        if k=='song_num':
            cur=newsong(int(re.sub(r'\D','',b['lines'][0]['text']))); songs.append(cur)
            for n,ls in pending_ben: 
                if n: V(cur,n)['ben']=ls
            pending_ben=[]; continue
        if k=='bengali':
            groups=[];g=[]
            for l in b['lines']:
                g.append(l); n=ben_num(l['text'])
                if n is not None: groups.append((n,g)); g=[]
            if g: groups.append((None,g))
            if cur is None: pending_ben+=groups; continue
            for n,ls in groups:
                if n and not V(cur,n)['ben']: V(cur,n)['ben']=ls
                elif n: pending_ben.append((n,ls))
            continue
        if cur is None: continue
        if k=='translit':
            g=[]
            for l in b['lines']:
                g.append(l); m=re.search(r'\[(\d+)\]',l['text'])
                if m:
                    V(cur,int(m.group(1)))['tr']=[segs(x) for x in g]; g=[]
        elif k=='wbw':
            g=[]
            for l in b['lines']:
                g.append(l); m=re.search(MK_T+r'\s*$',l['text'].rstrip())
                if m:
                    r=rango(m)
                    v=V(cur,r[-1]); v['wbw']=re.sub(MK_T+r'\s*$','',join(g)).strip()
                    v['wbw_rango']=r if len(r)>1 else None
                    for n in r: V(cur,n)
                    g=[]
        elif k=='prosa':
            for p in paragraphs(b['lines']):
                txt=join(p['lines'])
                m=re.match(r'^'+MK_P+r'\s*',txt)
                if p['cita']:
                    cur['notas'].append({'tipo':'cita','texto':[x['text'].strip() for x in p['lines']]})
                elif m and not p['boldmark'] and not V(cur,rango(m)[-1])['trad']:
                    r=rango(m); v=V(cur,r[-1])
                    v['trad']=txt[m.end():]; v['trad_rango']=r if len(r)>1 else None
                    for n in r: V(cur,n)
                else:
                    verso=rango(m)[0] if m else None
                    cur['notas'].append({'tipo':'nota','verso':verso,'texto':txt[m.end():] if m else txt})

    for s in songs:
        vs=sorted(s['versos'])
        cub_w={n for v in s['versos'].values() for n in (v['wbw_rango'] or [])}
        cub_s={n for v in s['versos'].values() for n in (v['trad_rango'] or [])}
        falt=[f"{n}:{'B' if not s['versos'][n]['ben'] else ''}{'T' if not s['versos'][n]['tr'] else ''}{'W' if not s['versos'][n]['wbw'] and n not in cub_w else ''}{'S' if not s['versos'][n]['trad'] and n not in cub_s else ''}" for n in vs]
        huecos=[f for f in falt if len(f)>2]
        print('  cancion',s['num'],'versos',vs[0],'a',vs[-1],'(%d)'%len(vs),
              ('| HUECOS '+str(huecos)) if huecos else '')

    # ================== recortes bengalíes + JSON ==================
    from PIL import Image, ImageOps
    import os, base64, io, re as _re
    DPI=300; SC=DPI/72.0
    imgcache={}
    def page_img(n):
        if n not in imgcache: imgcache[n]=Image.open(f'pages300/p-{n:03d}.png').convert('L')
        return imgcache[n]

    # límites verticales por vecindad: cada línea bengalí se corta a mitad de camino de la contigua
    BLIM={}
    _bypage={}
    for _l in stream:
        if _l['kind']=='bengali': _bypage.setdefault(_l['page'],[]).append(_l)
    for _pg,_ls in _bypage.items():
        _ls.sort(key=lambda x:x['top'])
        for _i,_l in enumerate(_ls):
            _prev=_ls[_i-1] if _i>0 else None
            _next=_ls[_i+1] if _i<len(_ls)-1 else None
            _t=(_prev['bottom']+_l['top'])/2 if _prev and _l['top']-_prev['bottom']<9 else _l['top']-4.5
            _b=(_l['bottom']+_next['top'])/2 if _next and _next['top']-_l['bottom']<9 else _l['bottom']+4.5
            BLIM[id(_l)]=(_t,_b)

    def crop_mask(l, pad=2.5, out=None):
        im=page_img(l['page']); SCx=SC
        win_t=(l['top']-7)*SCx; win_b=(l['bottom']+7)*SCx
        box=(int((l['x0']-3)*SCx), int(win_t), int((l['x1']+3)*SCx), int(win_b))
        c=ImageOps.autocontrast(im.crop(box))
        alpha=ImageOps.invert(c); px=alpha.load(); W,H=alpha.size
        rows=[sum(px[x,y] for x in range(0,W,2)) for y in range(H)]
        mx=max(rows) or 1; thr=mx*0.012
        cen=int((((l['top']+l['bottom'])/2)*SCx - win_t))
        cen=max(0,min(H-1,cen))
        cap_t=int((l['top']-5.5)*SCx - win_t); cap_b=int((l['bottom']+5.5)*SCx - win_t)
        def edge(step, cap):
            y=cen; gap=0; last=cen
            while 0<=y<H:
                if rows[y]>thr: last=y; gap=0
                else:
                    gap+=1
                    if gap>=3: break
                if (step<0 and y<cap) or (step>0 and y>cap): break
                y+=step
            return last
        t=max(0, edge(-1,cap_t)-3); b=min(H, edge(1,cap_b)+4)
        alpha=alpha.crop((0,t,W,b))
        rgba=Image.new('RGBA', alpha.size, (0,0,0,0)); rgba.putalpha(alpha)
        if MODO[0]=='archivo':
            nom=f"{l['page']:03d}-{int(l['top']*10):05d}.png"
            ruta=os.path.join(DEST[0], 'recortes', SLUG[0])
            os.makedirs(ruta, exist_ok=True)
            rgba.save(os.path.join(ruta, nom), 'PNG', optimize=True)
            return {'w':alpha.size[0],'h':alpha.size[1],'src':f'recortes/{SLUG[0]}/{nom}'}
        buf=io.BytesIO(); rgba.save(buf,'PNG',optimize=True)
        return {'w':alpha.size[0],'h':alpha.size[1],'png':base64.b64encode(buf.getvalue()).decode()}

    def parse_wbw(s):
        items=[]
        for part in s.split(';'):
            part=part.strip()
            if not part: continue
            if '–' not in part: 
                if items: items[-1]['gloss']+='; '+part
                continue
            term,gloss=part.split('–',1)
            term=term.strip(); var=None
            m=_re.match(r'^(.*?)\s*\(([^)]*)\)\s*$', term)
            if m: term,var=m.group(1).strip(), m.group(2).strip()
            items.append({'t':term,'v':var,'gloss':gloss.strip()})
        return items

    data={'obra':'Śaraṇāgati','comentario':'Śrī Laghu-chandrikā-bhāṣya',
          'seccion':{'ben':None,'rom':sec['rom'],'es':sec['es'],'slug':sec['slug'],
                     'orden':sec['orden'],'paginas':[P0,P1]},'canciones':[]}
    for b in blocks:
        if b['k']=='section_ben': data['seccion']['ben']=crop_mask(b['lines'][0], 3)
        if b['k']=='section_rom' and data['seccion']['ben'] and not data['seccion'].get('_done'):
            data['seccion']['_done']=True

    for s in songs:
        out={'n':s['num'],'versos':[],'notas':s['notas']}
        for n in sorted(s['versos']):
            v=s['versos'][n]
            out['versos'].append({
                'n':n,
                'pagina':(v['ben'][0]['page'] if v['ben'] else None),
                'ben':[crop_mask(l) for l in v['ben']],
                'legacy':[l['text'] for l in v['ben']],
                'tr':v['tr'],
                'wbw':parse_wbw(v['wbw']),
                'wbw_rango':v['wbw_rango'],
                'trad':v['trad'],
                'trad_rango':v['trad_rango'],
            })
        out['titulo']=' '.join(out['versos'][0]['tr'][0]).rstrip(',') if out['versos'] else ''
        data['canciones'].append(out)

    # adjuntar cada nota al verso que menciona su marcador, no al lugar donde cayó en la página
    data['seccion']['ben']=None
    for c in data['canciones']:
        byn={v['n']:v for v in c['versos']}
        for v in c['versos']: v['coment']=[]
        act=1
        for nota in c['notas']:
            if nota['tipo']=='cita': byn[act]['coment'].append({'t':'cita','x':nota['texto']})
            else:
                if nota.get('verso'): act=nota['verso']
                if act in byn: byn[act]['coment'].append({'t':'nota','x':nota['texto']})
        del c['notas']

    os.makedirs(os.path.join(DEST[0], 'json'), exist_ok=True)
    salida=os.path.join(DEST[0], 'json', sec['slug']+'.json')
    json.dump(data, open(salida,'w'), ensure_ascii=False)
    nlin=sum(len(v['ben']) for c in data['canciones'] for v in c['versos'])
    print('  JSON', round(os.path.getsize(salida)/1024,1),'KB |',
          len(data['canciones']),'canciones |',
          sum(len(c['versos']) for c in data['canciones']),'versos |', nlin,'lineas bengalies')
    return data


if __name__ == '__main__':
    import sys
    from secciones import SECCIONES, POR_SLUG
    dest = os.environ.get('DEST', 'sitio')
    pedidas = sys.argv[1:] or [s['slug'] for s in SECCIONES if s['canciones']]
    for slug in pedidas:
        extraer(POR_SLUG[slug], modo='archivo', dest=dest)
