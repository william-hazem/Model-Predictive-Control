import asyncio
import threading
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from asyncua import Client, ua

url = "opc.tcp://localhost:48030"

nodes_read_ids =  ["ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV",
                  "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.PV",
]
nodes_write_ids = ["ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.MV",
                "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.MV"]

# Variáveis globais
times_read = []
values_read = {i: [] for i in range(len(nodes_read_ids))}
times_write = []
values_write = {i: [] for i in range(len(nodes_write_ids))}
labels_read = []
labels_write = []

client = None
nodes_read = []
nodes_write = []
loop = asyncio.new_event_loop()

# -------- OPC UA (async) --------
async def connect_opcua():
    global client, nodes_read, nodes_write
    client = Client(url=url)
    await client.connect()
    print("Conectado ao servidor OPC UA (async)")
    nodes_read = [client.get_node(nid) for nid in nodes_read_ids]
    nodes_write = [client.get_node(nid) for nid in nodes_write_ids]

async def read_values():
    try:
        vals = await asyncio.gather(*[n.read_value() for n in nodes_read])
        return vals
    except Exception as e:
        print("Erro leitura:", e)
        return [None] * len(nodes_read)

async def write_value(index, valor):
    try:
        await nodes_write[index].write_value(ua.Variant(valor, ua.VariantType.Double))
        print(f"Valor {valor} escrito no nó {nodes_write_ids[index]}")
    except Exception as e:
        print(f"Erro escrita no nó {nodes_write_ids[index]}:", e)

# -------- THREAD PARA OPC UA --------
def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_opcua())
    loop.run_forever()

# -------- TKINTER + MATPLOTLIB --------
root = tk.Tk()
root.title("Cliente OPC UA (asyncua) - Leitura e Escrita")

# Frame do gráfico
frame_grafico = ttk.Frame(root)
frame_grafico.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

fig, (ax_read, ax_write) = plt.subplots(2, 1, figsize=(8, 6))
plt.subplots_adjust(hspace=0.5)
canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Atualização do gráfico
def update(frame):
    # Ler valores
    future = asyncio.run_coroutine_threadsafe(read_values(), loop)
    vals = future.result(timeout=2)

    

    if any(v is not None for v in vals):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        times_read.append(now)

        for i, val in enumerate(vals):
            if val is not None:
                values_read[i].append(val)

            # Atualizar Labels com os últimos valores lidos
        for i, lbl in enumerate(labels_read):
            if len(values_read[i]) > 0:
                lbl.config(text=f"Lido: {values_read[i][-1]:.2f}")

        # Atualizar Labels com os últimos valores escritos
        for i, lbl in enumerate(labels_write):
            if len(values_write[i]) > 0:
                lbl.config(text=f"Escrito: {values_write[i][-1]:.2f}")

        # Gráfico superior - leituras
        ax_read.cla()
        times_plot = times_read[-50:]
        for i in range(len(nodes_read_ids)):
            values_plot = values_read[i][-50:]
            ax_read.plot(times_plot, values_plot, marker="o", label=f"Node {nodes_read_ids[i]}")
        ax_read.set_xlabel("Tempo")
        ax_read.set_ylabel("Valor")
        ax_read.set_title("Valores Lidos do Servidor")
        ax_read.tick_params(axis="x", rotation=45)
        ax_read.legend()

        # Gráfico inferior - valores escritos
        ax_write.cla()
        times_plot_w = times_write[-50:]
        for i in range(len(nodes_write_ids)):
            values_plot_w = values_write[i][-50:]
            ax_write.plot(times_plot_w, values_plot_w, marker="x", label=f"Node {nodes_write_ids[i]}")
        ax_write.set_xlabel("Tempo")
        ax_write.set_ylabel("Valor")
        ax_write.set_title("Valores Escritos no Servidor")
        ax_write.tick_params(axis="x", rotation=45)
        ax_write.legend()

ani = animation.FuncAnimation(fig, update, interval=1000)

# Frame inferior (entradas de dados para escrita)
frame_controle = ttk.Frame(root, padding=10)
frame_controle.pack(side=tk.BOTTOM, fill=tk.X)

entries = []

def enviar_valor(idx):
    try:
        novo_valor = float(entries[idx].get())
        # Atualiza lista local para plot
        now = datetime.datetime.now().strftime("%H:%M:%S")
        times_write.append(now)
        values_write[idx].append(novo_valor)
        # Envia para o servidor
        asyncio.run_coroutine_threadsafe(write_value(idx, novo_valor), loop)
        messagebox.showinfo("Sucesso", f"Valor {novo_valor} enviado ao nó {nodes_write_ids[idx]}")
    except ValueError:
        messagebox.showerror("Erro", "Digite um número válido!")



for i, nid in enumerate(nodes_write_ids):
    subframe = ttk.Frame(frame_controle)
    subframe.pack(fill=tk.X, pady=5)

    ttk.Label(subframe, text=f"Nó {nid} ->").pack(side=tk.LEFT, padx=5)
    entry = ttk.Entry(subframe, width=10)
    entry.pack(side=tk.LEFT, padx=5)
    entries.append(entry)

    btn = ttk.Button(subframe, text="Enviar", command=lambda i=i: enviar_valor(i))
    btn.pack(side=tk.LEFT, padx=5)

    # Label para mostrar valor lido
    lbl_read = ttk.Label(subframe, text="Lido: ---")
    lbl_read.pack(side=tk.LEFT, padx=5)
    labels_read.append(lbl_read)

    # Label para mostrar valor escrito
    lbl_write = ttk.Label(subframe, text="Escrito: ---")
    lbl_write.pack(side=tk.LEFT, padx=5)
    labels_write.append(lbl_write)

# Finalização correta
def on_closing():
    if client:
        loop.call_soon_threadsafe(loop.stop)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# -------- INICIAR THREAD ASYNC --------
threading.Thread(target=start_async_loop, args=(loop,), daemon=True).start()

# Inicia interface
root.mainloop()
