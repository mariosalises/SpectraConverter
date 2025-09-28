# spectraconverter_v4/src/data_processor.py

import pandas as pd
from scipy.signal import savgol_filter
from .pybaselines_local import airpls
import warnings

warnings.filterwarnings("ignore", "overflow encountered in exp", RuntimeWarning)

def process_spectrum(dataframe, processing_steps):
    """
    Aplica una serie de pasos de procesamiento a un dataframe.
    Esta versión es más simple y se adapta al nuevo flujo de trabajo.
    """
    df = dataframe.copy()

    # Primero aplicamos la normalización si se solicita (para Luminiscencia)
    if processing_steps.get('normalize'):
        max_intensity = df['intensity'].max()
        if max_intensity > 0:
            df['intensity'] = df['intensity'] / max_intensity

    # Luego aplicamos el método principal (corrección o suavizado)
    method = processing_steps.get('method')
    params = processing_steps.get('params', {})

    if method == 'min':
        baseline = df['intensity'].min()
        df['intensity'] -= baseline
    
    elif method == 'airpls':
        intensity_array = df['intensity'].to_numpy()
        baseline, _ = airpls(intensity_array, **params)
        df['intensity'] -= baseline

    elif method == 'moving_average':
        df['intensity'] = df['intensity'].rolling(window=params.get('window', 5), center=True, min_periods=1).mean()

    elif method == 'savgol':
        if params.get('window', 11) > params.get('order', 2):
            df['intensity'] = savgol_filter(df['intensity'], **params)

    return df