import asyncio
from asyncua import Client, ua

url = 'opc.tcp://localhost:48030/server'
# Configuração do servidor OPC UA
url = "opc.tcp://localhost:48030"
nodes_read_ids =  ["ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV"
                ,"ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV"]   # Nó para leitura
nodes_write_ids = ["ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV",
                "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV"]
async def connect_opcua():
    global client, node_read, node_write
    client = Client(url=url)
    await client.connect()
    print("Conectado ao servidor OPC UA (async)")
    # node_read = client.get_node(node_read_id)
    node_write = client.get_node(nodes_write_ids[0])
    value = await node_write.read_value()
    # await node_write.write_value(value - 10)
    print(value, type(value))
    new_value = value - 10
    await node_write.write_value(new_value, ua.VariantType.Double)


# loop = asyncio.new_event_loop()
asyncio.run(connect_opcua())

NODE_PV1 = "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.PV"  # altere para seus NodeIds reais
NODE_PV2 = "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.PV"
NODE_MV1 = "ns=2;s=0:PlacaTermica.Malha1?PlacaTermica.Malha1.MV"
NODE_MV2 = "ns=2;s=0:PlacaTermica.Malha2?PlacaTermica.Malha2.MV"