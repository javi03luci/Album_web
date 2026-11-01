/* Álbum de un viaje: portada, galería por ciudades (carpetas) y visor con gestos. */
(function () {
  "use strict";
  var A = window.ALBUM, R = document.body.dataset.raiz || "";
  var $ = function (id) { return document.getElementById(id); };
  var el = function (tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  var alCargar = function (img) {
    var ok = function () { img.classList.add("cargada"); };
    if (img.complete && img.naturalWidth) ok(); else { img.addEventListener("load", ok); img.addEventListener("error", ok); }
  };

  /* ---------- portada ---------- */
  alCargar(document.querySelector(".portada img"));
  $("p-ante").textContent = A.padre ? A.padre.titulo : (A.fechas_propias ? A.anio : "");
  $("p-lugares").textContent = A.lugares.filter(function (l) { return l !== A.titulo; }).slice(0, 3).join(" · ");
  $("p-fechas").textContent = A.fechas;

  /* ---------- introducción ---------- */
  var intro = $("intro"), filtro = "";  /* filtro ya no se usa: cada ciudad tiene su página */
  intro.innerHTML = '<div class="adorno"><svg class="corazon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.7 4.5c2.1 0 3.6 1.2 4.3 2.6h2c.7-1.4 2.2-2.6 4.3-2.6 3.7 0 5.8 3.9 4.3 7.3C19.5 16.4 12 21 12 21z"/></svg></div>';
  if (A.frase) intro.appendChild(el("p", "frase", A.frase));
  /* Botones de ciudades: cada uno abre la página (URL) de esa ciudad; el abierto queda marcado */
  /* En la página del viaje: un recuadro por ciudad que abre su álbum */
  if (!A.padre && (A.ciudades || []).length) {
    var rec = el("div", "tarjetas recuadros");
    A.ciudades.forEach(function (c) {
      var t = el("a", "tarjeta");
      t.href = c.url;
      t.style.setProperty("--c", c.color || "#cfc4b8");
      var im = el("img"); im.loading = "lazy"; im.decoding = "async"; im.alt = ""; im.src = R + c.portada; alCargar(im);
      var tx = el("div", "t");
      tx.appendChild(el("b", "", c.titulo));
      tx.appendChild(el("span", "", c.n + (c.n === 1 ? " foto" : " fotos")));
      t.appendChild(im); t.appendChild(tx); rec.appendChild(t);
    });
    intro.appendChild(rec);
  }
  var lista = A.padre ? (A.hermanos || []) : [];
  if (lista.length > 1) {
    var chips = el("nav", "chips");
    chips.setAttribute("aria-label", "Ciudades del viaje");
    var hacerChip = function (texto, href, activo) {
      var c = el("a", "chip", texto);
      c.href = href;
      if (activo) c.setAttribute("aria-current", "page");
      chips.appendChild(c);
    };
    hacerChip(A.padre ? "Todo " + A.padre.titulo : "Todo", A.padre ? "../" : "./", !A.padre);
    lista.forEach(function (c) { hacerChip(c.titulo, c.url, A.padre && c.titulo === A.titulo); });
    intro.appendChild(chips);
  }
  var nCiud = A.lugares.length;
  intro.appendChild(el("p", "datos", A.n.toLocaleString("es-ES") + " fotos" + (nCiud > 1 ? " · " + nCiud + " lugares" : "")));

  if (A.padre) {
    var pie = document.querySelector(".pie-pag");
    var otro = el("div"); otro.style.marginTop = "12px";
    var lk2 = el("a", "", "Todos nuestros viajes"); lk2.href = R; lk2.style.cssText = "font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:var(--suave)";
    otro.appendChild(lk2); pie.appendChild(otro);
  }

  /* ---------- galería: una sección por carpeta de ciudad ---------- */
  var fotos = [], gal = $("galeria");
  function pintarGaleria() {
    fotos = []; gal.innerHTML = "";
    var frag = document.createDocumentFragment();
    A.secciones.forEach(function (s) {
      if (filtro && s.titulo !== filtro) return;
      var sec = el("section", "dia");
      if (s.titulo) {
        var cab = el("div", "dia-cab");
        cab.appendChild(el("span", "n", s.titulo));
        cab.appendChild(el("span", "f", s.fotos.length + (s.fotos.length === 1 ? " foto" : " fotos")));
        var pag = (A.ciudades || []).filter(function (c) { return c.titulo === s.titulo; })[0];
        if (pag) { var lk = el("a", "ver-ciudad", "Abrir álbum →"); lk.href = pag.url; cab.appendChild(lk); }
        sec.appendChild(cab);
      }
      var rej = el("div", s.fotos.length <= 2 ? "rejilla pocas" : "rejilla");
      s.fotos.forEach(function (f) {
        f.l = s.titulo && s.titulo !== "Otros momentos" ? s.titulo : "";
        var i = fotos.push(f) - 1;
        var b = el("button", "foto");
        b.style.setProperty("--r", (f.w / f.h).toFixed(4));
        b.setAttribute("aria-label", "Abrir foto " + (i + 1));
        b.dataset.i = i;
        var img = el("img");
        img.loading = "lazy"; img.decoding = "async"; img.alt = f.l || A.titulo;
        img.src = R + f.m;
        alCargar(img);
        b.appendChild(img);
        rej.appendChild(b);
      });
      sec.appendChild(rej);
      frag.appendChild(sec);
    });
    gal.appendChild(frag);
  }
  pintarGaleria();
  gal.addEventListener("click", function (e) {
    var b = e.target.closest(".foto");
    if (b) abrir(+b.dataset.i);
  });

  /* ---------- aparición suave ---------- */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("visto"); io.unobserve(x.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".aparece").forEach(function (n) { io.observe(n); });
  } else document.querySelectorAll(".aparece").forEach(function (n) { n.classList.add("visto"); });

  /* =========================================================== visor */
  var V = $("visor"), P = $("pista"), D = P.children, idx = 0, abierto = false, anim = false;
  var preferMenosMov = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function pintar(slot, i) {
    var d = D[slot]; d.innerHTML = "";
    if (i < 0 || i >= fotos.length) return;
    var f = fotos[i], img = el("img");
    img.alt = f.l || ""; img.draggable = false;
    img.src = R + f.m; alCargar(img);
    var g = new Image(); g.decoding = "async";
    g.onload = function () { if (img.isConnected) img.src = g.src; };
    g.src = R + f.g;
    d.appendChild(img);
  }
  function mover(px, conTrans) {
    P.style.transition = conTrans && !preferMenosMov ? "transform .38s cubic-bezier(.22,.61,.36,1)" : "none";
    P.style.transform = "translate3d(calc(-100% + " + px + "px),0,0)";
  }
  function mostrar(i) {
    idx = i;
    pintar(0, i - 1); pintar(1, i); pintar(2, i + 1);
    mover(0, false);
    var f = fotos[i];
    $("v-cont").textContent = (i + 1) + " / " + fotos.length;
    $("v-lug").textContent = f.l || A.titulo;
    $("v-fec").textContent = A.fechas || "";
    $("v-ant").style.visibility = i > 0 ? "" : "hidden";
    $("v-sig").style.visibility = i < fotos.length - 1 ? "" : "hidden";
  }
  function ir(dir) {
    var n = idx + dir;
    if (anim || n < 0 || n >= fotos.length) { mover(0, true); return; }
    anim = true;
    P.style.transition = preferMenosMov ? "none" : "transform .38s cubic-bezier(.22,.61,.36,1)";
    P.style.transform = "translate3d(" + (dir > 0 ? "-200%" : "0%") + ",0,0)";
    var fin = function () { P.removeEventListener("transitionend", fin); anim = false; mostrar(n); };
    if (preferMenosMov) fin(); else { P.addEventListener("transitionend", fin); setTimeout(function () { if (anim) fin(); }, 500); }
  }
  function abrir(i) {
    mostrar(i);
    abierto = true; V.classList.add("abierto"); V.classList.remove("limpio");
    document.documentElement.style.overflow = "hidden";
    history.pushState({ visor: 1 }, "", "#foto-" + (i + 1));
    $("v-cerrar").focus({ preventScroll: true });
  }
  function cerrarUI() {
    if (!abierto) return;
    abierto = false; V.classList.remove("abierto");
    document.documentElement.style.overflow = "";
    P.style.opacity = ""; V.style.background = "";
    var b = gal.querySelector('.foto[data-i="' + idx + '"]');
    if (b) { b.scrollIntoView({ block: "center" }); b.focus({ preventScroll: true }); }
  }
  function cerrar() { if (history.state && history.state.visor) history.back(); else cerrarUI(); }
  window.addEventListener("popstate", cerrarUI);
  if (/^#foto-/.test(location.hash)) history.replaceState(null, "", location.pathname + location.search);

  $("v-cerrar").addEventListener("click", cerrar);
  $("v-ant").addEventListener("click", function () { ir(-1); });
  $("v-sig").addEventListener("click", function () { ir(1); });
  document.addEventListener("keydown", function (e) {
    if (!abierto) return;
    if (e.key === "ArrowRight") ir(1);
    else if (e.key === "ArrowLeft") ir(-1);
    else if (e.key === "Escape") cerrar();
  });

  /* gestos: deslizar lateral = cambiar, deslizar abajo = cerrar, toque = ocultar controles */
  var x0 = 0, y0 = 0, t0 = 0, dx = 0, dy = 0, eje = null, activo = false;
  V.addEventListener("pointerdown", function (e) {
    if (e.target.closest("button") || anim) return;
    activo = true; x0 = e.clientX; y0 = e.clientY; t0 = Date.now(); dx = dy = 0; eje = null;
    V.setPointerCapture(e.pointerId);
  });
  V.addEventListener("pointermove", function (e) {
    if (!activo) return;
    dx = e.clientX - x0; dy = e.clientY - y0;
    if (!eje && Math.abs(dx) + Math.abs(dy) > 8) eje = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    if (eje === "x") {
      var borde = (idx === 0 && dx > 0) || (idx === fotos.length - 1 && dx < 0);
      mover(borde ? dx / 3 : dx, false);
    } else if (eje === "y" && dy > 0) {
      P.style.transition = "none";
      P.style.transform = "translate3d(-100%," + dy + "px,0) scale(" + Math.max(.85, 1 - dy / 1500) + ")";
      V.style.background = "rgba(13,11,10," + Math.max(.2, 1 - dy / 400) + ")";
    }
  });
  function soltar() {
    if (!activo) return; activo = false;
    var v = Math.abs(dx) / Math.max(1, Date.now() - t0);
    if (eje === "x") {
      if (dx < -60 || (dx < -20 && v > .4)) ir(1);
      else if (dx > 60 || (dx > 20 && v > .4)) ir(-1);
      else mover(0, true);
    } else if (eje === "y") {
      V.style.background = "";
      if (dy > 110) { P.style.transition = "opacity .25s"; P.style.opacity = "0"; setTimeout(function () { cerrar(); P.style.opacity = ""; mover(0, false); }, 200); }
      else mover(0, true);
    } else if (Date.now() - t0 < 300) V.classList.toggle("limpio");
  }
  V.addEventListener("pointerup", soltar);
  V.addEventListener("pointercancel", soltar);
})();
