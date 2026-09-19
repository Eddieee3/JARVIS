"use strict";

// ---------------------------------------------------------------------------
// Esfera animada (canvas 2D): estrellas de fondo + glow + núcleo + anillos
// rotando + partículas orbitando + pulsos tipo sonar + anillo HUD con marcas.
// Estados: idle, pensando, escuchando, hablando, error.
// ---------------------------------------------------------------------------

const canvas = document.getElementById("orb-canvas");
const ctx = canvas.getContext("2d");

const COLORES = {
  idle: "76,230,255",
  pensando: "76,230,255",
  escuchando: "76,255,190",
  hablando: "120,240,255",
  error: "255,77,77",
};

const INTERVALO_PULSO = {
  idle: 2200, pensando: 650, escuchando: 550, hablando: 950, error: 380,
};

let estadoOrbe = "idle";
let inicioEstado = performance.now();
let ancho = 0, alto = 0, centroX = 0, centroY = 0, radioBase = 0;
let estrellas = [];
let particulas = [];
let pulsos = [];
let ultimoPulso = 0;

function generarEstrellas() {
  const cantidad = Math.round((ancho * alto) / 9000);
  estrellas = Array.from({ length: cantidad }, () => ({
    x: Math.random() * ancho,
    y: Math.random() * alto,
    r: Math.random() * 1.3 + 0.3,
    fase: Math.random() * Math.PI * 2,
    velocidad: 0.4 + Math.random() * 0.8,
  }));
}

function generarParticulas() {
  particulas = Array.from({ length: 30 }, (_, i) => ({
    anguloInicial: Math.random() * Math.PI * 2,
    radioMult: 1.35 + Math.random() * 2.1,
    velocidad: (0.15 + Math.random() * 0.55) * (Math.random() < 0.5 ? 1 : -1),
    tam: 0.8 + Math.random() * 2.1,
    fase: Math.random() * Math.PI * 2,
    parpadeo: 1.2 + Math.random() * 2.4,
    achatado: 0.45 + Math.random() * 0.25,
  }));
}

function redimensionar() {
  const dpr = window.devicePixelRatio || 1;
  ancho = window.innerWidth;
  alto = window.innerHeight;
  canvas.width = ancho * dpr;
  canvas.height = alto * dpr;
  canvas.style.width = ancho + "px";
  canvas.style.height = alto + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  centroX = ancho / 2;
  centroY = alto / 2 - 40;
  radioBase = Math.min(ancho, alto) * 0.14;
  generarEstrellas();
  generarParticulas();
}
window.addEventListener("resize", redimensionar);
redimensionar();

function fijarEstadoOrbe(nuevoEstado) {
  if (estadoOrbe !== nuevoEstado) {
    estadoOrbe = nuevoEstado;
    inicioEstado = performance.now();
  }
}

function dibujarEstrellas(t) {
  estrellas.forEach((estrella) => {
    const parpadeo = 0.35 + Math.sin(t / 1000 * estrella.velocidad + estrella.fase) * 0.35;
    ctx.fillStyle = `rgba(180,225,255,${Math.max(0, parpadeo)})`;
    ctx.beginPath();
    ctx.arc(estrella.x, estrella.y, estrella.r, 0, Math.PI * 2);
    ctx.fill();
  });
}

