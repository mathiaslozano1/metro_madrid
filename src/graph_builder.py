import json
import networkx as nx

def load_data(filepath):
    """Carga los datos de estaciones y conexiones desde un archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_metro_graph(data):
    """
    Construye el grafo del Metro de Madrid bajo el modelo Estación-Línea.
    Es 100% compatible con versiones previas (soporta tanto 'linea' como 'lineas').
    """
    G = nx.Graph()
    
    # Agregar nodos
    for estacion in data.get('estaciones', []):
        linea = estacion.get('linea', '')
        lineas = estacion.get('lineas', [linea] if linea else [])
        if not linea and lineas:
            linea = lineas[0]
            
        G.add_node(
            estacion['id'], 
            nombre=estacion.get('nombre', estacion['id']), 
            linea=linea,
            lineas=lineas,
            lat=estacion.get('lat', 0.0),
            lon=estacion.get('lon', 0.0)
        )
        
    # Agregar aristas
    for conexion in data.get('conexiones', []):
        tiempo = conexion.get('tiempo', 2.0)
        tipo = conexion.get('tipo', 'via')
        linea = conexion.get('linea', '')
        
        G.add_edge(
            conexion['origen'], 
            conexion['destino'], 
            weight=tiempo,
            tiempo=tiempo,
            linea=linea,
            tipo=tipo
        )
        
    return G

def get_station_platforms(G, station_name):
    """
    Devuelve la lista de nodos (andenes de cada línea) correspondientes a una estación física.
    Ejemplo: 'Sol' -> ['Sol [L1]', 'Sol [L2]', 'Sol [L3]']
    """
    target = station_name.strip().lower()
    matches = [n for n, d in G.nodes(data=True) if d.get('nombre', '').strip().lower() == target]
    return matches

def get_all_physical_stations(G):
    """Devuelve la lista ordenada de todos los nombres únicos de estaciones físicas."""
    names = set(d.get('nombre', '') for _, d in G.nodes(data=True) if d.get('nombre'))
    return sorted(list(names))

if __name__ == "__main__":
    data = load_data('data/metro_madrid.json')
    G = build_metro_graph(data)
    print(f"Grafo construido exitosamente: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas.")
