# Nuestros viajes · álbum web

Un álbum de viajes que se construye **solo a partir de carpetas de fotos**.
Subes las fotos a GitHub y, en un par de minutos, la web se actualiza sola:
mapa, portadas, galerías y una URL fija por viaje para las etiquetas NFC.

---

## Cómo se organizan las carpetas

```
fotos/
└── 2026/                         ← AÑO (4 cifras)
    ├── Italia/                   ← VIAJE  →  web: /2026/italia/
    │   ├── Taormina/             ← CIUDAD (opcional): una sección del álbum
    │   ├── Palermo/
    │   ├── foto_suelta.jpg       ← fotos del viaje sin ciudad → «Otros momentos»
    │   ├── portada_atardecer.jpg ← la foto cuyo nombre empieza por «portada» es la portada
    │   ├── fechas.txt            ← (opcional) texto de la fecha, p. ej.: 12–19 de julio
    │   └── frase.txt             ← (opcional) una frase al abrir el álbum
    └── Suiza/                    ← viaje sin ciudades: todas las fotos juntas
```

Reglas:

- **Año → viaje → ciudad.** El nombre de cada carpeta es exactamente lo que se ve en la web.
- **Fecha.** Por defecto se muestra el año de la carpeta. Si quieres otro texto
  («Julio de 2026», «Puente de mayo»…), crea `fechas.txt` en la carpeta del viaje.
- **Lugar.** El nombre de la carpeta de la ciudad (o del viaje si no tiene ciudades).
- **Orden.** Dentro de cada carpeta, las fotos se ordenan por la hora en que se hicieron (si la tienen) y si no, por nombre.
- **Portada.** Renombra la foto que quieras para que empiece por `portada`. Si no hay ninguna, se elige una sola.
- **Ocultar** algo sin borrarlo: pon `_` delante del nombre de la carpeta (p. ej. `_Descartes`).
- Formatos: JPG, HEIC (iPhone), PNG y WebP.

**La URL de cada viaje** es `/AÑO/nombre-del-viaje/` (sin tildes ni espacios):
`2026/Italia` → `/2026/italia/`, `2025/Altea y Benidorm` → `/2025/altea-y-benidorm/`.
Si cambias el nombre de la carpeta o del año, **la URL cambia** y habría que regrabar su etiqueta NFC.

---

## 1 · Publicar en GitHub (solo la primera vez)

1. Crea una cuenta en <https://github.com> e instala **GitHub Desktop**
   (<https://desktop.github.com>). Inicia sesión.
2. En GitHub Desktop: **File → Add local repository…** → elige la carpeta
   `Album_web` → pulsa **create a repository**. Nombre: por ejemplo `viajes`.
   Deja *Git ignore* en *None* (ya viene preparado) → **Create repository**.
3. Escribe un resumen («Primera versión») → **Commit to main**.
4. **Publish repository** y **desmarca** «Keep this code private».
   (Subir ~720 MB tarda un rato.)
5. En la web de GitHub, entra en el repositorio → **Settings → Pages** →
   en *Source* elige **GitHub Actions**. No hay que tocar nada más.
6. Ve a la pestaña **Actions**: verás «Publicar álbum» trabajando. La primera
   vez tarda unos 10 minutos (crea las 3.000 copias web). Si salió antes de
   activar Pages y aparece en rojo, pulsa **Run workflow** para relanzarlo.
7. Cuando termine en verde, tu web está en
   **`https://TU-USUARIO.github.io/viajes/`**.

> El repositorio es público: cualquiera con el enlace puede ver las fotos.
> Las copias de `fotos/` ya **no llevan GPS** (las preparé así), y la web
> tampoco. Las fotos que subas a partir de ahora sí llevarán el GPS del móvil
> en el repositorio (no en la web). Las páginas tienen `noindex` para que
> Google no las muestre.

---

## 2 · Añadir o cambiar fotos (el día a día)

**Con GitHub Desktop (lo más cómodo):**
1. Crea las carpetas y copia las fotos dentro de `Album_web/fotos/…` como cualquier carpeta de Windows.
2. Abre GitHub Desktop → **Commit to main** → **Push origin**.
3. En 2–3 minutos está publicado.

**Desde la web de GitHub (sin instalar nada, también desde el móvil):**
1. Entra en el repositorio → carpeta `fotos` → **Add file → Upload files**.
2. Arrastra una **carpeta entera** (por ejemplo `2027/Lisboa/` con sus subcarpetas):
   GitHub respeta la estructura. Límite: 100 archivos y 25 MB por foto en cada subida.
3. Pulsa **Commit changes**. En 2–3 minutos está publicado.

Para borrar o mover fotos, hazlo en las carpetas y vuelve a subir los
cambios: lo que desaparece de las carpetas desaparece de la web.

---

## 3 · Enlaces para las etiquetas NFC

Abre **`https://TU-USUARIO.github.io/viajes/enlaces.html`** (en el móvil):
lista todos los viajes con su URL completa y un botón **Copiar**.

**Grabar una etiqueta** con la app gratuita **NFC Tools** (iPhone o Android):
1. **Escribir** → **Añadir un registro** → **URL / URI** → pega el enlace → OK.
2. **Escribir** y acerca la etiqueta a la parte superior trasera del móvil.
3. Pruébala con el móvil desbloqueado.
4. Opcional: cuando funcione, **bloquéala** (Otros → Bloquear). Es irreversible.

**Qué etiquetas comprar:** NTAG213/215 **«anti-metal» (on-metal)**. Las normales
no funcionan pegadas a un imán o a la nevera.

---

## 4 · Mapa

Cada viaje sale en el mapa donde está su ciudad principal. La ubicación se busca así:
1. **`ubicaciones.json`** (si está ahí, manda): `"2026/Italia/Taormina": [37.85, 15.29]`.
2. Si no, se **busca el nombre de la carpeta** en OpenStreetMap automáticamente.
3. Si no se encuentra, se usa el GPS de las fotos (si lo tienen).

Si un viaje sale en un sitio equivocado o no sale, añade su línea a
`ubicaciones.json` (latitud y longitud se copian de Google Maps: clic derecho
en el lugar → copiar coordenadas). En la pestaña **Actions** de GitHub, el
informe de cada publicación avisa si algún viaje no se pudo situar.

---

## 5 · Otros ajustes

- **Título y subtítulo** de la página principal: `sitio.json`.
- **Diseño:** carpeta `plantilla/` (colores y tipografías al principio de `assets/estilos.css`).
- **Vista previa en tu ordenador** antes de subir: doble clic en `actualizar.bat`
  (necesita Python; crea la carpeta `_web`, que no se sube).

### Qué hace cada cosa

| | |
|---|---|
| `fotos/` | Tus fotos. **Es lo único que necesitas tocar.** |
| `.github/workflows/publicar.yml` | Publica la web automáticamente en cada subida. |
| `herramientas/build.py` | Genera la web a partir de las carpetas. |
| `plantilla/` | Diseño de la portada, el álbum, el mapa y la página de enlaces. |
| `ubicaciones.json` | Posiciones del mapa (opcional, editable). |
| `sitio.json` | Título y subtítulo. |
