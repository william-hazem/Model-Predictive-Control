import asyncio
import threading
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from asyncua import Client
import sys

# --- Configurações ---
URL = "opc.tcp://localhost:48030"
REFRESH_RATE_MS = 2000  # Atualização do gráfico (ms)
WINDOW_SIZE =2000       # Janela de tempo móvel (segundos) para manter no gráfico

# Nodes (Mesmos IDs do seu código)
NODE_IDS = {
    'PV1': "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV",
    'PV2': "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.PV",
    'MV1': "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.MV",
    'MV2': "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.MV"
}

# --- Dados Compartilhados (Thread Safe Logic) ---
class DataStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.reset_data()

    def reset_data(self):
        with self.lock:
            self.start_time = time.time()
            self.time = []
            self.pv1 = []
            self.pv2 = []
            self.mv1 = []
            self.mv2 = []
            print("Dados limpos.")

    def add_data(self, pv1, pv2, mv1, mv2):
        t = time.time() - self.start_time
        with self.lock:
            self.time.append(t)
            self.pv1.append(pv1)
            self.pv2.append(pv2)
            self.mv1.append(mv1)
            self.mv2.append(mv2)
            
            # Limpeza automática para não pesar a memória (Janela deslizante)
            # Remove dados mais velhos que WINDOW_SIZE + margem
            if t > (WINDOW_SIZE + 10):
                 # Mantém apenas os últimos pontos que cabem na janela visual
                 # Isso é opcional, mas bom para longas durações
                 pass 

    def get_data(self):
        # Retorna uma cópia dos dados para evitar conflito de thread no plot
        with self.lock:
            return (list(self.time), list(self.pv1), list(self.pv2), 
                    list(self.mv1), list(self.mv2))

store = DataStore()
monitoring = True

# --- Thread de Comunicação OPC UA ---
async def opc_worker():
    print(f"Monitor: Tentando conectar em {URL}...")
    client = Client(url=URL)
    try:
        await client.connect()
        print("Monitor: Conectado ao OPC UA!")
        
        nodes = {k: client.get_node(v) for k, v in NODE_IDS.items()}
        
        while monitoring:
            try:
                # Leitura em lote é mais eficiente
                vals = []
                for key in ['PV1', 'PV2', 'MV1', 'MV2']:
                    val = await nodes[key].read_value()
                    vals.append(val)
                
                store.add_data(vals[0], vals[1], vals[2], vals[3])
                
            except Exception as e:
                print(f"Erro na leitura: {e}")
                await asyncio.sleep(1) # Espera um pouco antes de tentar de novo
            
            await asyncio.sleep(0.2) # Taxa de amostragem do monitor
            
    except Exception as e:
        print(f"Erro de conexão no Monitor: {e}")
    finally:
        try:
            await client.disconnect()
        except:
            pass
        print("Monitor desconectado.")

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(opc_worker())

# --- Interface Gráfica (Matplotlib) ---
def start_gui():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    plt.subplots_adjust(bottom=0.2) # Espaço para os botões
    fig.canvas.manager.set_window_title('Monitoramento OPC UA (Visualizador)')

    # Estilos
    ax1.set_ylabel('Temperatura (°C)')
    ax1.grid(True, linestyle=':')
    ax1.set_ylim(20, 70)
    
    ax2.set_ylabel('Comando (%)')
    ax2.set_xlabel('Tempo (s)')
    ax2.grid(True, linestyle=':')
    ax2.set_ylim(-5, 105)

    # Linhas iniciais
    l_pv1, = ax1.plot([], [], 'r-', label='PV1', linewidth=2)
    l_pv2, = ax1.plot([], [], 'b-', label='PV2', alpha=0.6)
    l_mv1, = ax2.plot([], [], 'r--', label='MV1', linewidth=2)
    l_mv2, = ax2.plot([], [], 'b--', label='MV2', alpha=0.6)
    
    ax1.legend(loc='upper right')
    ax2.legend(loc='upper right')

    def update(frame):
        # 1. Pega cópia segura dos dados
        t, pv1, pv2, mv1, mv2 = store.get_data()
        
        if not t: return l_pv1, l_pv2, l_mv1, l_mv2

        # 2. Segurança contra vetores de tamanhos diferentes (Causa raiz do seu crash anterior)
        min_len = min(len(t), len(pv1), len(pv2), len(mv1), len(mv2))
        t = t[:min_len]
        pv1 = pv1[:min_len]
        pv2 = pv2[:min_len]
        mv1 = mv1[:min_len]
        mv2 = mv2[:min_len]

        # 3. Atualiza Linhas
        l_pv1.set_data(t, pv1)
        l_pv2.set_data(t, pv2)
        l_mv1.set_data(t, mv1)
        l_mv2.set_data(t, mv2)

        # 4. Ajuste de Escala X (Janela deslizante)
        if t[-1] > WINDOW_SIZE:
            ax1.set_xlim(t[-1] - WINDOW_SIZE, t[-1] + 2)
            ax2.set_xlim(t[-1] - WINDOW_SIZE, t[-1] + 2)
        else:
            ax1.set_xlim(0, max(10, t[-1] + 2))
            ax2.set_xlim(0, max(10, t[-1] + 2))

        return l_pv1, l_pv2, l_mv1, l_mv2

    # --- Botões ---
    # Botão Limpar
    ax_clear = plt.axes([0.7, 0.05, 0.1, 0.075])
    btn_clear = Button(ax_clear, 'Limpar')
    
    def on_clear(event):
        store.reset_data()
    btn_clear.on_clicked(on_clear)

    # Botão Salvar
    ax_save = plt.axes([0.81, 0.05, 0.1, 0.075])
    btn_save = Button(ax_save, 'Salvar Fig')

    def on_save(event):
        nome = f"monitor_print_{int(time.time())}.png"
        plt.savefig(nome)
        print(f"Imagem salva como {nome}")
    btn_save.on_clicked(on_save)

    ani = animation.FuncAnimation(fig, update, interval=REFRESH_RATE_MS, blit=False, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    # 1. Inicia thread de dados OPC
    opc_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_background_loop, args=(opc_loop,), daemon=True)
    t.start()
    
    # 2. Inicia GUI na thread principal
    try:
        start_gui()
    except KeyboardInterrupt:
        pass
    
    monitoring = False
    print("Encerrando monitor...")