/* Página principal: mapa de viajes y lista por años. */
(function () {
  "use strict";
  var S = window.SITIO, V = S.viajes;
  var esc = function (t) { return String(t || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var url = function (v) { return v.url; };
  var sub = function (v) {
    if (v.fechas && v.fechas !== String(v.anio)) return v.fechas;
    if (v.lugares.length > 1) return v.lugares.slice(0, 3).join(" · ");
    return v.n + " fotos";
  };

  var total = V.reduce(function (s, v) { return s + v.n; }, 0);
  var anios = V.map(function (v) { return v.anio; }).filter(Boolean);
  document.getElementById("resumen").textContent =
    V.length + " viajes · " + total.toLocaleString("es-ES") + " fotos" +
    (anios.length ? " · desde " + Math.min.apply(null, anios) : "");

  /* ---------- lista por años ---------- */
  var lista = document.getElementById("lista"), porAnio = {};
  V.forEach(function (v) { var a = v.anio || "Sin fecha"; (porAnio[a] = porAnio[a] || []).push(v); });
  Object.keys(porAnio).sort(function (a, b) { return String(b).localeCompare(String(a)); }).forEach(function (a) {
    var s = document.createElement("section"); s.className = "anio aparece";
    s.innerHTML = "<h2>" + esc(a) + "</h2>";
    var g = document.createElement("div"); g.className = "tarjetas";
    porAnio[a].forEach(function (v) {
      var t = document.createElement("a"); t.className = "tarjeta"; t.href = url(v);
      t.style.setProperty("--c", v.portada.color);
      t.innerHTML = '<img loading="lazy" decoding="async" alt="" src="' + esc(v.portada.m) + '">' +
        '<div class="t"><b>' + esc(v.titulo) + "</b><span>" + esc(sub(v)) + "</span></div>";
      var img = t.querySelector("img");
      var ok = function () { img.classList.add("cargada"); };
      if (img.complete && img.naturalWidth) ok(); else { img.onload = ok; img.onerror = ok; }
      g.appendChild(t);
    });
    s.appendChild(g); lista.appendChild(s);
  });

  /* ---------- aparición suave ---------- */
  var nodos = document.querySelectorAll(".aparece");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("visto"); io.unobserve(x.target); } });
    }, { rootMargin: "0px 0px -6% 0px" });
    nodos.forEach(function (n) { io.observe(n); });
  } else nodos.forEach(function (n) { n.classList.add("visto"); });

  /* ---------- mapa ---------- */
  var caja = document.querySelector(".mapa-caja");
  if (!window.L) { caja.style.display = "none"; return; }
  var tactil = window.matchMedia("(pointer: coarse)").matches;
  var mapa = L.map("mapa", {
    zoomControl: !tactil, scrollWheelZoom: false, dragging: !tactil, tap: false,
    worldCopyJump: true, attributionControl: true
  });
  /* Fondo del mapa: OpenStreetMap (gratis, sin clave). Si fallara, pasa solo a Esri. */
  var fondos = [
    ["https://tile.openstreetmap.org/{z}/{x}/{y}.png",
     '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'],
    ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
     'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap']
  ];
  var nFondo = 0, fallos = 0, capa;
  function ponerFondo() {
    if (capa) mapa.removeLayer(capa);
    capa = L.tileLayer(fondos[nFondo][0], { maxZoom: 18, attribution: fondos[nFondo][1] }).addTo(mapa);
    capa.on("tileerror", function () {
      if (++fallos > 4 && nFondo < fondos.length - 1) { nFondo++; fallos = 0; ponerFondo(); }
    });
  }
  ponerFondo();

  var puntos = [];
  V.forEach(function (v) {
    if (!v.pos) return;
    var icono = L.divIcon({
      className: "", iconSize: [40, 40], iconAnchor: [20, 20], popupAnchor: [0, -18],
      html: '<div class="marcador' + (v.origen_pos === "carpeta" ? " aprox" : "") + '" style="background-image:url(\'' + esc(v.portada.m) + '\')"></div>'
    });
    L.marker(v.pos, { icon: icono, title: v.titulo, riseOnHover: true }).addTo(mapa).bindPopup(
      '<a class="pop" href="' + url(v) + '"><img src="' + esc(v.portada.m) + '" alt=""><div><b>' + esc(v.titulo) +
      "</b><span>" + esc(v.fechas) + (v.lugares.length ? "<br>" + esc(v.lugares.slice(0, 3).join(" · ")) : "") +
      '</span><span style="margin:0;color:inherit">Abrir álbum →</span></div></a>', { closeButton: false });
    puntos.push(v.pos);
  });
  if (puntos.length) mapa.fitBounds(puntos, { padding: [40, 40], maxZoom: 9 });
  else mapa.setView([45, 5], 4);

  /* En el móvil, el mapa se "activa" al tocarlo para no secuestrar el scroll de la página. */
  if (tactil) {
    var aviso = document.createElement("button");
    aviso.textContent = "Toca para explorar el mapa";
    aviso.style.cssText = "position:absolute;left:50%;bottom:16px;transform:translateX(-50%);z-index:500;" +
      "background:rgba(255,255,255,.92);border-radius:999px;padding:10px 18px;font-size:.72rem;letter-spacing:.14em;" +
      "text-transform:uppercase;box-shadow:0 6px 18px rgba(0,0,0,.15)";
    caja.appendChild(aviso);
    aviso.addEventListener("click", function () {
      mapa.dragging.enable(); mapa.touchZoom.enable();
      aviso.remove();
    });
  }
})();
