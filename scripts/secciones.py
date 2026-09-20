#!/usr/bin/env python3
"""Tabla unica de secciones. Los rangos salen del indice del libro y la ultima
pagina de cada seccion es la anterior al comienzo de la siguiente.
'canciones' en falso marca las tres secciones finales, que no siguen el formato
de canciones numeradas y hay que revisar aparte."""

SECCIONES = [
    dict(orden=1,  slug='mangalacharana',   rom='Maṅgalācharaṇa',              es='Invocación',            p0=49,  p1=56,  canciones=True),
    dict(orden=2,  slug='dainyatmika',      rom='Dainyātmikā',                 es='Humildad',              p0=57,  p1=78,  canciones=True),
    dict(orden=3,  slug='atma-nivedanatmika', rom='Ātma-nivedanātmikā',        es='Auto-sumisión',         p0=79,  p1=124, canciones=True),
    dict(orden=4,  slug='goptritve-varana', rom='Goptṛtve Varaṇa',             es='Aceptación del guardián', p0=125, p1=140, canciones=True),
    dict(orden=5,  slug='visrambhatmika',   rom='Viśrambhātmikā',              es='Confianza',             p0=141, p1=158, canciones=True),
    dict(orden=6,  slug='varjanatmika',     rom='Varjanātmikā',                es='Renuncia',              p0=159, p1=176, canciones=True),
    dict(orden=7,  slug='anukulyatmika',    rom='Ānukūlyātmikā',               es='Aceptación de lo favorable', p0=177, p1=194, canciones=True),
    dict(orden=8,  slug='bhajana-lalasa',   rom='Bhajana-lālasā',              es='Anhelo de servicio',    p0=195, p1=238, canciones=True),
    dict(orden=9,  slug='siddhi-lalasa',    rom='Siddhi-lālasā',               es='Anhelo de perfección',  p0=239, p1=250, canciones=True),
    dict(orden=10, slug='vijnapti',         rom='Vijñapti',                    es='Súplica',               p0=251, p1=258, canciones=True),
    dict(orden=11, slug='nama-mahatmya',    rom='Śrī Nāma-māhātmya',           es='La gloria del Nombre',  p0=259, p1=268, canciones=True),
    dict(orden=12, slug='saranagatera-prarthana', rom='Śaraṇāgatera Prārthanā', es='Oración del rendido',  p0=269, p1=274, canciones=False),
    dict(orden=13, slug='hari-guru-vaisnava-vandana', rom='Hari-Guru-Vaiṣṇava-Vandanā', es='Reverencias', p0=275, p1=284, canciones=False),
    dict(orden=14, slug='ma-muncha',        rom='Mā Muñcha Pañcha-Daśakam',    es='No me abandones',       p0=285, p1=290, canciones=False),
]

INDICE_KIRTAN = (303, 304)   # en el PDF, no en la 307 como decía la nota

POR_SLUG = {s['slug']: s for s in SECCIONES}

def archivo(sec):
    return f"{sec['orden']:02d}-{sec['slug']}.html"

def vecinas(sec):
    i = sec['orden'] - 1
    ant = SECCIONES[i - 1] if i > 0 else None
    sig = SECCIONES[i + 1] if i < len(SECCIONES) - 1 else None
    return ant, sig
