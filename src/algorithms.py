import networkx as nx
import unicodedata

def normalize_name(s):
    """Normaliza un texto quitando tildes, reemplazando guiones bajos y pasando a minúsculas."""
    if not isinstance(s, str):
        return ""
    s = s.replace('_', ' ').strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

class FormattedTime(float):
    """
    Representa un tiempo en minutos:
    - Se comporta numéricamente como float (permite sumas, comparaciones, etc.)
    - Al imprimirse (str o f-string) se formatea automáticamente como 'MM:SS' (minutos:segundos).
    """
    def __new__(cls, val):
        if val is None or val == float('inf'):
            return super().__new__(cls, 0.0)
        return super().__new__(cls, float(val))
        
    def __init__(self, val):
        if val is None or val == float('inf'):
            self.minutes = 0
            self.seconds = 0
            self.formatted = "--:--"
        else:
            total_seconds = int(round(float(val) * 60))
            self.minutes = total_seconds // 60
            self.seconds = total_seconds % 60
            self.formatted = f"{self.minutes:02d}:{self.seconds:02d}"
            
    def __str__(self):
        return self.formatted
        
    def __repr__(self):
        return f"'{self.formatted}'"
        
    @property
    def text(self):
        return f"{self.minutes} min {self.seconds:02d} seg"

