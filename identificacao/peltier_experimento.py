"""
    Backend da execução do experimento na placa térmica com sinal PRBS

    Esse script comunica-se com o servidor UA da placa terminca e aplica os sinais fornecidos por meio de
    arquivos de texto.

    Para visualizar a execução, execute peltier_viewer.py
"""

import asyncio
import time
import csv
import numpy as np
import sys
from asyncua import Client, ua

# --- Configurações Iniciais ---
# url = "opc.tcp://localhost:48030"
url = "opc.tcp://150.165.52.236:48030"
filename_input = "prbs_malha2.txt"
filename_output = "dados_processo2.csv"

# Parâmetros do Sinal
signal_offset = 0.5
signal_gain   = 0.2 * 100
ponto_operacao = 20
input_ts = 2.0  # Tempo de amostragem

# Nodes (IDs das variáveis no Servidor)
node_ids = {
    'PV1': "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV",
    'PV2': "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.PV",
    'MV1': "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.MV",
    'MV2': "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.MV",
}

# --- 1. Preparação do Sinal ---
print("--- PREPARAÇÃO ---")
try:
    raw_signal = np.loadtxt(filename_input, delimiter=',')
    print(f"Arquivo '{filename_input}' carregado com sucesso.")
except OSError:
    print(f"Aviso: '{filename_input}' não encontrado. Gerando sinal randômico de teste.")
    raw_signal = np.random.rand(50)
    exit()

# Cálculo do sinal final
input_signal = ponto_operacao   + signal_gain * (raw_signal - signal_offset)
# input_signal1 = ponto_operacao  + 30 * (raw_signal - signal_offset)
# input_signal2 = ponto_operacao  + 10 * (raw_signal - signal_offset)

pre_signal = ponto_operacao*np.ones(10)
input_signal = np.concatenate([pre_signal, input_signal, [0.0]])
# input_signal = np.concatenate([pre_signal, input_signal, input_signal1, input_signal2, [0.0]])

# from matplotlib.pyplot import plot, show
# plot(input_signal)
# show(block=True)

print(f"Total de amostras a executar: {len(input_signal)}")
print(f"Duração estimada: {len(input_signal) * input_ts} segundos ({len(input_signal) * input_ts / 60.0} minutos).")

resp = input("Deseja iniciar o processo real? [Y/N]: ").strip().upper()
if resp != 'Y':
    print("Operação cancelada.")
    sys.exit()

# input_signal = 50*np.ones(201)
# input_signal[60:] = 60
# input_signal[200] = 50


# --- 2. Loop de Controle (Async) ---
async def main_control_loop():
    client = Client(url=url)
    
    try:
        # Abre CSV para salvar dados imediatamente
        with open(filename_output, mode='w', newline='') as csv_file:
            fieldnames = ['Tempo_Relativo', 'PV1', 'PV2', 'CMD', 'MV1', 'MV2']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            
            print(f"Conectando OPC UA ({url})...")
            await client.connect()
            print("Conectado! Iniciando experimento...")
            
            # Pega os nodes
            nodes = {k: client.get_node(v) for k, v in node_ids.items()}
            
            start_time = time.time()
            
            # --- LOOP PRINCIPAL ---
            for idx, val_mv1 in enumerate(input_signal):
                iter_start = time.time()
                current_time = iter_start - start_time
                
                # 1. ESCRITA (Aplica o sinal na planta)
                try:
                    dv = ua.DataValue(ua.Variant(float(val_mv1), ua.VariantType.Double))
                    await nodes['MV2'].write_value(dv)
                    # await nodes['MV2'].write_value(0) # Garante MV2 em 0 se necessário
                except Exception as e:
                    print(f"Erro Write: {e}")

                # 2. LEITURA (Lê sensores)
                vals = {}
                try:
                    for name, node in nodes.items():
                        vals[name] = await node.read_value()
                except Exception as e:
                    print(f"Erro Read: {e}")
                    vals = {k: 0.0 for k in node_ids}

                # 3. SALVAR NO ARQUIVO
                # Salvamos linha a linha para garantir que se crachar, os dados até aqui estão salvos
                row_data = {
                    'Tempo_Relativo': f"{current_time:.2f}",
                    'PV1': vals['PV1'], 
                    'PV2': vals['PV2'],
                    'CMD': val_mv1,          # comando aplicado
                    'MV1': vals['MV1'],      # comando lido na MV1, se aplicado
                    'MV2': vals['MV2']       # comando lido na MV2, se aplicado
                }
                writer.writerow(row_data)
                csv_file.flush() # Força a gravação no disco
                
                print(f"[{idx+1}/{len(input_signal)}] T={current_time:.1f}s | MV1_CMD: {val_mv1:.1f} | PV1: {vals['PV1']:.1f} | MV2 {vals['MV2']:.1f}")
                
                # 4. CONTROLE DE TEMPO (Ts)
                elapsed = time.time() - iter_start
                sleep_time = max(0, input_ts - elapsed)
                await asyncio.sleep(sleep_time)
            # end for
                
    except Exception as e:
        print(f"\nERRO FATAL DURANTE O LOOP: {e}")
    finally:
        if client:
            try:
                await client.disconnect()
                print("Cliente OPC UA desconectado.")
            except:
                pass
        print(f"\nExperimento finalizado. Dados salvos em '{filename_output}'.")

if __name__ == "__main__":
    # Executa o loop assíncrono diretamente na thread principal
    asyncio.run(main_control_loop())