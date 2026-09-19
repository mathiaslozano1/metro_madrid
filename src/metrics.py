import networkx as nx

def calculate_degree(G):
    """Calcula el grado de todos los nodos (andenes)."""
    return dict(G.degree())

def calculate_betweenness_centrality(G):
    """Calcula la centralidad de intermediación de los andenes."""
    return nx.betweenness_centrality(G, weight='weight')

def calculate_density(G):
    """Calcula la densidad de la red."""
    return nx.density(G)

def calculate_diameter(G):
    """Calcula el diámetro de la red (en número de tramos)."""
    if nx.is_connected(G):
        return nx.diameter(G)
    else:
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        return nx.diameter(subgraph)

def aggregate_station_metrics(G):
    """
    Agrupa las métricas calculadas a nivel de andén para obtener los rankings 
    por estación física (sumando transbordos y centralidades).
    """
    grados = calculate_degree(G)
    centralidades = calculate_betweenness_centrality(G)
    
    estaciones_grados = {}
    estaciones_centralidad = {}
    
    for nodo, d in G.nodes(data=True):
        nombre = d.get('nombre', nodo)
        estaciones_grados[nombre] = estaciones_grados.get(nombre, 0) + grados.get(nodo, 0)
        estaciones_centralidad[nombre] = estaciones_centralidad.get(nombre, 0.0) + centralidades.get(nodo, 0.0)
        
    return {
        'grados_estacion': estaciones_grados,
        'centralidad_estacion': estaciones_centralidad
    }

def get_all_metrics(G):
    """Obtiene un diccionario con todas las métricas de la red."""
    station_agg = aggregate_station_metrics(G)
    return {
        'degree': calculate_degree(G),
        'betweenness_centrality': calculate_betweenness_centrality(G),
        'density': calculate_density(G),
        'diameter': calculate_diameter(G),
        'station_degree': station_agg['grados_estacion'],
        'station_betweenness': station_agg['centralidad_estacion']
    }