def format_minutes_seconds(decimal_minutes):
    """
    Convierte minutos decimales a formato 'MM:SS' (minutos:segundos).
    Ejemplo: 10.9 minutos -> 654 segundos -> '10:54'
    """
    if decimal_minutes is None or decimal_minutes == float('inf'):
        return "--:--"
    total_seconds = int(round(float(decimal_minutes) * 60))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def format_time_text(decimal_minutes):
    """
    Convierte minutos decimales a texto legible 'X min Y seg'.
    Ejemplo: 10.9 -> '10 min 54 seg'
    """
    if decimal_minutes is None or decimal_minutes == float('inf'):
        return "N/A"
    total_seconds = int(round(float(decimal_minutes) * 60))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes} min {seconds:02d} seg ({minutes:02d}:{seconds:02d})"

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
    - Tiempos desglosados en minutos:segundos (MM:SS) y minutos decimales
    - Instrucciones paso a paso para el viajero
    """
    if not path or len(path) < 2:
        return {
            'path': path if path else [],
            'tiempo_total': 0.0,
            'tiempo_total_formato': "00:00",
            'tiempo_tren': 0.0,
            'tiempo_tren_formato': "00:00",
            'tiempo_transbordo': 0.0,
            'tiempo_transbordo_formato': "00:00",
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
                seg_fmt = format_minutes_seconds(current_segment_time)
                instrucciones.append(
                    f"Tomar Línea {current_line} desde '{current_segment_start}' hasta '{u_name}' "
                    f"({current_segment_stops} paradas, {seg_fmt} [{current_segment_time:.1f} min])"
                )
                current_segment_stops = 0
                current_segment_time = 0.0
                
            trans_fmt = format_minutes_seconds(t)
            instrucciones.append(
                f"Transbordo a pie en '{u_name}': cambiar de Línea {current_line} a Línea {v_line} "
                f"({trans_fmt} caminando [{t:.1f} min])"
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
        seg_fmt = format_minutes_seconds(current_segment_time)
        instrucciones.append(
            f"Tomar Línea {current_line} desde '{current_segment_start}' hasta '{last_station}' "
            f"({current_segment_stops} paradas, {seg_fmt} [{current_segment_time:.1f} min])"
        )
        
    tiempo_total_num = round(tiempo_tren + tiempo_transbordo, 1)
    
    return {
        'path': path,
        'tiempo_total': tiempo_total_num,
        'tiempo_total_formato': format_minutes_seconds(tiempo_total_num),
        'tiempo_total_texto': format_time_text(tiempo_total_num),
        'tiempo_tren': round(tiempo_tren, 1),
        'tiempo_tren_formato': format_minutes_seconds(tiempo_tren),
        'tiempo_transbordo': round(tiempo_transbordo, 1),
        'tiempo_transbordo_formato': format_minutes_seconds(tiempo_transbordo),
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
    Devuelve (path, tiempo) donde tiempo se imprime automáticamente en formato 'MM:SS'.
    """
    if source in G and target in G:
        try:
            path = nx.dijkstra_path(G, source, target, weight='weight')
            time = nx.dijkstra_path_length(G, source, target, weight='weight')
            return path, FormattedTime(time)
        except nx.NetworkXNoPath:
            return None, float('inf')
    else:
        res = find_best_route(G, source, target, criteria='time')
        if res:
            return res['path'], FormattedTime(res['tiempo_total'])
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
    Devuelve un diccionario 100% compatible con ambos formatos, incluyendo 'MM:SS'.
    """
    route_time = find_best_route(G, origin_station, destination_station, criteria='time')
    route_transfers = find_best_route(G, origin_station, destination_station, criteria='transfers')
    
    time_path = route_time['path'] if route_time else []
    time_val = FormattedTime(route_time['tiempo_total']) if route_time else float('inf')
    time_fmt = route_time['tiempo_total_formato'] if route_time else "--:--"
    
    trans_path = route_transfers['path'] if route_transfers else []
    trans_stops = route_transfers['num_paradas_tren'] if route_transfers else 0
    trans_time = FormattedTime(route_transfers['tiempo_total']) if route_transfers else float('inf')
    trans_fmt = route_transfers['tiempo_total_formato'] if route_transfers else "--:--"
    
    return {
        'origen': origin_station,
        'destino': destination_station,
        'menor_tiempo': route_time,
        'menores_transbordos': route_transfers,
        # Claves de compatibilidad con formato clásico y formato minutos:segundos
        'dijkstra': {
            'path': time_path,
            'time': time_val,             # FormattedTime: al imprimirse en f-string da 'MM:SS'
            'time_formatted': time_fmt,   # Cadena directa 'MM:SS'
            'tiempo_formato': time_fmt,   # Cadena directa 'MM:SS'
            'time_decimal': float(time_val),
            'stops': route_time.get('num_paradas_tren', 0) if route_time else 0,
            'transfers': route_time.get('num_transbordos', 0) if route_time else 0,
            'details': route_time
        },
        'bfs': {
            'path': trans_path,
            'stops': trans_stops,
            'transfers': route_transfers.get('num_transbordos', 0) if route_transfers else 0,
            'time': trans_time,           # FormattedTime: al imprimirse en f-string da 'MM:SS'
            'time_formatted': trans_fmt,  # Cadena directa 'MM:SS'
            'tiempo_formato': trans_fmt,  # Cadena directa 'MM:SS'
            'time_decimal': float(trans_time),
            'details': route_transfers
        }
    }

def find_route_with_disruption(G, origin_station, destination_station, avoid_station=None, avoid_line=None, avoid_edge=None, criteria='time'):
    """
    Calcula la ruta de contingencia entre dos estaciones esquivando una estación cerrada
    (completa o una línea específica) o un tramo de vía cortado.
    Compara el resultado contra la ruta normal habitual.
    """
    # 1. Ruta normal sin incidencias
    normal_route = find_best_route(G, origin_station, destination_station, criteria=criteria)
    
    # 2. Construir grafo con la incidencia aplicada
    G_disrupted = G.copy()
    excluded_desc = []
    
    if avoid_station:
        st_nodes = resolve_station_nodes(G, avoid_station)
        if avoid_line:
            clean_l = str(avoid_line).upper()
            if not clean_l.startswith('L') and clean_l != 'R':
                clean_l = f"L{clean_l}"
            nodes_to_cut = [n for n in st_nodes if G.nodes[n].get('linea') == clean_l]
            excluded_desc.append(f"Andén de {avoid_station} en {clean_l}")
        else:
            nodes_to_cut = st_nodes
            excluded_desc.append(f"Estación completa {avoid_station} ({len(st_nodes)} andenes)")
            
        G_disrupted.remove_nodes_from(nodes_to_cut)
        
    if avoid_edge:
        u_query, v_query = avoid_edge[0], avoid_edge[1]
        line_filter = avoid_edge[2] if len(avoid_edge) > 2 else None
        
        try:
            from robustness import clean_line_code
        except ImportError:
            from src.robustness import clean_line_code
            
        clean_l = clean_line_code(line_filter)
        u_nodes = resolve_station_nodes(G_disrupted, u_query)
        v_nodes = resolve_station_nodes(G_disrupted, v_query)
        
        edges_to_remove = set()
        for u in u_nodes:
            for v in v_nodes:
                if G_disrupted.has_edge(u, v):
                    d = G_disrupted.get_edge_data(u, v)
                    if d.get('tipo') == 'via':
                        if not clean_l or clean_line_code(d.get('linea')) == clean_l:
                            edges_to_remove.add((u, v))
                            
        # Si no hay vía directa pero se especificó una línea continua entre ambas paradas:
        if not edges_to_remove and clean_l:
            u_line = [n for n in u_nodes if clean_line_code(G_disrupted.nodes[n].get('linea')) == clean_l]
            v_line = [n for n in v_nodes if clean_line_code(G_disrupted.nodes[n].get('linea')) == clean_l]
            if u_line and v_line:
                try:
                    line_sub = nx.Graph()
                    for u_sub, v_sub, d_sub in G_disrupted.edges(data=True):
                        if d_sub.get('tipo') == 'via' and clean_line_code(d_sub.get('linea')) == clean_l:
                            line_sub.add_edge(u_sub, v_sub, weight=d_sub.get('weight', 1))
                    seg_path = nx.shortest_path(line_sub, u_line[0], v_line[0])
                    for seg_u, seg_v in zip(seg_path[:-1], seg_path[1:]):
                        edges_to_remove.add((seg_u, seg_v))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass
                    
        for u, v in edges_to_remove:
            if G_disrupted.has_edge(u, v):
                G_disrupted.remove_edge(u, v)
                
        u_disp = G.nodes[u_nodes[0]].get('nombre', u_query) if u_nodes else u_query
        v_disp = G.nodes[v_nodes[0]].get('nombre', v_query) if v_nodes else v_query
        l_info = f" ({clean_l})" if clean_l else ""
        excluded_desc.append(f"Tramo de vía {u_disp} <-> {v_disp}{l_info}")
        
    # 3. Calcular ruta en red con incidencia
    detour_route = None
    try:
        detour_route = find_best_route(G_disrupted, origin_station, destination_station, criteria=criteria)
    except (ValueError, nx.NetworkXNoPath):
        detour_route = None
        
    is_possible = detour_route is not None
    extra_time = None
    extra_time_text = "N/A"
    
    if is_possible and normal_route:
        diff = max(0.0, detour_route['tiempo_total'] - normal_route['tiempo_total'])
        extra_time = FormattedTime(diff)
        extra_time_text = extra_time.text
        
    return {
        'origen': origin_station,
        'destino': destination_station,
        'criterio': criteria,
        'avoid_station': avoid_station,
        'avoid_line': avoid_line,
        'avoid_edge': avoid_edge,
        'elementos_excluidos': " | ".join(excluded_desc),
        'ruta_normal': normal_route,
        'ruta_desvio': detour_route,
        'es_posible': is_possible,
        'sobrecosto_tiempo': extra_time,
        'sobrecosto_tiempo_texto': extra_time_text
    }

if __name__ == "__main__":
    from graph_builder import load_data, build_metro_graph
    
    data = load_data('data/metro_madrid.json')
    G = build_metro_graph(data)
    
    res = compare_routes(G, "Sol", "Nuevos Ministerios")
    rt = res['menor_tiempo']
    print(f"Ruta Sol -> Nuevos Ministerios:")
    print(f"  Tiempo Total en Formato MM:SS: {rt['tiempo_total_formato']} ({rt['tiempo_total_texto']})")
    print(f"  Tiempo Tren: {rt['tiempo_tren_formato']} | Tiempo Transbordo: {rt['tiempo_transbordo_formato']}")
    for inst in rt['instrucciones']:
        print(f"   • {inst}")

