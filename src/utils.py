import sys
import os

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funciona tanto en desarrollo
    como para un ejecutable de PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si no, usa la ruta normal relativa al archivo utils.py
        # Sube un nivel para llegar a la carpeta raíz del proyecto
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(base_path, relative_path)