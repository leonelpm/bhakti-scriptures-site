# Śaraṇāgati

Lectura del Śaraṇāgati de Bhaktivinod Ṭhākur en la edición española del
Śrī Chaitanya Sāraswat Maṭh, con el comentario Śrī Laghu-chandrikā-bhāṣya.

Sitio estático. Cada sección es una página que se abre sola, sin frameworks ni
build. El texto va escrito en el documento, no se arma en el navegador. Los
controles de lectura siguen siendo CSS con casillas y `:has()`.

Ya no es un sitio sin JavaScript. En el `<head>` de cada página van diez líneas
que guardan el tamaño de letra y el tema en el navegador y los restauran antes de
pintar, para que no se pierdan al cambiar de sección ni parpadee el tema claro al
entrar. Con JavaScript desactivado no pasa nada: la página arranca en los valores
por defecto y las casillas y el botón de tema siguen funcionando, porque quien
lleva el tema son los radios y el script solo los recuerda.

## Estructura

    index.html         secciones y el índice de kīrtan por primer verso
    NN-seccion.html    una página por sección, en el orden del libro
    estilo.css         hoja compartida
    recortes/          recortes del bengalí impreso, capa de auditoría
    json/              salida del extractor, no hace falta para leer

## Interfaz

- **Por defecto: tema claro y letra grande.** El claro es el valor de `:root` y
  el oscuro solo entra cuando se pide, así que el sistema en oscuro ya no arrastra
  la página. La letra grande también es la de `:root`, y «menor» y «medio» son los
  que anulan. Así lo primero que se pinta ya es lo que toca, sin parpadeo.
- **Configuración** es la pestaña desplegable de debajo de la barra. La barra y
  ella van dentro de un mismo bloque pegajoso (`.top`), así que acompañan al
  scroll juntas sin tener que acertar a mano dónde acaba una y empieza la otra.
  El panel se abre por encima del texto, sin empujarlo. Lleva las capas y el
  tamaño de letra.
- **El tema** no está en Configuración: es el botón de la barra. Enseña la luna
  cuando estás en claro y el sol cuando estás en oscuro, y mueve los mismos tres
  radios de siempre (día, noche, automático), que siguen en el documento aunque no
  se vean. Por eso no puede contradecirlos. La portada lleva el mismo botón, en
  una barra estrecha, y obedece al tema guardado igual que las secciones.
- **El botón de subir al principio** va fijo abajo a la derecha en todas las
  páginas. Es un enlace a `#`, así que funciona sin JavaScript; donde hay línea de
  tiempo de scroll asoma al alejarse de la cabecera.
- **El título y el subtítulo de la barra** miden el triple de lo que medían
  (`--brandT`, `--brandS`). En pantalla estrecha bajan con el ancho, porque al
  triple no caben junto a los botones; ahí la barra se queda solo con el enlace al
  índice y el resto de la navegación se usa desde el pie.
- **El cuerpo del texto no lleva ninguna línea divisoria.** Las capas se
  distinguen por el blanco y por los rótulos: `--sep1` entre el bengalí y la
  transliteración, que son la misma capa; `--sep2` antes de cada rótulo
  (TRADUCCIÓN, PALABRA POR PALABRA, COMENTARIO); `--sep3` entre versos; `--sep4`
  entre canciones. Cada escalón tiene que leerse mayor que el de dentro: si se
  tocan los valores, hay que mirarlos juntos.
  El único filete que queda es el de las citas del comentario, en color de
  acento. Se queda porque no separa capas: marca el verso ajeno que el
  comentarista trae de fuera, y es lo único que lo distingue de su propia prosa.
- **El índice lateral de canciones** va fijo, fuera del flujo, para que la columna
  de lectura quede centrada en la pantalla y no en el hueco que sobra. Aparece a
  partir de 1180 px. El número de cada fila es **el de la canción en el libro**,
  no un conteo de la página: por eso Ātma-nivedanātmikā empieza en la 6. El libro
  numera del 1 al 32 de Maṅgalācharaṇa a Ānukūlyātmikā y vuelve a empezar en
  Bhajana-lālasā, que va del 1 al 13 y sigue en Siddhi-lālasā del 14 al 16. El punto de ruptura no es libre: sale de la cuenta que hace
  `verificar.py`, que recorre de 1180 a 3840 px y comprueba que el índice no pisa
  el texto ni el número de verso. Con el corte anterior, 980 px, se montaba.

## Regenerar

Hace falta `python3` con `pdfplumber`, `Pillow`, `beautifulsoup4` y `tinycss2`, y
un rasterizador: `pdftoppm` (poppler) o, si no está, `pypdfium2`, que llega por
pip. **Los recortes publicados están hechos con poppler**; pypdfium2 da el mismo
texto pero recortes ±1 px distintos, y en algún caso se come un descendente. Si
vas a regenerar `recortes/`, instala poppler:

    conda install -c conda-forge poppler

