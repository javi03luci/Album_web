#!/usr/bin/env python3
"""
Generador del álbum de viajes · todo se decide con CARPETAS.

    fotos/
      2026/                      <- año
        Italia/                  <- viaje   -> URL  /2026/italia/
          Taormina/              <- ciudad (opcional)
            foto1.jpg
          Palermo/
          foto_suelta.jpg        <- fotos del viaje sin ciudad concreta
          portada_atardecer.jpg  <- (opcional) la que empiece por "portada" es la portada
          fechas.txt             <- (opcional) texto de fecha, p. ej. "12–19 de julio"
          frase.txt              <- (opcional) frase que aparece al abrir el álbum

Uso:  python herramientas/build.py            (genera la web en _web/)
      python herramientas/build.py --salida X (la usa GitHub Actions)

Requisitos: pip install pillow pillow-heif
"""
import argparse, hashlib, json, os, re, shutil, sys, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("Aviso: pillow-heif no instalado; las fotos .HEIC se saltarán.")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
EXT = ('.jpg', '.jpeg', '.heic', '.heif', '.png', '.webp')
GRANDE, MINI = 1600, 560
CAL_G, CAL_M = 74, 64


# ---------------------------------------------------------------- utilidades
def slugify(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-') or 'viaje'


def cargar_json(ruta, defecto):
    try:
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defecto


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, sort_keys=True)


def leer_txt(ruta):
    try:
        with open(ruta, encoding='utf-8-sig') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ''


def es_foto(nombre):
    return nombre.lower().endswith(EXT) and not nombre.startswith(('.', '._'))


# ---------------------------------------------------------------- lectura de fotos
def _dms(v, ref):
    try:
        d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
        return -d if ref in ('S', 'W') else d
    except Exception:
        return None


def leer_info(ruta):
    """Tamaño, hora (solo para ordenar) y GPS (solo como reserva para el mapa)."""
    r = {}
    with Image.open(ruta) as im:
        ex = im.getexif()
        w, h = im.size
        if ex.get(274) in (5, 6, 7, 8):
            w, h = h, w
        r['w'], r['h'] = w, h
        sub = ex.get_ifd(0x8769)
        f = sub.get(36867) or sub.get(36868) or ex.get(306)
        if isinstance(f, str):
            try:
                r['t'] = datetime.strptime(f.strip('\x00 ')[:19], '%Y:%m:%d %H:%M:%S').isoformat()
            except ValueError:
                pass
        g = ex.get_ifd(0x8825)
        if g and 2 in g and 4 in g:
            lat, lon = _dms(g[2], g.get(1)), _dms(g[4], g.get(3))
            if lat is not None and lon is not None and (abs(lat) > 1e-6 or abs(lon) > 1e-6):
                r['gps'] = [round(lat, 3), round(lon, 3)]
    return r


def procesar_imagen(args):
    src, dst_g, dst_m = args
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
            for dst, lado, q in ((dst_g, GRANDE, CAL_G), (dst_m, MINI, CAL_M)):
                if os.path.exists(dst):
                    continue
                c = im.copy()
                c.thumbnail((lado, lado), Image.LANCZOS)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                c.save(dst + '.tmp', 'WEBP', quality=q, method=5)   # sin metadatos
                os.replace(dst + '.tmp', dst)
        return None
    except Exception as e:
        return f"{src}: {e}"


def color_medio(ruta):
    with Image.open(ruta) as im:
        r, g, b = im.convert('RGB').resize((1, 1), Image.BOX).getpixel((0, 0))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------- ubicaciones para el mapa
