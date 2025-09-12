import math

def compute_mean(ts, T, n):
    return 0.5

def compute_coef(ts, T, n):
    a_n = 0
    b_n = 0

    k = T**2 / (2*(T-ts)*ts*(math.pi*n)**2)

    a_n = k * (math.cos(2*math.pi*n*ts/T) - 1)
    b_n = k * (math.sin(2*math.pi*n*ts/T) - 1)
    
    return a_n, b_n

def triangular(ts, T, n_max):
    
    map(compute_coef, range(0, n_max+1))