Con el PDF en la raíz (`SARANAGATI.pdf`, ignorado por git) y `DEST` apuntando a
la carpeta publicable:

    DEST=. python3 scripts/extraer_pdf.py                  todas las secciones con canciones
    DEST=. python3 scripts/extraer_pdf.py dainyatmika      solo una
    DEST=. python3 scripts/extraer_kirtan.py               el índice por primer verso
    DEST=. python3 scripts/generar_sitio.py                monta index.html y las páginas

`extraer_pdf.py` rasteriza a 300 DPI en `pages300/` solo las páginas que falten.
`pages300/` y `__pycache__/` están ignorados.

Los scripts leen y escriben siempre en UTF-8 y con saltos `\n`, así que la salida
es la misma en Windows y en Linux.

### La capa de recortes

Los recortes del bengalí impreso están **encendidos en todas las secciones**: es
la capa de auditoría y hace falta mientras se revisa el libro capítulo por
capítulo. Cuando termine la revisión se apagan de una vez en todo el sitio con el
interruptor de `generar_sitio.py`:

    CAPA_ORIGINAL=0 DEST=. python3 scripts/generar_sitio.py

o poniendo `CAPA_ORIGINAL = False` en el propio archivo. Apagarla quita los PNG y
también la casilla «Original impreso» de Configuración. Bhajana-lālasā pasa de
148 KB a 125 KB.

## Comprobaciones

Ninguna página se publica sin pasar las tres.

    DEST=. python3 scripts/test_ida_vuelta.py
    DEST=. python3 scripts/generar_sitio.py
    DEST=. python3 scripts/verificar.py

`test_ida_vuelta.py` convierte cada línea de transliteración a bengalí y vuelve
atrás. Hay que pasarlo después de tocar las reglas de `iast2ben.py`. Ahora mismo
coinciden las 525 líneas de las cuatro secciones hechas.

`generar_sitio.py` cuenta versos, líneas, traducciones, glosarios y comentarios en
el HTML ya generado y los compara con el JSON, y no escribe el sitio como «listo»
si algo no cuadra.

`verificar.py` es la comprobación fina, y va sobre el HTML ya escrito en disco, no
sobre lo que el generador cree haber escrito:

- **DOM**: verso a verso, con BeautifulSoup, contra el JSON. Líneas bengalíes,
  recortes, líneas de transliteración, traducción con su rótulo, entradas del
  glosario y piezas del comentario, y que ninguna esté vacía. Una vez se publicó
  una versión en blanco por un campo vacío que nadie contó.
- **HOJA**: que no han vuelto los filetes del cuerpo, que Configuración sigue
  siendo pegajosa y que el índice lateral sigue fuera del flujo.
- **TEMA**: recorre los 18 estados posibles del botón de tema (sistema claro u
  oscuro × `data-th` × radio marcado) resolviendo la cascada de `estilo.css`, y
  comprueba que siempre se ve un icono y solo uno, que es el del tema contrario al
  que hay puesto, y que pulsarlo cambia el tema con y sin JavaScript.
- **PORTADA**: que `index.html` lleva el mismo botón de tema, los mismos radios y
  el mismo guardado que las secciones.
- **ANCHOS**: lee las medidas del índice lateral de la hoja y recorre de 1180 a
  3840 px comprobando que no pisa el texto ni se sale por la izquierda.
- **NAVEGADOR**: abre las páginas en Chromium con `file://`, que es como se miran
  en local, a cuatro anchos y con el sistema en oscuro. Comprueba lo que ninguna
  lectura del HTML puede ver: que los recortes cargan de verdad, que el alto real
  del bloque de arriba coincide con `--topH` (si no, el encabezado de canción se
  esconde detrás de la barra), que no aparece scroll horizontal, que se arranca en
  claro y en grande, y que pulsar la luna pone el tema oscuro e invierte los
  recortes. Se salta sola si no hay playwright:

      pip install playwright && playwright install chromium

## Hecho

| # | Sección | Páginas | Canciones | Versos | Líneas bengalíes |
| --- | --- | --- | --- | --- | --- |
| 01 | Maṅgalācharaṇa | 49–56 | 1 | 7 | 14 |
| 02 | Dainyātmikā | 57–78 | 4 | 25 | 100 |
| 03 | Ātma-nivedanātmikā | 79–124 | 11 | 68 | 190 |
| 08 | Bhajana-lālasā | 195–238 | 13 | 52 | 221 |

Los glosarios y traducciones compartidos cuadran uno a uno con lo impreso: de los
5 marcadores `[N–M]` que hay en el libro en estas cuatro secciones salen 5
glosarios compartidos, y de los 18 `(N–M)` los 5 que abren traducción salen como
traducción compartida y los 13 que abren comentario salen como nota.

## Reglas que salieron de Ātma-nivedanātmikā y Bhajana-lālasā