class Ubicaciones:
    """1º ubicaciones.json (editable)  2º nombre buscado en OpenStreetMap  3º GPS de las fotos."""

    def __init__(self, ruta_fija, ruta_auto, online=True):
        self.fija = cargar_json(ruta_fija, {})
        self.ruta_auto = ruta_auto
        self.auto = cargar_json(ruta_auto, {})
        self.online = online
        self.ultima = 0

    def _buscar(self, texto):
        if texto in self.auto:
            return self.auto[texto]
        if not self.online:
            return None
        espera = 1.1 - (time.time() - self.ultima)
        if espera > 0:
            time.sleep(espera)
        self.ultima = time.time()
        url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(
            {'q': texto, 'format': 'json', 'limit': 1, 'accept-language': 'es'})
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'album-de-viajes/1.0 (GitHub Pages personal)'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.load(resp)
            pos = [round(float(res[0]['lat']), 2), round(float(res[0]['lon']), 2)] if res else None
        except Exception as e:
            print(f"  (no se pudo buscar '{texto}' en el mapa: {e})")
            return None
        self.auto[texto] = pos
        guardar_json(self.ruta_auto, self.auto)
        return pos

    def de(self, clave, consultas, gps):
        if clave in self.fija:
            return self.fija[clave], 'manual'
        for q in consultas:
            p = self._buscar(q)
            if p:
                return p, 'nombre'
        if gps:
            return [round(sum(a for a, b in gps) / len(gps), 2), round(sum(b for a, b in gps) / len(gps), 2)], 'gps'
        return None, None


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fotos', default=os.path.join(RAIZ, 'fotos'))
    ap.add_argument('--salida', default=os.path.join(RAIZ, '_web'))
    ap.add_argument('--cache', default=None, help='carpeta de caché (por defecto, dentro de la salida)')
    ap.add_argument('--procesos', type=int, default=max(1, os.cpu_count() or 2))
    ap.add_argument('--sin-internet', action='store_true')
    a = ap.parse_args()

    sitio = cargar_json(os.path.join(RAIZ, 'sitio.json'), {'titulo': 'Nuestros viajes', 'subtitulo': ''})
    cache_dir = a.cache or os.path.join(a.salida, '.cache')
    cache_ruta = os.path.join(cache_dir, 'info_fotos.json')
    cache = cargar_json(cache_ruta, {})
    ubic = Ubicaciones(os.path.join(RAIZ, 'ubicaciones.json'), os.path.join(cache_dir, 'ubicaciones_auto.json'),
                       online=not a.sin_internet)
    avisos = []

    if not os.path.isdir(a.fotos):
        sys.exit(f"No existe la carpeta de fotos: {a.fotos}")

    # 1) Recorrer  fotos/AÑO/VIAJE/[CIUDAD/]
    viajes = []
    for anio in sorted(os.listdir(a.fotos)):
        ra = os.path.join(a.fotos, anio)
        if not os.path.isdir(ra) or anio.startswith(('.', '_')):
            continue
        if not re.fullmatch(r'\d{4}', anio):
            avisos.append(f"'{anio}' no es un año (4 cifras): se ignora.")
            continue
        for nombre in sorted(os.listdir(ra)):
            rv = os.path.join(ra, nombre)
            if not os.path.isdir(rv) or nombre.startswith(('.', '_')):
                continue
            fotos = []
            for dp, dns, fs in os.walk(rv):
                dns[:] = sorted(d for d in dns if not d.startswith(('.', '_')))
                relv = os.path.relpath(dp, rv)
                ciudad = '' if relv == '.' else relv.replace('\\', '/').split('/')[0]
                for f in sorted(fs):
                    if es_foto(f):
                        fotos.append({'src': os.path.join(dp, f), 'ciudad': ciudad, 'nombre': f})
            if fotos:
                viajes.append({'anio': int(anio), 'titulo': nombre, 'slug': slugify(nombre), 'dir': rv, 'fotos': fotos})

    # 2) Información de cada foto (con caché) y duplicados exactos
    leidas = 0
    for v in viajes:
        unicos, vistos = [], set()
        for f in v['fotos']:
            rel = os.path.relpath(f['src'], a.fotos).replace('\\', '/')
            clave = f"{rel}|{os.path.getsize(f['src'])}"
            if clave not in cache:
                try:
                    cache[clave] = leer_info(f['src'])
                    with open(f['src'], 'rb') as fh:
                        cache[clave]['md5'] = hashlib.md5(fh.read()).hexdigest()
                except Exception as e:
                    avisos.append(f"No se pudo leer {rel}: {e}")
                    continue
                leidas += 1
                if leidas % 300 == 0:
                    guardar_json(cache_ruta, cache)
            f.update(cache[clave])
            f['rel'] = rel
            if f['md5'] in vistos:
                continue
            vistos.add(f['md5'])
            unicos.append(f)
        v['fotos'] = unicos
    guardar_json(cache_ruta, cache)

    # 3) Copias web (sin metadatos)
    trabajos, usados = [], set()
    for v in viajes:
        for f in v['fotos']:
            h = hashlib.md5(f['rel'].encode()).hexdigest()[:12]
            f['g'] = f"fotos/{v['anio']}/{v['slug']}/g/{h}.webp"
            f['m'] = f"fotos/{v['anio']}/{v['slug']}/m/{h}.webp"
            usados.update((f['g'], f['m']))
            dg, dm = os.path.join(a.salida, f['g']), os.path.join(a.salida, f['m'])
            if not (os.path.exists(dg) and os.path.exists(dm)):
                trabajos.append((f['src'], dg, dm))
    if trabajos:
        print(f"Creando {len(trabajos)} copias web...", flush=True)
        with ProcessPoolExecutor(a.procesos) as ex:
            for i, err in enumerate(ex.map(procesar_imagen, trabajos, chunksize=4), 1):
                if err:
                    avisos.append(err)
                if i % 200 == 0:
                    print(f"  {i}/{len(trabajos)}", flush=True)

    # 4) Datos de cada viaje
    datos = []
    for v in viajes:
        fs = [f for f in v['fotos'] if os.path.exists(os.path.join(a.salida, f['m']))]
        if not fs:
            continue
        orden_f = lambda f: (f.get('t') or '9999', f['nombre'])
        ciudades = []
        for f in sorted(fs, key=orden_f):
            if f['ciudad'] and f['ciudad'] not in ciudades:
                ciudades.append(f['ciudad'])
        secciones = [{'titulo': c, 'fotos': sorted([f for f in fs if f['ciudad'] == c], key=orden_f)} for c in ciudades]
        sueltas = sorted([f for f in fs if not f['ciudad']], key=orden_f)
        if sueltas:
            secciones.append({'titulo': 'Otros momentos' if ciudades else '', 'fotos': sueltas})

        # ubicación en el mapa
        lugares = []
        for c in ciudades:
            gps = [f['gps'] for f in fs if f['ciudad'] == c and f.get('gps')]
            pos, _ = ubic.de(f"{v['anio']}/{v['titulo']}/{c}", [f"{c}, {v['titulo']}", c], gps)
            lugares.append({'nombre': c, 'pos': pos, 'n': sum(1 for f in fs if f['ciudad'] == c)})
        clave_v = f"{v['anio']}/{v['titulo']}"
        if clave_v in ubic.fija:
            pos_v, origen = ubic.fija[clave_v], 'manual'
        elif any(l['pos'] for l in lugares):
            pos_v, origen = max((l for l in lugares if l['pos']), key=lambda l: l['n'])['pos'], 'ciudad'
        else:
            pos_v, origen = ubic.de(clave_v, [v['titulo']], [f['gps'] for f in fs if f.get('gps')])
        if not pos_v:
            avisos.append(f"[{clave_v}] no sé dónde está: añádelo a ubicaciones.json para que salga en el mapa.")

        # portada: la foto cuyo nombre empiece por "portada"; si no, una horizontal
        port = next((f for f in fs if f['nombre'].lower().startswith('portada')), None)
        if not port:
            orden = sorted(fs, key=orden_f)
            horiz = [f for f in orden if f['w'] > f['h'] * 1.2] or orden
            port = horiz[len(horiz) // 3]

        fechas_txt = leer_txt(os.path.join(v['dir'], 'fechas.txt'))
        datos.append({
            'titulo': v['titulo'], 'slug': v['slug'], 'anio': v['anio'], 'url': f"{v['anio']}/{v['slug']}/",
            'fechas': fechas_txt or str(v['anio']), 'fechas_propias': bool(fechas_txt),
            'frase': leer_txt(os.path.join(v['dir'], 'frase.txt')),
            'lugares': [l['nombre'] for l in lugares], 'pos': pos_v, 'origen_pos': origen,
            'n': len(fs), 'orden': min((f.get('t') or '9999') for f in fs),
            'portada': {'g': port['g'], 'm': port['m'], 'w': port['w'], 'h': port['h'],
                        'color': color_medio(os.path.join(a.salida, port['m']))},
            'secciones': [{'titulo': s['titulo'], 'fotos': [
                {'g': f['g'], 'm': f['m'], 'w': f['w'], 'h': f['h']} for f in s['fotos']]} for s in secciones],
        })

    # mismo año y mismo nombre de URL: se diferencian
    vistas = {}
    for d in datos:
        if d['url'] in vistas:
            vistas[d['url']] += 1
            d['slug'] += f"-{vistas[d['url']]}"
            d['url'] = f"{d['anio']}/{d['slug']}/"
            avisos.append(f"Dos viajes con URL parecida en {d['anio']}: '{d['titulo']}' usa /{d['url']}")
        else:
            vistas[d['url']] = 1
    datos.sort(key=lambda d: (d['anio'], d['orden']), reverse=True)

    # 5) Páginas
    plant = os.path.join(RAIZ, 'plantilla')
    shutil.copytree(os.path.join(plant, 'assets'), os.path.join(a.salida, 'assets'), dirs_exist_ok=True)
    open(os.path.join(a.salida, '.nojekyll'), 'w').close()

    def js(o):
        return json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    def esc(t):
        return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;')

    def plantilla(nombre):
        with open(os.path.join(plant, nombre), encoding='utf-8') as f:
            return f.read()

    resumen = [{k: d[k] for k in ('titulo', 'url', 'anio', 'fechas', 'lugares', 'pos', 'origen_pos', 'n', 'portada')}
               for d in datos]
    datos_sitio = js({'sitio': sitio, 'viajes': resumen})
    for nombre in ('index.html', 'enlaces.html'):
        html = (plantilla(nombre).replace('{{TITULO}}', esc(sitio.get('titulo')))
                .replace('{{SUBTITULO}}', esc(sitio.get('subtitulo'))).replace('{{DATOS}}', datos_sitio))
        with open(os.path.join(a.salida, nombre), 'w', encoding='utf-8') as f:
            f.write(html)

    t_album = plantilla('album.html')
    paginas = set()
    for d in datos:
        dest = os.path.join(a.salida, d['url'])
        os.makedirs(dest, exist_ok=True)
        desc = ' · '.join(x for x in [', '.join(d['lugares'][:3]), d['fechas']] if x)
        html = (t_album.replace('{{TITULO}}', esc(d['titulo'])).replace('{{SITIO}}', esc(sitio.get('titulo')))
                .replace('{{DESCRIPCION}}', esc(desc)).replace('{{PORTADA}}', '../../' + d['portada']['g'])
                .replace('{{COLOR}}', d['portada']['color']).replace('{{DATOS}}', js(d)))
        with open(os.path.join(dest, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        paginas.add(os.path.normpath(os.path.join(dest, 'index.html')))

    # 6) Limpieza: fotos y páginas de viajes que ya no existen en las carpetas
    borradas = 0
    for dp, dns, fs in os.walk(a.salida, topdown=False):
        rel = os.path.relpath(dp, a.salida).replace('\\', '/')
        if rel.startswith(('.cache', 'assets')):
            continue
        for f in fs:
            p = os.path.join(dp, f)
            r = os.path.relpath(p, a.salida).replace('\\', '/')
            if (r.startswith('fotos/') and r not in usados) or \
               (re.match(r'\d{4}/', r) and os.path.normpath(p) not in paginas):
                os.remove(p)
                borradas += 1
        if rel != '.' and not os.listdir(dp):
            os.rmdir(dp)
    if borradas:
        print(f"Eliminados {borradas} archivos de fotos o viajes que ya no están en las carpetas.")

    # 7) Informe
    print(f"\nListo: {len(datos)} viajes, {sum(d['n'] for d in datos)} fotos -> {a.salida}")
    for d in datos:
        print(f"  /{d['url']:<30} {d['n']:>4} fotos  {', '.join(d['lugares']) or '(sin ciudades)'}"
              f"  [mapa: {d['origen_pos'] or 'NO'}]")
    if avisos:
        print("\nAvisos:")
        for x in avisos:
            print("  - " + x)


if __name__ == '__main__':
    main()
