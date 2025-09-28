# =============================================================================
# --- INICIO DEL PARCHE ANTI-CHEMOFFICE ---
# Este bloque se ejecuta primero para limpiar la ruta de búsqueda de Python
# y eliminar la interferencia del software de PerkinElmer.
# =============================================================================
import sys

# La palabra clave a buscar en la ruta conflictiva
CHEMOFFICE_PATH_IDENTIFIER = "PerkinElmer"

# Creamos una nueva lista de rutas, excluyendo cualquiera que contenga el identificador
original_path_count = len(sys.path)
clean_sys_path = [
    path for path in sys.path 
    if CHEMOFFICE_PATH_IDENTIFIER not in path
]

# Si hemos eliminado alguna ruta, lo notificamos y aplicamos la limpieza
if len(clean_sys_path) < original_path_count:
    print("INFO: Se ha detectado y eliminado una ruta de ChemOffice que causaba conflictos.")
    sys.path = clean_sys_path

# =============================================================================
# --- FIN DEL PARCHE ---
# El resto del programa se ejecuta ahora en un entorno limpio.
# =============================================================================

# spectraconverter_v4/main.py

import tkinter as tk
from tkinterdnd2 import TkinterDnD 
from src.ui import MainAppWindow
from src.utils import resource_path
from PIL import Image, ImageTk

class SplashScreen(tk.Toplevel):
    """
    Ventana de carga con la lógica de escalado correcta:
    - Se reduce si es más grande que un % de la pantalla.
    - Nunca se muestra más grande que su tamaño original.
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent

        TRANSPARENT_COLOR = '#abcdef' 
        self.overrideredirect(True)
        self.wm_attributes('-transparentcolor', TRANSPARENT_COLOR)
        self.config(bg=TRANSPARENT_COLOR)

        try:
            splash_image_path = resource_path('assets/splashprofesional.png')
            pil_image = Image.open(splash_image_path)

            # --- LÓGICA DE ESCALADO CORREGIDA ---

            # Puedes ajustar este valor. 70% es un buen punto de partida.
            MAX_SCREEN_COVERAGE = 0.7 

            self.update_idletasks()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            image_width, image_height = pil_image.size

            # Calculamos el tamaño máximo permitido basado en el porcentaje de la pantalla
            max_allowed_width = int(screen_width * MAX_SCREEN_COVERAGE)
            max_allowed_height = int(screen_height * MAX_SCREEN_COVERAGE)
            
            # Calculamos el factor de escala. Si la imagen ya cabe, este factor será >= 1.0
            scale_factor = min(max_allowed_width / image_width, max_allowed_height / image_height)

            # Si el factor es < 1.0, significa que la imagen es demasiado grande y debemos reducirla.
            if scale_factor < 1.0:
                self.width = int(image_width * scale_factor)
                self.height = int(image_height * scale_factor)
                pil_image = pil_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            # Si el factor es >= 1.0, la imagen cabe perfectamente, así que usamos su tamaño original.
            else:
                self.width = image_width
                self.height = image_height

            self.splash_image = ImageTk.PhotoImage(pil_image)

        except Exception as e:
            print(f"ERROR: No se pudo cargar la imagen: {e}")
            self.splash_image = None
            self.width, self.height = 450, 250
            
        # Centrado y geometría
        x = (self.winfo_screenwidth() / 2) - (self.width / 2)
        y = (self.winfo_screenheight() / 2) - (self.height / 2)
        self.geometry(f'{self.width}x{self.height}+{int(x)}+{int(y)}')

        canvas = tk.Label(self, image=self.splash_image, bg=TRANSPARENT_COLOR, borderwidth=0)
        canvas.pack()


def main():
    """Función principal que lanza el splash y luego la app."""
    
    # Buena práctica para que la app se vea bien en pantallas con escala
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except (ImportError, AttributeError):
        pass

    root = TkinterDnD.Tk()
    root.withdraw() 
    
    splash = SplashScreen(root)
    splash.update()

    def launch_main_app():
        splash.destroy()
        MainAppWindow(root) 
        root.deiconify() 

    # --- CONTROL DE DURACIÓN CENTRALIZADO ---
    # Muestra la splash screen durante 4000 milisegundos (4 segundos)
    # y luego llama a la función para lanzar la app principal.
    # Puedes cambiar este número a tu gusto.
    root.after(4000, launch_main_app)
    
    root.mainloop()

if __name__ == "__main__":
    main()