function dibujarAnilloHud(t, color, radio) {
  const radioHud = radio * 4.1;
  const marcas = 60;
  const rotacion = t / 1000 * 0.04;
  ctx.strokeStyle = `rgba(${color},0.22)`;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(centroX, centroY, radioHud, 0, Math.PI * 2);
  ctx.stroke();
  for (let i = 0; i < marcas; i++) {
    const angulo = (i / marcas) * Math.PI * 2 + rotacion;
    const largo = i % 5 === 0 ? 10 : 4;
    const x1 = centroX + Math.cos(angulo) * radioHud;
    const y1 = centroY + Math.sin(angulo) * radioHud;
    const x2 = centroX + Math.cos(angulo) * (radioHud + largo);
    const y2 = centroY + Math.sin(angulo) * (radioHud + largo);
    ctx.strokeStyle = `rgba(${color},${i % 5 === 0 ? 0.4 : 0.18})`;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
}

function dibujarPulsos(t, color) {
  const duracion = 1700;
  pulsos = pulsos.filter((p) => t - p.inicio < duracion);
  pulsos.forEach((p) => {
    const progreso = (t - p.inicio) / duracion;
    const radioPulso = radioBase * (1 + progreso * 3.4);
    ctx.strokeStyle = `rgba(${color},${0.45 * (1 - progreso)})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(centroX, centroY, radioPulso, 0, Math.PI * 2);
    ctx.stroke();
  });
}

function dibujarParticulas(t, color, radio) {
  particulas.forEach((p) => {
    const angulo = p.anguloInicial + (t / 1000) * p.velocidad;
    const radioOrbita = radio * p.radioMult;
    const x = centroX + Math.cos(angulo) * radioOrbita;
    const y = centroY + Math.sin(angulo) * radioOrbita * p.achatado;
    const brillo = 0.35 + Math.sin(t / 1000 * p.parpadeo + p.fase) * 0.35;
    // Estela sutil detrás de la partícula
    const anguloEstela = angulo - 0.12 * Math.sign(p.velocidad || 1);
    const xEstela = centroX + Math.cos(anguloEstela) * radioOrbita;
    const yEstela = centroY + Math.sin(anguloEstela) * radioOrbita * p.achatado;
    ctx.strokeStyle = `rgba(${color},${Math.max(0, brillo) * 0.25})`;
    ctx.lineWidth = p.tam * 0.7;
    ctx.beginPath();
    ctx.moveTo(xEstela, yEstela);
    ctx.lineTo(x, y);
    ctx.stroke();

    ctx.fillStyle = `rgba(${color},${Math.max(0, Math.min(1, brillo + 0.25))})`;
    ctx.beginPath();
    ctx.arc(x, y, p.tam, 0, Math.PI * 2);
    ctx.fill();
  });
}

function dibujarOrbe(t) {
  ctx.clearRect(0, 0, ancho, alto);
  const color = COLORES[estadoOrbe] || COLORES.idle;

  dibujarEstrellas(t);

  let velocidadPulso = 1.1, amplitudPulso = 0.06, velocidadRotacion = 0.15;
  if (estadoOrbe === "pensando") { velocidadPulso = 3.2; amplitudPulso = 0.09; velocidadRotacion = 0.9; }
  if (estadoOrbe === "escuchando") { velocidadPulso = 4.5; amplitudPulso = 0.14; velocidadRotacion = 0.5; }
  if (estadoOrbe === "hablando") { velocidadPulso = 6; amplitudPulso = 0.1; velocidadRotacion = 0.35; }
  if (estadoOrbe === "error") { velocidadPulso = 8; amplitudPulso = 0.18; velocidadRotacion = 0.1; }

  const pulso = 1 + Math.sin(t / 1000 * velocidadPulso) * amplitudPulso;
  const radio = radioBase * pulso;

  // Pulsos tipo sonar: se generan a un ritmo que depende del estado
  const intervalo = INTERVALO_PULSO[estadoOrbe] || INTERVALO_PULSO.idle;
  if (t - ultimoPulso > intervalo) {
    pulsos.push({ inicio: t });
    ultimoPulso = t;
  }
  dibujarPulsos(t, color);

  // Anillo HUD exterior con marcas (tipo mira/reticle)
  dibujarAnilloHud(t, color, radio);

  // Partículas orbitando (más pequeñas, con estela)
  dibujarParticulas(t, color, radio);

  // Glow exterior
  const gradiente = ctx.createRadialGradient(centroX, centroY, radio * 0.1, centroX, centroY, radio * 3.2);
  gradiente.addColorStop(0, `rgba(${color},0.55)`);
  gradiente.addColorStop(0.35, `rgba(${color},0.12)`);
  gradiente.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = gradiente;
  ctx.beginPath();
  ctx.arc(centroX, centroY, radio * 3.2, 0, Math.PI * 2);
  ctx.fill();

  // Núcleo
  const nucleo = ctx.createRadialGradient(centroX, centroY, 0, centroX, centroY, radio);
  nucleo.addColorStop(0, `rgba(${color},0.95)`);
  nucleo.addColorStop(0.7, `rgba(${color},0.55)`);
  nucleo.addColorStop(1, `rgba(${color},0.05)`);
  ctx.fillStyle = nucleo;
  ctx.beginPath();
  ctx.arc(centroX, centroY, radio, 0, Math.PI * 2);
  ctx.fill();

  // Anillos orbitales (segmentados, rotando)
  const anillos = [
    { radio: radio * 1.7, ancho: 2, segmentos: 10, velocidad: velocidadRotacion, offset: 0 },
    { radio: radio * 2.15, ancho: 1.5, segmentos: 16, velocidad: -velocidadRotacion * 0.6, offset: 1.2 },
    { radio: radio * 2.6, ancho: 1, segmentos: 22, velocidad: velocidadRotacion * 0.35, offset: 2.4 },
  ];
  anillos.forEach((anillo) => {
    ctx.strokeStyle = `rgba(${color},0.5)`;
    ctx.lineWidth = anillo.ancho;
    const paso = (Math.PI * 2) / anillo.segmentos;
    const rotacion = t / 1000 * anillo.velocidad + anillo.offset;
    for (let i = 0; i < anillo.segmentos; i++) {
      const inicioAngulo = i * paso + rotacion;
      const finAngulo = inicioAngulo + paso * 0.55;
      ctx.beginPath();
      ctx.arc(centroX, centroY, anillo.radio, inicioAngulo, finAngulo);
      ctx.stroke();
    }
  });

  requestAnimationFrame(dibujarOrbe);
}
requestAnimationFrame(dibujarOrbe);

// ---------------------------------------------------------------------------
// Subtítulos (el "chat" se muestra como texto superpuesto, no como lista)
// ---------------------------------------------------------------------------

const elementoSubtitulos = document.getElementById("subtitulos");
let temporizadorSubtitulo = null;

function mostrarSubtitulo(quien, texto) {
  if (!texto) return;
  // textContent (no innerHTML): el texto viene del usuario, del modelo y de
  // resultados de herramientas, y esta página tiene acceso a pywebview.api.
  const etiqueta = document.createElement("span");
  etiqueta.className = "quien";
  etiqueta.textContent = quien;
  elementoSubtitulos.replaceChildren(etiqueta, document.createTextNode(texto));
  elementoSubtitulos.classList.add("visible");
  if (temporizadorSubtitulo) clearTimeout(temporizadorSubtitulo);
  const duracion = Math.min(14000, Math.max(4000, texto.length * 60));
  temporizadorSubtitulo = setTimeout(() => {
    elementoSubtitulos.classList.remove("visible");
  }, duracion);
}

// ---------------------------------------------------------------------------
// Controles e integración con Python (puente pywebview)
// ---------------------------------------------------------------------------

const estadoInicial = document.getElementById("estado-inicial");
const campoEntrada = document.getElementById("campo-entrada");
const botonMicrofono = document.getElementById("boton-microfono");
const botonVozToggle = document.getElementById("boton-voz-toggle");

let vozActiva = true;
botonVozToggle.addEventListener("click", () => {
  vozActiva = !vozActiva;
  botonVozToggle.classList.toggle("activo", vozActiva);
});

function habilitarControles(habilitados) {
  campoEntrada.disabled = !habilitados;
  botonMicrofono.disabled = !habilitados;
}

async function procesarTexto(texto) {
  if (!texto || !texto.trim()) return;
  mostrarSubtitulo("Tú", texto);
  habilitarControles(false);
  fijarEstadoOrbe("pensando");
  try {
    const resultado = await window.pywebview.api.enviar_texto(texto, vozActiva);
    if (resultado && resultado.ok) {
      fijarEstadoOrbe("hablando");
      mostrarSubtitulo("JARVIS", resultado.respuesta);
      setTimeout(() => fijarEstadoOrbe("idle"), 2500);
    } else {
      fijarEstadoOrbe("error");
      mostrarSubtitulo("Sistema", (resultado && resultado.mensaje) || "Fallo desconocido.");
      setTimeout(() => fijarEstadoOrbe("idle"), 2000);
    }
  } catch (e) {
    fijarEstadoOrbe("error");
    mostrarSubtitulo("Sistema", "Fallo de comunicación con el núcleo: " + e);
    setTimeout(() => fijarEstadoOrbe("idle"), 2000);
  } finally {
    habilitarControles(true);
    campoEntrada.focus();
  }
}

campoEntrada.addEventListener("keydown", (evento) => {
  if (evento.key === "Enter") {
    const texto = campoEntrada.value;
    campoEntrada.value = "";
    procesarTexto(texto);
  }
});

botonMicrofono.addEventListener("click", async () => {
  habilitarControles(false);
  botonMicrofono.classList.add("escuchando");
  fijarEstadoOrbe("escuchando");
  mostrarSubtitulo("Sistema", "Escuchando...");
  try {
    const resultado = await window.pywebview.api.escuchar();
    botonMicrofono.classList.remove("escuchando");
    if (resultado && resultado.texto) {
      await procesarTexto(resultado.texto);
    } else {
      fijarEstadoOrbe("error");
      mostrarSubtitulo("Sistema", (resultado && resultado.error) || "No se entendió el audio.");
      setTimeout(() => fijarEstadoOrbe("idle"), 2000);
      habilitarControles(true);
    }
  } catch (e) {
    botonMicrofono.classList.remove("escuchando");
    fijarEstadoOrbe("error");
    mostrarSubtitulo("Sistema", "Fallo del subsistema de voz: " + e);
    setTimeout(() => fijarEstadoOrbe("idle"), 2000);
    habilitarControles(true);
  }
});

async function iniciar() {
  try {
    const resultado = await window.pywebview.api.iniciar_nucleo();
    if (resultado && resultado.ok) {
      estadoInicial.classList.add("oculto");
      mostrarSubtitulo("JARVIS", resultado.mensaje);
      fijarEstadoOrbe("idle");
      habilitarControles(true);
      campoEntrada.focus();
    } else {
      estadoInicial.textContent = "Falla de arranque: " + ((resultado && resultado.mensaje) || "error desconocido.");
      fijarEstadoOrbe("error");
    }
  } catch (e) {
    estadoInicial.textContent = "Falla de arranque: " + e;
    fijarEstadoOrbe("error");
  }
}

if (window.pywebview) {
  iniciar();
} else {
  window.addEventListener("pywebviewready", iniciar);
}
