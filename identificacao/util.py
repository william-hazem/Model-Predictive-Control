import numpy as np
import matplotlib.pyplot as plt

def carregar_dados(path: str):
    raw = np.loadtxt(path, delimiter=',', skiprows=1)
    formated = {
        "t":   raw[:, 0],
        "pv1": raw[:, 1],
        "pv2": raw[:, 2],
        "mv1": raw[:, 3],
        "mv2": raw[:, 4],
    }
    return formated

def plot_pv_mv(dados, f=lambda x: x):
    """
        Plota em dois gráficos distintos a PV e a MV do processo
        @input dados dados estruturados da t, PV e MV
        @f     função de preprocessamento dos dados
    """
    fig, (ax_pv, ax_mv) = plt.subplots(2, 1, sharex=True)
    t = dados["t"]
    ax_pv.set_ylabel("Temperatura [°C]")
    ax_mv.set_ylabel("PWM [%]")
    ax_mv.set_xlabel("Tempo [min.]")
    ax_pv.plot(t, f(dados["pv1"]), label="PV1")
    ax_pv.plot(t, f(dados["pv2"]), label="PV2")
    ax_mv.plot(t, f(dados["mv1"]), label="MV1")
    ax_mv.plot(t, f(dados["mv2"]), label="MV2")

    ax_pv.legend()
    ax_mv.legend()
    return fig, (ax_pv, ax_mv)


def remover_valor_inicial(arr: np.array):
    return arr - arr[0]