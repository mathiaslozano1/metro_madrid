import networkx as nx

def shortest_path_dijkstra(G, source, target):
    """
    Encuentra la ruta más corta entre dos estaciones utilizando el algoritmo de Dijkstra,
    minimizando el tiempo (peso de las aristas).
    """
    try:
        path = nx.dijkstra_path(G, source, target, weight='weight')
        time = nx.dijkstra_path_length(G, source, target, weight='weight')
        return path, time
    except nx.NetworkXNoPath:
        return None, float('inf')

def shortest_path_bfs(G, source, target):
    """
    Encuentra la ruta más corta en términos de número de transbordos/paradas
    utilizando búsqueda en anchura (BFS).
    """
    try:
        path = nx.shortest_path(G, source, target)
        stops = len(path) - 1
        return path, stops
    except nx.NetworkXNoPath:
        return None, float('inf')

def compare_routes(G, source, target):
    """Compara las rutas por tiempo (Dijkstra) y por paradas (BFS)."""
    dijkstra_path, time = shortest_path_dijkstra(G, source, target)
    bfs_path, stops = shortest_path_bfs(G, source, target)
    
    return {
        'dijkstra': {'path': dijkstra_path, 'time': time},
        'bfs': {'path': bfs_path, 'stops': stops}
    }
