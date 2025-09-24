# spectraconverter_v4/main.py

import tkinter as tk
from tkinterdnd2 import TkinterDnD 
from src.ui import MainAppWindow
from src.utils import resource_path

class SplashScreen(tk.Toplevel):
    """Ventana de carga que se muestra al iniciar la aplicación."""
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        
        try:
            # --- LÍNEA EDITADA AQUÍ ---
            # Cambiado 'splash.png' a 'splashprovisional.png'
            splash_image_path = resource_path('assets/splashprovisional.png')
            
            self.splash_image = tk.PhotoImage(file=splash_image_path)
            width, height = self.splash_image.width(), self.splash_image.height()
        except tk.TclError:
            self.splash_image = None
            width, height = 400, 200 # Tamaño por defecto si falla la imagen
            
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        self.overrideredirect(True) # Oculta bordes y barra de título

        if self.splash_image:
            tk.Label(self, image=self.splash_image).pack()
        else:
            tk.Label(self, text="Spectra Converter v4.0\nCargando...", font=("Arial", 16)).pack(expand=True)

def main():
    """Función principal que lanza el splash y luego la app."""
    
    root = TkinterDnD.Tk()
    root.withdraw() 
    
    splash = SplashScreen(root)

    # Forzamos a la interfaz a actualizarse AHORA MISMO para que el splash
    # sea visible inmediatamente, antes de que el 'after' empiece a contar.
    splash.update()

    def launch_main_app():
        splash.destroy()
        MainAppWindow(root) 
        root.deiconify() 

    root.after(3000, launch_main_app)
    root.mainloop()

if __name__ == "__main__":
    main()