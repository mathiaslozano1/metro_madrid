import json
import networkx as nx

def load_data(filepath):
    """Carga los datos de estaciones y conexiones desde un archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_metro_graph(data):
    """Construye un grafo de networkX a partir de los datos del metro."""
    G = nx.Graph()
    
    # Agregar nodos (estaciones)
    for estacion in data.get('estaciones', []):
        G.add_node(estacion['id'], 
                   nombre=estacion['nombre'], 
                   lineas=estacion['lineas'])
        
    # Agregar aristas (conexiones)
    for conexion in data.get('conexiones', []):
        G.add_edge(conexion['origen'], 
                   conexion['destino'], 
                   weight=conexion['tiempo'], 
                   linea=conexion['linea'])
        
    return G

if __name__ == "__main__":
    data = load_data('../data/metro_madrid.json')
    G = build_metro_graph(data)
    print(f"Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas.")
