"use strict";

// ---------------------------------------------------------------------------
// Esfera animada (canvas 2D): núcleo con glow + anillos rotando + partículas.
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

let estadoOrbe = "idle";
let inicioEstado = performance.now();
let ancho = 0, alto = 0, centroX = 0, centroY = 0, radioBase = 0;

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
}
window.addEventListener("resize", redimensionar);
redimensionar();

function fijarEstadoOrbe(nuevoEstado) {
  if (estadoOrbe !== nuevoEstado) {
    estadoOrbe = nuevoEstado;
    inicioEstado = performance.now();
  }
}

function dibujarOrbe(t) {
  ctx.clearRect(0, 0, ancho, alto);
  const color = COLORES[estadoOrbe] || COLORES.idle;
  const transcurrido = (t - inicioEstado) / 1000;

  let velocidadPulso = 1.1, amplitudPulso = 0.06, velocidadRotacion = 0.15;
  if (estadoOrbe === "pensando") { velocidadPulso = 3.2; amplitudPulso = 0.09; velocidadRotacion = 0.9; }
  if (estadoOrbe === "escuchando") { velocidadPulso = 4.5; amplitudPulso = 0.14; velocidadRotacion = 0.5; }
  if (estadoOrbe === "hablando") { velocidadPulso = 6; amplitudPulso = 0.1; velocidadRotacion = 0.35; }
  if (estadoOrbe === "error") { velocidadPulso = 8; amplitudPulso = 0.18; velocidadRotacion = 0.1; }

  const pulso = 1 + Math.sin(t / 1000 * velocidadPulso) * amplitudPulso;
  const radio = radioBase * pulso;

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

  // Anillos orbitales
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
  elementoSubtitulos.innerHTML = `<span class="quien">${quien}</span>${texto}`;
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
