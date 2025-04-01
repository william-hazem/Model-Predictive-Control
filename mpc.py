from scipy.linalg import expm # função para calcular a exponencial de matrizes

from numpy import *

def discretize_system(A, B, C, T):
    """Discretiza o sistema contínuo com período de amostragem T."""
    A_d = expm(A * T)

    # Cálculo de B_d
    if linalg.matrix_rank(A) == A.shape[0]:  # Se A é inversível
        B_d = linalg.inv(A) @ (A_d - eye(A.shape[0])) @ B
    else:
        # Forma alternativa usando integração numérica
        n = 100  # Número de pontos de integração (ajustável)
        dt = T / n
        B_d = zeros_like(B, dtype=float64)  # Garante float64
        for i in range(n):
            B_d += expm(A * (i * dt)) * dt @ B

    return A_d, B_d, C  # C permanece o mesmo

def augmented_system(A_m, B_m, C_m):
    n = A_m.shape[0]        # número de estados do sistema
    o_m = zeros((1, n))
    _1 = ones((1, 1))
    # para concatenar matrizes em python, usar hstack e vstack

    A = vstack([
        hstack([A_m, o_m.T]),      # Parte superior de A
        hstack([C_m @ A_m, _1]) # Parte inferior de A
    ])

    B = vstack([
        B_m,
        C_m @ B_m
    ])

    C = hstack([o_m, [[1]]])
    return A, B, C

def compute_FPhi(A, B, C, N_p, N_c):
  n = A.shape[0]
  F = zeros((N_p, n))
  Phi = zeros((N_p, N_c))

  for i in range(0, N_p):
    F[i] = C @ linalg.matrix_power(A, i + 1) # i começa em 0 e vai até N_p - 1
    temp = zeros((1, N_c))
    for c in range(0, N_c):
      if c > i:
        break
      # aplica a formula apenas para os elementos da triangular inferior
      # A potência em A na primeira coluna é igual ao número da linha -1
      # para cada coluna seguinte a potência é reduzida em 1, (-2) na segunda coluna, ... (-c) na c-ésima coluna
      temp[:, c] = C @ linalg.matrix_power(A, i - c) @ B
    Phi[i] = temp