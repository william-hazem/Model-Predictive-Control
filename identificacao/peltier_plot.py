import numpy as np
import matplotlib.pyplot as plt

file = input("Arquivo de dados: ")

data_raw = np.loadtxt(file, delimiter=',', skiprows=1)
print(data_raw.shape)

data = {
    'mv1': data_raw[:, 1],
    'mv2': data_raw[:, 2],
    'pv1': data_raw[:, 3],
    'pv2': data_raw[:, 4]
}

ts = float(input("Tempo de amostragem [s]: "))
N = len(data['mv1'])
t = np.linspace(0, N*ts, N)

fig, axs = plt.subplots(2, 1, figsize=(10, 8))

ax1, ax2 = axs.ravel()

ax1.plot(t,data['pv1'], label='PV1')
ax1.plot(t,data['pv2'], label='PV2')

ax2.plot(t,data['mv1'], label='MV2')
ax2.plot(t,data['mv2'], label='MV2')

ax1.legend()

for ax in axs:
    ax.set_xlabel('t [s]')
fig.show(True)

input('Pressione Enter')