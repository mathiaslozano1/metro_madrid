import networkx as nx
import unicodedata

def normalize_name(s):
    """Normaliza un texto quitando tildes, reemplazando guiones bajos y pasando a minúsculas."""
    if not isinstance(s, str):
        return ""
    s = s.replace('_', ' ').strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def resolve_station_nodes(G, query):
    """
    Encuentra los nodos correspondientes en el grafo a partir de una consulta.
    Soporta:
    - Nombres con guiones bajos ('nuevos_ministerios' -> 'Nuevos Ministerios')
    - Nombres sin tildes ('opera' -> 'Ópera')
    - IDs exactos ('Sol [L1]') o parciales ('sol')
    """
    if query in G:
        return [query]
        
    norm_query = normalize_name(query)
    
    # 1. Búsqueda exacta normalizada por atributo 'nombre'
    matches = [n for n, d in G.nodes(data=True) if normalize_name(d.get('nombre', '')) == norm_query]
    if matches:
        return matches
        
    # 2. Búsqueda por coincidencia en el ID del nodo normalizado
    matches = [n for n in G.nodes() if norm_query in normalize_name(n)]
    if matches:
        return matches
        
    # 3. Búsqueda parcial en el nombre
    matches = [n for n, d in G.nodes(data=True) if norm_query in normalize_name(d.get('nombre', ''))]
    if matches:
        return matches
        
    return []

def analyze_path(G, path):
    """
    Analiza un camino en el modelo Estación-Línea y extrae un itinerario detallado:
    - Paradas de tren
    - Transbordos realizados
    - Tiempos desglosados (tren vs transbordo)
    - Instrucciones paso a paso para el viajero
    """
    if not path or len(path) < 2:
        return {
            'path': path if path else [],
            'tiempo_total': 0.0,
            'tiempo_tren': 0.0,
            'tiempo_transbordo': 0.0,
            'num_paradas_tren': 0,
            'num_transbordos': 0,
            'lineas_usadas': [],
            'instrucciones': []
        }
        
    tiempo_tren = 0.0
    tiempo_transbordo = 0.0
    num_paradas_tren = 0
    num_transbordos = 0
    lineas_usadas = []
    instrucciones = []
    
    current_line = G.nodes[path[0]].get('linea')
    if current_line and current_line not in lineas_usadas:
        lineas_usadas.append(current_line)
        
    start_station = G.nodes[path[0]].get('nombre', path[0])
    current_segment_start = start_station
    current_segment_stops = 0
    current_segment_time = 0.0
    
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        edge_data = G.get_edge_data(u, v, default={})
        
        tipo = edge_data.get('tipo', 'via')
        t = edge_data.get('tiempo', 2.0)
        
        u_name = G.nodes[u].get('nombre', u)
        v_name = G.nodes[v].get('nombre', v)
        v_line = G.nodes[v].get('linea')
        
        if tipo == 'transbordo':
            tiempo_transbordo += t
            num_transbordos += 1
            
            # Cerrar el segmento de tren anterior si había paradas
            if current_segment_stops > 0:
                instrucciones.append(
                    f"Tomar Línea {current_line} desde '{current_segment_start}' hasta '{u_name}' "
                    f"({current_segment_stops} paradas, {current_segment_time:.1f} min)"
                )
                current_segment_stops = 0
                current_segment_time = 0.0
                
            instrucciones.append(
                f"Transbordo a pie en '{u_name}': cambiar de Línea {current_line} a Línea {v_line} "
                f"({t:.1f} min caminando)"
            )
            
            current_line = v_line
            if current_line not in lineas_usadas:
                lineas_usadas.append(current_line)
            current_segment_start = v_name
        else:
            tiempo_tren += t
            num_paradas_tren += 1
            current_segment_stops += 1
            current_segment_time += t
            
    # Cerrar el último tramo de tren
    if current_segment_stops > 0:
        last_station = G.nodes[path[-1]].get('nombre', path[-1])
        instrucciones.append(
            f"Tomar Línea {current_line} desde '{current_segment_start}' hasta '{last_station}' "
            f"({current_segment_stops} paradas, {current_segment_time:.1f} min)"
        )
        
    return {
        'path': path,
        'tiempo_total': round(tiempo_tren + tiempo_transbordo, 1),
        'tiempo_tren': round(tiempo_tren, 1),
        'tiempo_transbordo': round(tiempo_transbordo, 1),
        'num_paradas_tren': num_paradas_tren,
        'num_transbordos': num_transbordos,
        'lineas_usadas': lineas_usadas,
        'instrucciones': instrucciones
    }

