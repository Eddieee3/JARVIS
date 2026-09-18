# JARVIS (prototipo)

Asistente con function-calling (OpenAI), memoria semántica persistente (ChromaDB),
control de Windows / Android (ADB), entrada/salida por voz y una app de escritorio
(Tkinter). JARVIS también aprende de sus propios errores: cuando una herramienta
falla, registra el fallo en memoria y reintenta con un enfoque distinto antes de
responder.

## Instalación

```bash
cd JARVIS_PROJECT
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y coloca tu clave de OpenAI:

```bash
copy .env.example .env
```

## Ejecución

**App de escritorio (recomendado):**

```bash
python gui.py
```

Ventana con historial de chat, entrada de texto, botón "🎤 Hablar" para dar
órdenes por voz, y una casilla para que JARVIS lea sus respuestas en voz alta.

**Consola (sin interfaz gráfica):**

```bash
python jarvis.py
```

Escribe una orden en la consola. Escribe `salir`, `apagar` o `shutdown` para
terminar. `Ctrl+C` también cierra la sesión de forma controlada.

## Subsistemas

- **windows_os.py** — control de ventanas (`pyautogui`), diagnóstico de
  CPU/RAM/procesos (`psutil`) y clasificación automática de carpetas por
  extensión. Requiere un entorno de escritorio con display; si no está
  disponible, JARVIS lo desactiva automáticamente y sigue funcionando.
- **android_os.py** — control de un dispositivo Android enlazado por ADB
  (`adb start-server`, depuración USB activada). Si no hay un dispositivo
  conectado, las órdenes móviles responden con un aviso en vez de fallar.
- **memory.py** — memoria episódica persistente en `.jarvis_memory/` (ChromaDB
  local, sin dependencias de pago): preferencias del usuario y bitácora de
  fallos de herramientas, ambas consultadas como contexto en cada orden.
- **voice.py** — entrada por voz (STT, vía `sounddevice` + Google Speech
  Recognition) y salida por voz (TTS local con `pyttsx3`/SAPI5). No usa PyAudio
  para evitar depender de un compilador de C++ en Windows.
- **gui.py** — aplicación de escritorio (Tkinter) que envuelve `JarvisCore` con
  chat de texto y voz.

## Aprendizaje de errores

Cuando una herramienta falla durante una orden, JARVIS:

1. Registra el fallo (herramienta, argumentos, error) en `jarvis_error_log`
   dentro de `.jarvis_memory/`.
2. Le devuelve el error al modelo en la misma conversación para que reintente
   con otro enfoque (hasta 2 veces por orden, configurable con el parámetro
   `max_reintentos` de `procesar_orden`).
3. En órdenes futuras similares, recupera esos fallos pasados como contexto
   para evitar repetirlos.

## Notas

- Requiere Python 3.10+ y una clave de API de OpenAI con acceso a `gpt-4o`.
- El control de Android es opcional: sin `adb` y sin un dispositivo enlazado,
  esas órdenes simplemente informan que el subsistema no está disponible.
- La entrada por voz necesita un micrófono accesible por `sounddevice`; si el
  reconocimiento falla (sin conexión, sin micrófono), la GUI lo informa sin
  interrumpir el resto de la app.
