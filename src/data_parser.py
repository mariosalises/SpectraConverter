# spectraconverter_v4/src/data_parser.py

import pandas as pd
import os

def _find_data_start(file_path):
    """
    Función auxiliar que examina un archivo para encontrar la primera línea
    que contiene datos numéricos de al menos dos columnas.
    
    Args:
        file_path (str): La ruta al archivo a analizar.

    Returns:
        int: El número de la línea donde comienzan los datos (0-indexed),
             o -1 si no se encuentran datos válidos.
    """
    try:
        # Usamos 'errors=ignore' para evitar problemas con caracteres extraños en los encabezados
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                # Ignoramos líneas vacías o que solo contengan espacios
                if not line.strip():
                    continue
                
                # Dividimos la línea por cualquier espacio en blanco y filtramos partes vacías
                parts = [part for part in line.strip().split() if part]
                
                # Si hay al menos dos "palabras" o columnas en la línea...
                if len(parts) >= 2:
                    try:
                        # ... intentamos convertir las dos primeras a números.
                        float(parts[0].replace(',', '.')) # Reemplazamos comas por puntos (decimal europeo)
                        float(parts[1].replace(',', '.'))
                        # Si tiene éxito, hemos encontrado el inicio de los datos.
                        return i
                    except (ValueError, IndexError):
                        # Si falla la conversión, es una línea de texto, así que continuamos.
                        continue
    except Exception as e:
        print(f"Error al leer el archivo {file_path}: {e}")
    
    # Si recorremos todo el archivo y no encontramos datos, devolvemos -1.
    return -1


def parse_spectrum_file(file_path):
    """
    Parsea un archivo de espectro, detectando automáticamente el inicio de los datos.

    Args:
        file_path (str): La ruta completa al archivo .txt o .asc.

    Returns:
        pd.DataFrame: Un DataFrame con columnas 'wavelength' e 'intensity' si tiene éxito,
                      o None si el archivo no se puede parsear.
    """
    # 1. Realizamos el trabajo de detective para encontrar la primera línea de datos.
    start_line = _find_data_start(file_path)
    
    # 2. Si no se encontraron datos, devolvemos None para indicar el fallo.
    if start_line == -1:
        print(f"Aviso: No se encontraron datos numéricos válidos en {os.path.basename(file_path)}")
        return None
        
    try:
        # 3. Usamos pandas para leer el archivo de forma eficiente, saltando el encabezado.
        df = pd.read_csv(
            file_path,
            skiprows=start_line,
            header=None,
            sep=r'\s+',  # Forma moderna y robusta de manejar espacios/tabs como separadores
            usecols=[0, 1],
            names=['wavelength', 'intensity'],
            engine='python', # El motor 'python' es más lento pero mejor manejando separadores complejos
            decimal=','      # Intentamos manejar la coma como decimal si existe
        )
        
        # 4. Limpieza final: nos aseguramos de que todo sea numérico y eliminamos filas malas.
        #    'coerce' convertirá en NaN (Not a Number) cualquier cosa que no pueda ser un número.
        df['wavelength'] = pd.to_numeric(df['wavelength'], errors='coerce')
        df['intensity'] = pd.to_numeric(df['intensity'], errors='coerce')
        
        # Eliminamos cualquier fila que tenga NaN en cualquiera de las dos columnas.
        df.dropna(inplace=True)
        
        # Si después de la limpieza el DataFrame está vacío, no es útil.
        if df.empty:
            print(f"Aviso: El DataFrame está vacío después de limpiar {os.path.basename(file_path)}")
            return None
            
        return df
        
    except Exception as e:
        print(f"Error al parsear {os.path.basename(file_path)} con pandas: {e}")
        return None