import networkx as nx

def identify_articulation_points(G):
    """
    Identifica los puntos de articulación de la red.
    Un punto de articulación es un nodo cuya eliminación desconecta el grafo.
    """
    return list(nx.articulation_points(G))

def simulate_node_removal(G, node_id):
    """
    Simula la eliminación de un nodo (estación) y evalúa el impacto en la conectividad.
    Retorna el nuevo grafo y la información sobre componentes conectados.
    """
    G_copy = G.copy()
    if node_id in G_copy:
        G_copy.remove_node(node_id)
    
    is_connected = nx.is_connected(G_copy)
    num_components = nx.number_connected_components(G_copy)
    
    return {
        'new_graph': G_copy,
        'is_connected': is_connected,
        'num_components': num_components
    }

def simulate_edge_removal(G, source, target):
    """
    Simula la eliminación de una arista (tramo) y evalúa el impacto en la conectividad.
    """
    G_copy = G.copy()
    if G_copy.has_edge(source, target):
        G_copy.remove_edge(source, target)
        
    is_connected = nx.is_connected(G_copy)
    num_components = nx.number_connected_components(G_copy)
    
    return {
        'new_graph': G_copy,
        'is_connected': is_connected,
        'num_components': num_components
    }
