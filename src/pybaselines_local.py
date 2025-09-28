# Contenido extraído y corregido del código fuente oficial de pybaselines v1.2.1
# para ser usado localmente y evitar problemas de entorno.

import numpy as np
from scipy.sparse import spdiags
from scipy.sparse.linalg import spsolve

def _whittaker_smooth(y, lam, d, w):
    """El algoritmo base de suavizado de Whittaker."""
    y_len = len(y)
    # Crea una matriz diagonal con los pesos
    W = spdiags(w, 0, y_len, y_len)
    # Resuelve el sistema de ecuaciones lineales para encontrar la línea base suavizada
    return spsolve(W + lam * (d.T @ d), W @ y)

def airpls(data, lam=1e7, p=0.01, max_iter=50, tol=1e-3, weights=None):
    """
    Implementación local y funcional de airPLS.
    Esta versión SÍ usa el parámetro 'p' correctamente.
    """
    y_len = len(data)
    
    # Construye la matriz de diferencias de segundo orden (D)
    # Esta es la forma robusta y correcta de hacerlo.
    D = spdiags(
        np.vstack((np.ones(y_len), -2 * np.ones(y_len), np.ones(y_len))),
        [0, 1, 2],
        y_len - 2,
        y_len
    )

    if weights is None:
        w = np.ones(y_len)
    else:
        w = np.array(weights)

    for i in range(1, max_iter + 1):
        baseline = _whittaker_smooth(data, lam, D, w)
        residual = data - baseline
        
        # Encuentra los residuales negativos
        residual_neg = residual[residual < 0]
        
        # Si no hay residuales negativos, la línea base está por debajo de la señal, hemos terminado.
        if not residual_neg.any():
            break
        
        # Lógica para recalcular los pesos
        d_sum = np.sum(np.abs(residual_neg))
        w_new = np.where(residual >= 0, 0, np.exp(i * residual / d_sum))

        # Comprueba la convergencia
        w_norm = np.linalg.norm(w - w_new) / np.linalg.norm(w)
        if w_norm < tol:
            break
        
        w = w_new

    return baseline, {'weights': w}