import networkx as nx

def calculate_degree(G):
    """Calcula el grado de todos los nodos."""
    return dict(G.degree())

def calculate_betweenness_centrality(G):
    """Calcula la centralidad de intermediación de los nodos."""
    return nx.betweenness_centrality(G, weight='weight')

def calculate_density(G):
    """Calcula la densidad de la red."""
    return nx.density(G)

def calculate_diameter(G):
    """Calcula el diámetro de la red. Retorna inf si la red no está conectada."""
    if nx.is_connected(G):
        return nx.diameter(G)
    else:
        # Extraer el componente conectado más grande para calcular su diámetro
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        return nx.diameter(subgraph)

def get_all_metrics(G):
    """Obtiene un diccionario con todas las métricas de la red."""
    return {
        'degree': calculate_degree(G),
        'betweenness_centrality': calculate_betweenness_centrality(G),
        'density': calculate_density(G),
        'diameter': calculate_diameter(G)
    }
