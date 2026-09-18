import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from apscheduler.schedulers.background import BackgroundScheduler

# Importaciones de los módulos locales que creaste arriba
from memory import JarvisMemory
from windows_os import WindowsController
from android_os import AndroidController

load_dotenv()


class JarvisCore:
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY no está configurada. Copia .env.example a .env "
                "y coloca tu clave antes de iniciar JARVIS."
            )
        self.openai_client = OpenAI(api_key=api_key)

        # Instanciación de subsistemas de hardware y almacenamiento
        self.memoria = JarvisMemory()

        # El control de ventanas requiere un entorno de escritorio con display;
        # si no está disponible (p. ej. sesión remota o servidor), JARVIS sigue
        # operativo pero informa que ese subsistema está inactivo.
        try:
            self.windows = WindowsController()
        except Exception as e:
            print(f"[Sistema] Advertencia: subsistema de Windows no disponible ({e}).")
            self.windows = None

        self.android = AndroidController()

        # Motor de Automatizaciones en segundo plano (Cron-Jobs)
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def obtener_esquema_herramientas(self):
        """Mapeo estructurado para indicarle al modelo qué herramientas puede autogestionar."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "gestionar_ventanas",
                    "description": "Controla interfaces visuales o programas abiertos en Windows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["minimizar_todo", "abrir"]},
                            "programa": {"type": "string", "description": "Nombre de la aplicación, ej: 'chrome', 'notepad'"}
                        },
                        "required": ["accion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escanear_hardware",
                    "description": "Devuelve lecturas métricas en tiempo real de la CPU, RAM y procesos de Windows."
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clasificar_directorio",
                    "description": "Organiza automáticamente carpetas de archivos de forma masiva según su extensión.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ruta_directorio": {"type": "string", "description": "Ruta de la carpeta absoluta a ordenar"}
                        },
                        "required": ["ruta_directorio"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ejecutar_comando_android",
                    "description": "Controla el teléfono móvil enlazado (música, capturas, inyección de datos).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accion": {"type": "string", "enum": ["abrir_spotify", "capturar_pantalla_movil", "escribir"]},
                            "texto_inyectar": {"type": "string", "description": "Texto si la acción requiere escritura"}
                        },
                        "required": ["accion"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recordar_dato",
                    "description": "Guarda explícitamente información crítica sobre hábitos del usuario o preferencias para el futuro.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "clave_contexto": {"type": "string", "description": "ID único simplificado, ej: 'preferencia_cafe'"},
                            "informacion": {"type": "string", "description": "El dato puro que hay que almacenar en la base de datos"}
                        },
                        "required": ["clave_contexto", "informacion"]
                    }
                }
            }
        ]

    def procesar_orden(self, entrada_usuario):
        # 1. Recuperación automática de memoria semántica de fondo
        contexto_pasado = self.memoria.recuperar_contexto(entrada_usuario)
        system_prompt = "Eres JARVIS, un asistente inteligente autónomo avanzado integrado en los sistemas operativos del usuario. Responde de manera sofisticada, concisa y caballerosa."
        if contexto_pasado:
            system_prompt += f" Contexto recuperado de la base de datos de hábitos del usuario: {contexto_pasado}"

        # 2. Análisis semántico de la orden por el LLM
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": entrada_usuario}
            ],
            tools=self.obtener_esquema_herramientas(),
            tool_choice="auto"
        )
        
        mensaje_respuesta = response.choices[0].message
        tool_calls = mensaje_respuesta.tool_calls

        # 3. Si la IA determina que el comando requiere interactuar con el mundo físico/máquina
        if tool_calls:
            # Todas las tool_calls de este turno deben resolverse antes de pedir
            # la respuesta final: la API rechaza el turno si falta alguna.
            mensajes_tool = []
            for tool_call in tool_calls:
                nombre_funcion = tool_call.function.name
                try:
                    argumentos = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    argumentos = {}

                try:
                    # Enrutamiento dinámico hacia los módulos importados
                    if nombre_funcion in ("gestionar_ventanas", "escanear_hardware", "clasificar_directorio") and self.windows is None:
                        resultado_ejecucion = "El subsistema de Windows no está disponible en este entorno."
                    elif nombre_funcion == "gestionar_ventanas":
                        resultado_ejecucion = self.windows.gestionar_ventanas(**argumentos)
                    elif nombre_funcion == "escanear_hardware":
                        resultado_ejecucion = self.windows.escanear_hardware()
                    elif nombre_funcion == "clasificar_directorio":
                        resultado_ejecucion = self.windows.clasificar_directorio(**argumentos)
                    elif nombre_funcion == "ejecutar_comando_android":
                        resultado_ejecucion = self.android.ejecutar_comando(**argumentos)
                    elif nombre_funcion == "recordar_dato":
                        resultado_ejecucion = self.memoria.recordar_dato(**argumentos)
                    else:
                        resultado_ejecucion = "Error de enlace en la matriz de funciones."
                except Exception as e:
                    resultado_ejecucion = f"Fallo al ejecutar '{nombre_funcion}': {e}"

                mensajes_tool.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(resultado_ejecucion),
                })

            # Devuelve los resultados de la máquina a la IA para que formule la confirmación por voz/texto
            final_response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": entrada_usuario},
                    mensaje_respuesta,
                    *mensajes_tool,
                ]
            )
            print(f"\n[JARVIS]: {final_response.choices[0].message.content}")
        else:
            print(f"\n[JARVIS]: {mensaje_respuesta.content}")

# =====================================================================
# INICIALIZADOR DE INTERFAZ POR CONSOLA (Listo para acoplar entrada de audio)
# =====================================================================
if __name__ == "__main__":
    print("[Matriz Central] Inicializando sistemas periféricos de JARVIS...")
    try:
        jarvis = JarvisCore()
    except RuntimeError as e:
        print(f"[Falla de Arranque]: {e}")
        raise SystemExit(1)
    print("[Matriz Central] Todos los sistemas se encuentran operativos, Señor.")
    
    while True:
        try:
            orden = input("\nInterfaz de comando activa: ")
            if orden.lower() in ['salir', 'shutdown', 'apagar']:
                print("[JARVIS]: Desactivando módulos locales de procesamiento. Buenas noches, señor.")
                jarvis.scheduler.shutdown()
                break
            if not orden.strip():
                continue
                
            jarvis.procesar_orden(orden)
            
        except KeyboardInterrupt:
            jarvis.scheduler.shutdown()
            break
        except Exception as e:
            print(f"[Falla de Núcleo]: {e}")