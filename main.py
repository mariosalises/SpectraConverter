# =============================================================================
# --- INICIO DEL PARCHE ANTI-CHEMOFFICE ---
# =============================================================================
import sys

CHEMOFFICE_PATH_IDENTIFIER = "PerkinElmer"
original_path_count = len(sys.path)
clean_sys_path = [
    path for path in sys.path 
    if CHEMOFFICE_PATH_IDENTIFIER not in path
]

if len(clean_sys_path) < original_path_count:
    print("INFO: Se ha detectado y eliminado una ruta de ChemOffice que causaba conflictos.")
    sys.path = clean_sys_path
# =============================================================================
# --- FIN DEL PARCHE ---
# =============================================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD 
from src.ui import MainAppWindow
from src.utils import resource_path
from PIL import Image, ImageTk

# --- INICIO DEL CÓDIGO DE TUFUP ---
import os
import tempfile
from tufup.client import Client
from version import __version__

def check_for_updates():
    APP_NAME = 'SpectraConverter'
    
    # Directorio donde se ejecuta el .exe
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(__file__)

    # Directorio para descargar los metadatos de actualización
    metadata_dir = tempfile.mkdtemp()
    
    # Directorio donde guardamos el 'root.json' de confianza dentro del .exe
    local_metadata_dir = os.path.join(current_dir, 'metadata')

    client = Client(
        app_name=APP_NAME,
        app_version=__version__,
        repo_url='https://github.com/mariosalises/SpectraConverter/releases/latest/download',
        current_dir=current_dir,
        metadata_dir=metadata_dir,
        local_metadata_dir=local_metadata_dir
    )
    
    # Comprueba si hay actualizaciones
    if client.check_for_updates():
        latest_version = client.get_latest_version()
        if messagebox.askyesno("Actualización Disponible", f"Hay una nueva versión ({latest_version}) disponible. ¿Quieres descargar e instalar?"):
            client.update() # Descarga, instala y reinicia.

# --- FIN DEL CÓDIGO DE TUFUP ---


class SplashScreen(tk.Toplevel):
    """
    Ventana de carga simple, auto-escalable y con esquinas redondeadas.
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

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            image_width, image_height = pil_image.size
            max_allowed_width = int(screen_width * 0.7)
            max_allowed_height = int(screen_height * 0.7)
            scale_factor = min(max_allowed_width / image_width, max_allowed_height / image_height)

            if scale_factor < 1.0:
                self.width = int(image_width * scale_factor)
                self.height = int(image_height * scale_factor)
                pil_image = pil_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
            else:
                self.width = image_width
                self.height = image_height

            self.splash_image = ImageTk.PhotoImage(pil_image)

        except Exception as e:
            print(f"ERROR: No se pudo cargar o reescalar la imagen: {e}")
            self.splash_image = None
            self.width, self.height = 450, 250
            
        x = (self.winfo_screenwidth() / 2) - (self.width / 2)
        y = (self.winfo_screenheight() / 2) - (self.height / 2)
        self.geometry(f'{self.width}x{self.height}+{int(x)}+{int(y)}')

        canvas = tk.Label(self, image=self.splash_image, bg=TRANSPARENT_COLOR, borderwidth=0)
        canvas.pack()


def main():
    """Función principal que lanza el splash y luego la app."""
    
    root = TkinterDnD.Tk()
    root.tk.call('tk', 'scaling', 1.0)
    root.withdraw() 
    
    splash = SplashScreen(root)
    splash.update()

    def launch_main_app():
        splash.destroy()
        MainAppWindow(root) 
        root.deiconify() 

    root.after(4000, launch_main_app)
    root.mainloop()

if __name__ == "__main__":
    # Solo comprobamos si es un .exe para no hacerlo en desarrollo
    if getattr(sys, 'frozen', False):
        try:
            check_for_updates()
        except Exception as e:
            # Usamos un messagebox para que el usuario vea el error si algo falla
            messagebox.showerror("Error de Actualización", f"No se pudo comprobar si hay actualizaciones:\n\n{e}")
    main()