def find_best_route(G, origin_station, destination_station, criteria='time'):
    """
    Busca la mejor ruta entre dos estaciones (acepta nombres comunes, con/sin tilde o guiones).
    Evalúa automáticamente todas las combinaciones de andenes de entrada y salida.
    
    criteria:
    - 'time': Minimiza el tiempo total en minutos (Dijkstra estándar).
    - 'transfers': Minimiza el número de cambios de línea (transbordos).
    """
    origin_nodes = resolve_station_nodes(G, origin_station)
    dest_nodes = resolve_station_nodes(G, destination_station)
    
    if not origin_nodes:
        raise ValueError(f"No se encontró la estación de origen: '{origin_station}'")
    if not dest_nodes:
        raise ValueError(f"No se encontró la estación de destino: '{destination_station}'")
        
    def transfer_weight(u, v, d):
        return 1000 if d.get('tipo') == 'transbordo' else 1
        
    best_analysis = None
    best_metric = float('inf')
    
    for o_node in origin_nodes:
        for d_node in dest_nodes:
            try:
                if criteria == 'time':
                    path = nx.dijkstra_path(G, o_node, d_node, weight='weight')
                    res = analyze_path(G, path)
                    if res and res['tiempo_total'] < best_metric:
                        best_metric = res['tiempo_total']
                        best_analysis = res
                else:
                    path = nx.dijkstra_path(G, o_node, d_node, weight=transfer_weight)
                    res = analyze_path(G, path)
                    if res:
                        metric = res['num_transbordos'] * 10000 + res['tiempo_total']
                        if metric < best_metric:
                            best_metric = metric
                            best_analysis = res
            except nx.NetworkXNoPath:
                continue
                
    return best_analysis

def shortest_path_dijkstra(G, source, target):
    """
    Calcula la ruta más corta minimizando el tiempo total.
    Soporta tanto nombres de estaciones ('Sol', 'sol') como IDs de nodos ('Sol [L1]').
    """
    if source in G and target in G:
        try:
            path = nx.dijkstra_path(G, source, target, weight='weight')
            time = nx.dijkstra_path_length(G, source, target, weight='weight')
            return path, round(time, 1)
        except nx.NetworkXNoPath:
            return None, float('inf')
    else:
        res = find_best_route(G, source, target, criteria='time')
        if res:
            return res['path'], res['tiempo_total']
        return None, float('inf')

def shortest_path_bfs(G, source, target):
    """
    Calcula la ruta minimizando paradas/transbordos.
    Soporta tanto nombres de estaciones como IDs de nodos.
    """
    if source in G and target in G:
        try:
            path = nx.shortest_path(G, source, target)
            return path, len(path) - 1
        except nx.NetworkXNoPath:
            return None, float('inf')
    else:
        res = find_best_route(G, source, target, criteria='transfers')
        if res:
            return res['path'], res['num_paradas_tren']
        return None, float('inf')

def compare_routes(G, origin_station, destination_station):
    """
    Compara la ruta por menor tiempo frente a la ruta por menores transbordos.
    Devuelve un diccionario 100% compatible con ambos formatos:
    - Nuevo: 'menor_tiempo', 'menores_transbordos'
    - Clásico: 'dijkstra', 'bfs'
    """
    route_time = find_best_route(G, origin_station, destination_station, criteria='time')
    route_transfers = find_best_route(G, origin_station, destination_station, criteria='transfers')
    
    time_path = route_time['path'] if route_time else []
    time_val = route_time['tiempo_total'] if route_time else float('inf')
    
    trans_path = route_transfers['path'] if route_transfers else []
    trans_stops = route_transfers['num_paradas_tren'] if route_transfers else 0
    
    return {
        'origen': origin_station,
        'destino': destination_station,
        'menor_tiempo': route_time,
        'menores_transbordos': route_transfers,
        # Claves de compatibilidad con versiones previas:
        'dijkstra': {
            'path': time_path,
            'time': time_val,
            'details': route_time
        },
        'bfs': {
            'path': trans_path,
            'stops': trans_stops,
            'details': route_transfers
        }
    }

if __name__ == "__main__":
    from graph_builder import load_data, build_metro_graph
    
    data = load_data('data/metro_madrid.json')
    G = build_metro_graph(data)
    
    # Probar con variaciones de nombres (minúsculas, guiones bajos, sin tilde)
    test_cases = [
        ("Sol", "Nuevos Ministerios"),
        ("sol", "nuevos_ministerios"),
        ("opera", "principe_pio"),
        ("Callao", "Plaza de Espana")
    ]
    
    for o, d in test_cases:
        res = compare_routes(G, o, d)
        print(f"\n{o} -> {d}:")
        print(f"  Dijkstra/Menor Tiempo: {res['dijkstra']['time']} min | Path: {len(res['dijkstra']['path'])} nodos")
        print(f"  BFS/Menores Transbordos: {res['bfs']['stops']} paradas | Path: {len(res['bfs']['path'])} nodos")
