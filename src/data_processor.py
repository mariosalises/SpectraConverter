# spectraconverter_v4/src/data_processor.py

import pandas as pd
from scipy.signal import savgol_filter
from pybaselines.whittaker import airpls

def process_spectrum(dataframe, method, params):
    """
    Aplica un método de procesamiento a un único espectro.

    Args:
        dataframe (pd.DataFrame): El DataFrame con los datos crudos.
        method (str): El método a aplicar ('min', 'airpls', 'moving_average', 'savgol').
        params (dict): Un diccionario con los parámetros para el método.

    Returns:
        pd.DataFrame: Un nuevo DataFrame con los datos procesados.
    """
    df = dataframe.copy()
    processed_intensity = df['intensity'].copy()

    if method == 'min':
        baseline = processed_intensity.min()
        processed_intensity -= baseline
        
    elif method == 'airpls':
        # Extraemos los parámetros, con valores por defecto por si acaso
        lam = params.get('lam', 1e7)
        p = params.get('p', 0.01)
        baseline, _ = airpls(processed_intensity, lam=lam, p=p)
        processed_intensity -= baseline
        
    elif method == 'moving_average':
        window = params.get('window', 5)
        # Usamos rolling.mean(), asegurando que el centro esté alineado y los bordes se rellenen
        processed_intensity = processed_intensity.rolling(window=window, center=True, min_periods=1).mean()
        
    elif method == 'savgol':
        window = params.get('window', 11)
        order = params.get('order', 2)
        # Savitzky-Golay requiere que la ventana sea mayor que el orden
        if window > order:
            processed_intensity = savgol_filter(processed_intensity, window, order)
            
    # Creamos un nuevo DataFrame con el resultado
    processed_df = pd.DataFrame({
        'wavelength': df['wavelength'],
        'intensity': processed_intensity
    })
    
    return processed_df