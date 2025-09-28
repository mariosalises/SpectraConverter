import sys
import inspect
try:
    import pybaselines
    from pybaselines.whittaker import airpls
except ImportError:
    pybaselines = None
    airpls = None

print("\n--- DIAGNÓSTICO DEFINITIVO DEL ENTORNO DE PYTHON ---")

# 1. ¿Qué ejecutable de Python estamos usando?
print(f"\n[1] Python Executable (sys.executable):\n    {sys.executable}")

# 2. ¿Qué versión de Python es?
print(f"\n[2] Python Version (sys.version):\n    {sys.version}")

# 3. ¿Dónde está buscando Python los módulos? (El más importante)
print("\n[3] Rutas de Búsqueda de Módulos (sys.path):")
for i, path in enumerate(sys.path):
    print(f"    {i}: {path}")

# 4. ¿Qué información nos da la librería pybaselines si la encuentra?
if pybaselines:
    print("\n[4] Información de la librería 'pybaselines' encontrada:")
    print(f"    Versión reportada (__version__): {pybaselines.__version__}")
    print(f"    Ubicación del paquete (__file__): {pybaselines.__file__}")
    if airpls:
        try:
            signature = inspect.signature(airpls)
            print(f"    Firma de 'airpls' encontrada: {signature}")
        except Exception as e:
            print(f"    No se pudo obtener la firma de 'airpls': {e}")
    else:
        print("    La función 'airpls' no se pudo importar desde pybaselines.whittaker.")
else:
    print("\n[4] No se pudo importar la librería 'pybaselines'.")

print("\n--- FIN DEL DIAGNÓSTICO ---")