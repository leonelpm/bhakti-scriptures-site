# Śaraṇāgati

Lectura del Śaraṇāgati de Bhaktivinod Ṭhākur en la edición española del
Śrī Chaitanya Sāraswat Maṭh, con el comentario Śrī Laghu-chandrikā-bhāṣya.

Sitio estático. Cada sección es una página que se abre sola, sin frameworks ni
build. Los controles de lectura son CSS con casillas y `:has()`. La única página
con JavaScript será el buscador global, cuando exista.

## Estructura

    indice.html        secciones y el índice de kīrtan por primer verso
    NN-seccion.html    una página por sección, en el orden del libro
    estilo.css         hoja compartida
    recortes/          recortes del bengalí impreso, capa de auditoría
    json/              salida del extractor, no hace falta para leer

## Regenerar

Con el PDF a mano y los scripts del repositorio:

    python3 extraer_pdf.py                 todas las secciones con canciones
    python3 extraer_pdf.py dainyatmika     solo una
    python3 extraer_kirtan.py              el índice por primer verso
    python3 generar_sitio.py               monta indice.html y las páginas

`extraer_pdf.py` rasteriza a 300 DPI en `pages300/` solo las páginas que falten.

## Comprobaciones

    python3 test_ida_vuelta.py

Convierte cada línea de transliteración a bengalí y vuelve atrás. Las 100 líneas
de Dainyātmikā deben coincidir. Hay que pasarlo después de tocar las reglas de
`iast2ben.py`.

`generar_sitio.py` cuenta versos, líneas, glosarios y comentarios en el HTML ya
generado y los compara con el JSON. Ninguna página se publica sin pasar eso.

## Pendiente

- Secciones 3 a 11.
- Secciones 12 a 14, que no siguen el formato de canciones.
- Buscador global.
- Títulos bengalíes de sección, que se solapan con el latino y salen mordidos.
- Caracteres combinantes sueltos en algunos glosarios.
