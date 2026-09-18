import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

from jarvis import JarvisCore
from voice import VoiceInterface


class JarvisGUI(tk.Tk):
    """Aplicación de escritorio para JARVIS: chat de texto + entrada/salida por voz."""

    def __init__(self):
        super().__init__()
        self.title("JARVIS")
        self.geometry("640x520")
        self.minsize(480, 380)

        self.jarvis = None
        self.voice = VoiceInterface()
        self.hablar_respuestas = tk.BooleanVar(value=True)

        self._construir_interfaz()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        # La inicialización de JarvisCore puede tardar (carga del modelo de
        # embeddings, conexión ADB, etc.), así que corre en segundo plano para
        # no congelar la ventana al abrir.
        self._agregar_mensaje("Sistema", "Inicializando sistemas periféricos de JARVIS...")
        self._fijar_estado("Inicializando...", ocupado=True)
        threading.Thread(target=self._inicializar_jarvis, daemon=True).start()

    def _construir_interfaz(self):
        contenedor_chat = tk.Frame(self)
        contenedor_chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))

        self.area_chat = scrolledtext.ScrolledText(
            contenedor_chat, wrap=tk.WORD, state="disabled", font=("Segoe UI", 10)
        )
        self.area_chat.pack(fill=tk.BOTH, expand=True)

        self.etiqueta_estado = tk.Label(self, text="Iniciando...", anchor="w", fg="gray")
        self.etiqueta_estado.pack(fill=tk.X, padx=8)

        contenedor_entrada = tk.Frame(self)
        contenedor_entrada.pack(fill=tk.X, padx=8, pady=8)

        self.campo_entrada = tk.Entry(contenedor_entrada, font=("Segoe UI", 10))
        self.campo_entrada.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.campo_entrada.bind("<Return>", lambda evento: self._enviar_orden())

        self.boton_enviar = tk.Button(contenedor_entrada, text="Enviar", command=self._enviar_orden)
        self.boton_enviar.pack(side=tk.LEFT, padx=(6, 0))

        self.boton_microfono = tk.Button(contenedor_entrada, text="🎤 Hablar", command=self._escuchar_orden)
        self.boton_microfono.pack(side=tk.LEFT, padx=(6, 0))

        casilla_voz = tk.Checkbutton(
            self, text="Leer respuestas en voz alta", variable=self.hablar_respuestas
        )
        casilla_voz.pack(anchor="w", padx=8, pady=(0, 8))

        self._alternar_controles(activos=False)

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------
    def _inicializar_jarvis(self):
        try:
            jarvis = JarvisCore()
        except Exception as e:
            self.after(0, self._al_fallar_inicializacion, str(e))
            return
        self.after(0, self._al_completar_inicializacion, jarvis)

    def _al_completar_inicializacion(self, jarvis):
        self.jarvis = jarvis
        self._agregar_mensaje("JARVIS", "Todos los sistemas se encuentran operativos, Señor.")
        self._fijar_estado("Listo.")
        self._alternar_controles(activos=True)
        self.campo_entrada.focus_set()

    def _al_fallar_inicializacion(self, mensaje_error):
        self._agregar_mensaje("Sistema", f"Falla de arranque: {mensaje_error}")
        self._fijar_estado("Error de inicialización.", error=True)
        messagebox.showerror("JARVIS", f"No se pudo inicializar JARVIS:\n\n{mensaje_error}")

    # ------------------------------------------------------------------
    # Interacción por texto
    # ------------------------------------------------------------------
    def _enviar_orden(self):
        texto = self.campo_entrada.get().strip()
        if not texto or self.jarvis is None:
            return
        self.campo_entrada.delete(0, tk.END)
        self._agregar_mensaje("Tú", texto)
        self._procesar_en_segundo_plano(texto)

    def _procesar_en_segundo_plano(self, texto):
        self._alternar_controles(activos=False)
        self._fijar_estado("Pensando...", ocupado=True)
        threading.Thread(target=self._ejecutar_orden, args=(texto,), daemon=True).start()

    def _ejecutar_orden(self, texto):
        try:
            respuesta = self.jarvis.procesar_orden(texto)
        except Exception as e:
            respuesta = f"Fallo de núcleo: {e}"
        self.after(0, self._al_recibir_respuesta, respuesta)

    def _al_recibir_respuesta(self, respuesta):
        self._agregar_mensaje("JARVIS", respuesta)
        self._fijar_estado("Listo.")
        self._alternar_controles(activos=True)
        self.campo_entrada.focus_set()
        if self.hablar_respuestas.get() and respuesta:
            threading.Thread(target=self.voice.hablar, args=(respuesta,), daemon=True).start()

    # ------------------------------------------------------------------
    # Interacción por voz
    # ------------------------------------------------------------------
    def _escuchar_orden(self):
        if self.jarvis is None:
            return
        self._alternar_controles(activos=False)
        self._fijar_estado("Escuchando... (habla ahora)", ocupado=True)
        threading.Thread(target=self._capturar_voz, daemon=True).start()

    def _capturar_voz(self):
        texto, error = self.voice.escuchar()
        self.after(0, self._al_recibir_voz, texto, error)

    def _al_recibir_voz(self, texto, error):
        if not texto:
            self._agregar_mensaje("Sistema", error or "No se entendió el audio.")
            self._fijar_estado("Listo.")
            self._alternar_controles(activos=True)
            return
        self._agregar_mensaje("Tú (voz)", texto)
        self._procesar_en_segundo_plano(texto)

    # ------------------------------------------------------------------
    # Utilidades de interfaz
    # ------------------------------------------------------------------
    def _agregar_mensaje(self, remitente, mensaje):
        self.area_chat.configure(state="normal")
        self.area_chat.insert(tk.END, f"{remitente}: {mensaje}\n\n")
        self.area_chat.configure(state="disabled")
        self.area_chat.see(tk.END)

    def _fijar_estado(self, texto, ocupado=False, error=False):
        self.etiqueta_estado.configure(text=texto, fg="red" if error else ("orange" if ocupado else "green"))

    def _alternar_controles(self, activos):
        estado = tk.NORMAL if activos else tk.DISABLED
        self.campo_entrada.configure(state=estado)
        self.boton_enviar.configure(state=estado)
        self.boton_microfono.configure(state=estado)

    def _al_cerrar(self):
        if self.jarvis is not None:
            try:
                self.jarvis.scheduler.shutdown(wait=False)
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = JarvisGUI()
    app.mainloop()