Cada una vale para todo el libro, no para el caso que la destapó. Después de cada
una se regeneraron las secciones 1 y 2 y su texto no cambió.

- **El adorno del número de canción es corto Y va centrado.** Con la anchura sola,
  el estribillo de Bhajana-lālasā (`hari he!`, `jaya he!`, `prabhu he!`) es corto
  pero arranca en el margen izquierdo, y se tomaba por número: se perdían 11
  líneas bengalíes, una por canción. Los adornos de verdad están centrados a menos
  de 0,05 pt del centro de la caja; los estribillos, a 78.
- **Un `(N)` a principio de línea solo abre párrafo si nombra versos de esta
  canción que aún no tienen traducción.** El comentario está lleno de números
  entre paréntesis que no son versos: la referencia de un śloka partida por el
  salto de línea (`…Śrī Stotra-ratna` / `(49):`) y las enumeraciones (`(5) kampa,
  temblor; (6) vaivarṇya, palidez`). Abrían versos fantasma —el 49 en la canción
  12 de Ātma-nivedanātmikā y el 5 en la canción 12 de Bhajana-lālasā— y se
  llevaban por delante el resto del comentario.
- **Un glosario sigue abierto mientras no cambie el cuerpo.** Los hay a 9 puntos,
  que caen en `small`, y los hay a 9,7, que caen en `prosa` y se confunden con el
  comentario (solo pasa en Maṅgalācharaṇa). Antes seguía tragando cualquier prosa:
  cuando un glosario se partía por un salto de página, se comía entera la
  traducción que venía en medio (canción 6, verso 2).
- **Un glosario partido por un salto de página se junta.** Llega en dos bloques
  con la traducción y el comentario entre medias; lo que queda abierto en un
  bloque sigue en el siguiente.
- **Las marcas combinantes van con la letra anterior.** El chandrabindu sale del
  PDF con anchura cero y la misma x que el glifo siguiente, así que al ordenar la
  línea por x cruzaba el espacio o la raya y se pegaba a la palabra de después.
  Se recoloca por posición, detrás de la letra cuyo borde derecho cae más cerca.
  Esto también arregló siete términos de los glosarios de las secciones 1 y 2, que
  llevaban la marca una letra corrida: `kād̐iyā` → `kā̐diyā`, `yāh̐āra` → `yā̐hāra`,
  `phād̐e` → `phā̐de`, y `duhu` + `̐ambos` → `duhu̐` + `ambos`.
- **Una consonante que se queda sin vocal lleva হসন্ত.** Pasa al final de palabra
  y delante de un guion que sí se imprime. Sin el hasanta la vuelta atrás leía la
  vocal inherente y salía `jagata` por `jagat`, `asata-saṅga` por `asat-saṅga`.
  El libro lo marca igual en la fuente heredada: `jagat` es `ij_`, no `ij`.
- **Una línea sin texto visible no es una línea.** Un glifo de espacio suelto
  formaba su propia línea, entraba como transliteración y metía una línea en
  blanco en el verso (canción 8, verso 5).
- **El recorte impreso va como `<img>`, no como máscara CSS.** Chrome no carga las
  máscaras cuando la página se abre con `file://`, así que la capa de auditoría
  desaparecía entera al mirar el sitio en local y solo se veía publicada. Como el
  recorte es tinta negra sobre nada, en tema oscuro se invierte con `--inv`, que
  se declara junto al resto de colores del tema y no repite la condición.
- **Nada oculto puede ensanchar la página.** El grupo de radios del tema va con
  `.oculto`; en su sitio natural, junto al botón, sus hijos desbordaban por la
  derecha y la página cogía scroll horizontal aunque no se vieran. Va anclado a la
  izquierda del contenedor pegajoso, que ocupa todo el ancho.

## Pendiente

- Secciones 4 a 7 y 9 a 11.
- Secciones 12 a 14, que no siguen el formato de canciones.
- Buscador global. El código está en `generar_html.JS` y la hoja ya lo contempla,
  pero `generar_sitio.py` monta las páginas con `con_buscador=False`.
- Títulos bengalíes de sección, que se solapan con el latino y salen mordidos.
  `extraer_pdf.py` recorta `section_ben` y luego lo tira (`data['seccion']['ben']
  = None`).
- En Vijñapti y Śrī Nāma-māhātmya no se detecta ningún número de canción impreso.
  Hay que mirar si esas dos secciones no los llevan o si `kind()` necesita otra
  regla, antes de extraerlas.
- Las notas de comentario con marcador de rango, como `(1–4) Esta canción se basa
  en el primer verso del Śrī Upadeśāmṛta`, se cuelgan del primer verso del rango.
  En el libro van detrás del último. Es colocación, no pérdida.
- El archivo se llama `README.md` y no `LEEME.md` para que GitHub lo enseñe en la
  portada del repositorio.
