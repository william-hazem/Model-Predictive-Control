# Calculo dos coeficientes da série de Fourier para um sinal triangular não simétrico
# parametrizado pelo tempo de subida, e período

import math
import numpy as np

def compute_mean(ts, T, n):
    return 0.5

def compute_coef(n : int, ts : float, T : float):
    if n == 0:
        return 0.5
    # k = T**2 / (2*(T-ts)*ts*(math.pi*n)**2)
    pi =  np.pi
    cos = np.cos
    sin = np.sin

    omega_n = 2*pi*n/T
    k = 2 / T / (omega_n ** 2)

    a_n1 = cos(omega_n*ts) - 1
    a_n2 = cos(omega_n*ts) - 1 #cos(omega_n*T)
    a_n = a_n1 / ts + a_n2 / (T - ts)
    a_n = k * a_n

    b_n1 = sin(omega_n*ts)
    b_n2 = sin(omega_n*ts) - 0.0 #sin(omega_n*T)
    b_n = b_n1 / ts + b_n2 / (T - ts)
    b_n = k * b_n
    # a_n = k * (math.cos(2*math.pi*n*ts/T) - 1)

    # b_n = k * (math.sin(2*math.pi*n*ts/T) - 1)
    return a_n, b_n

def triangular(ts, T, n_max):
    
    map(compute_coef, range(0, n_max+1))