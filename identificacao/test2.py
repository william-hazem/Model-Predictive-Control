import asyncio
import csv
import signal
import sys
from asyncua import Client
import matplotlib.pyplot as plt
from datetime import datetime
import time
URL = "opc.tcp://localhost:48030"  # altere para seu servidor

NODE_PV1 = "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV"  # altere para seus NodeIds reais
NODE_PV2 = "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.PV"
NODE_MV1 = "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.MV"
NODE_MV2 = "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.MV"

# Variáveis globais para dados
times, pv1_values, pv2_values, mv1_values, mv2_values = [], [], [], [], []
running = True  # flag para controlar loop

def save_data_and_fig():
    """Salvar CSV e figura"""
    filename_csv = "pv_mv_data.csv"
    filename_fig = "pv_mv_plot.png"
    
    # Salvar CSV
    with open(filename_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["timestamp", "PV1", "PV2", "MV1", "MV2"])
        for t, pv1, pv2, mv1, mv2 in zip(times, pv1_values, pv2_values, mv1_values, mv2_values):
            csv_writer.writerow([t, pv1, pv2, mv1, mv2])
    
    # Salvar figura
    fig, (ax_pv, ax_mv) = plt.subplots(2, 1, figsize=(10, 8))
    ax_pv.plot(times, pv1_values, label="PV1")
    ax_pv.plot(times, pv2_values, label="PV2")
    ax_pv.set_title("PV")
    ax_pv.legend()
    ax_pv.set_xlabel("Time")
    ax_pv.set_ylabel("Value")

    ax_mv.plot(times, mv1_values, label="MV1")
    ax_mv.plot(times, mv2_values, label="MV2")
    ax_mv.set_title("MV")
    ax_mv.legend()
    ax_mv.set_xlabel("Time")
    ax_mv.set_ylabel("Value")

    fig.autofmt_xdate()
    plt.tight_layout()
    fig.savefig(filename_fig)
    print(f"\nDados salvos em {filename_csv} e gráfico em {filename_fig}")

def signal_handler(sig, frame):
    global running
    print("\nInterrupção recebida, encerrando...")
    running = False

async def main():
    global running
    
    

    async with Client(URL) as client:
        pv_nodes = [client.get_node(NODE_PV1), client.get_node(NODE_PV2)]
        mv_nodes = [client.get_node(NODE_MV1), client.get_node(NODE_MV2)]

        plt.ion()
        global fig
        fig, (ax_pv, ax_mv) = plt.subplots(2, 1, figsize=(10, 8))

        # Criar linhas vazias
        line_pv1, = ax_pv.plot([], [], label="PV1")
        line_pv2, = ax_pv.plot([], [], label="PV2")
        ax_pv.set_title("PV")
        ax_pv.set_xlabel("Time")
        ax_pv.set_ylabel("Value")
        ax_pv.legend()

        line_mv1, = ax_mv.plot([], [], label="MV1")
        line_mv2, = ax_mv.plot([], [], label="MV2")
        ax_mv.set_title("MV")
        ax_mv.set_xlabel("Time")
        ax_mv.set_ylabel("Value")
        ax_mv.legend()

        t0 = datetime.now()

        while running:
            try:
                pv_values = [await node.read_value() for node in pv_nodes]
                mv_values = [await node.read_value() for node in mv_nodes]
                timestamp = datetime.now()
                minutes = (timestamp - t0).total_seconds() / 60.0
                times.append(minutes)

                pv1_values.append(pv_values[0])
                pv2_values.append(pv_values[1])
                mv1_values.append(mv_values[0])
                mv2_values.append(mv_values[1])

                # Atualizar linhas existentes
                line_pv1.set_data(times, pv1_values)
                line_pv2.set_data(times, pv2_values)
                line_mv1.set_data(times, mv1_values)
                line_mv2.set_data(times, mv2_values)

                # Ajustar limites automaticamente
                ax_pv.relim()
                ax_pv.autoscale_view()
                ax_mv.relim()
                ax_mv.autoscale_view()

                plt.pause(1)
            except Exception as e:
                print("Erro na leitura:", e)
                await asyncio.sleep(1)

        save_data_and_fig()

if __name__ == "__main__":
    # Captura Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    # Captura fechamento da janela do matplotlib
    # plt.ion()
    fig = plt.figure()
    fig.canvas.mpl_connect('close_event', lambda event: signal_handler(None, None))

    asyncio.run(main())
