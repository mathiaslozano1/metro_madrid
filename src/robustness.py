import networkx as nx
import unicodedata
import difflib

try:
    from algorithms import FormattedTime
except ImportError:
    try:
        from src.algorithms import FormattedTime
    except ImportError:
        def FormattedTime(v):
            return f"{int(v)//60:02d}:{int(round(v*60))%60:02d}" if v is not None else "--:--"

def normalize_name(s):
    """Normaliza un texto quitando tildes, reemplazando guiones bajos y pasando a minúsculas."""
    if not isinstance(s, str):
        return ""
    s = s.replace('_', ' ').strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def clean_line_code(line_input):
    """
    Normaliza el identificador de una línea a su formato estándar en el grafo ('L1', 'L10', 'R', etc.).
    Soporta entradas como: '1', 1, 'l1', 'L1', 'linea 1', 'L01', 'R', 'Ramal', 'ramal'.
    """
    if line_input is None:
        return None
    s = str(line_input).strip()
    if not s:
        return None
    s_norm = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    s_norm = s_norm.replace('_', ' ').strip()
    
    # Remover prefijos de línea
    for prefix in ['linea', 'line']:
        if s_norm.startswith(prefix):
            s_norm = s_norm[len(prefix):].strip()
            
    if s_norm in ['r', 'ramal']:
        return 'R'
    if s_norm.isdigit():
        return f"L{int(s_norm)}"
    if s_norm.startswith('l') and s_norm[1:].isdigit():
        return f"L{int(s_norm[1:])}"
    return s.upper()

def find_candidate_stations(G, query):
    """
    Busca andenes de una estación usando coincidencia exacta de ID, nombre físico normalizado,
    subcadenas y sugerencias difusas con difflib.
    Retorna una tupla: (nodos_encontrados, sugerencia_si_no_encontrado)
    """
    if not query:
        return [], None
        
    query_str = str(query).strip()
    # 1. Si es ID exacto de nodo en el grafo
    if query_str in G:
        return [query_str], None
        
    norm = normalize_name(query_str)
    if not norm:
        return [], None
        
    # 2. Coincidencia exacta por atributo 'nombre' normalizado
    exact_name = [n for n, d in G.nodes(data=True) if normalize_name(d.get('nombre', '')) == norm]
    if exact_name:
        return exact_name, None
        
    # 3. Coincidencia exacta con ID de nodo normalizado
    exact_id = [n for n in G.nodes() if normalize_name(n) == norm]
    if exact_id:
        return exact_id, None
        
    # 4. Subcadena en 'nombre'
    sub_name = [n for n, d in G.nodes(data=True) if norm in normalize_name(d.get('nombre', ''))]
    if sub_name:
        return sub_name, None
        
    # 5. Subcadena en ID de nodo
    sub_id = [n for n in G.nodes() if norm in normalize_name(n)]
    if sub_id:
        return sub_id, None
        
    # 6. Búsqueda difusa de la estación más cercana
    all_names = list(dict.fromkeys(d.get('nombre', n) for n, d in G.nodes(data=True)))
    close = difflib.get_close_matches(query_str, all_names, n=3, cutoff=0.5)
    sugerencia = close[0] if close else None
    return [], sugerencia

def get_station_neighbors_summary(G, station_query):
    """
    Obtiene las estaciones físicas vecinas directamente conectadas y sus líneas asociadas.
    """
    nodes, _ = find_candidate_stations(G, station_query)
    neighbors = {}
    for n in nodes:
        nombre_propio = G.nodes[n].get('nombre', n)
        for nbr in G.neighbors(n):
            nbr_nombre = G.nodes[nbr].get('nombre', nbr)
            nbr_linea = G.nodes[nbr].get('linea', '')
            if nbr_nombre != nombre_propio:
                neighbors.setdefault(nbr_nombre, set()).add(nbr_linea)
    return neighbors

def resolve_station_nodes_for_removal(G, station_query):
    """
    Resuelve los nodos del grafo correspondientes a una consulta para su eliminación.
    Permite eliminar:
    - Un andén específico por su ID exacto (ej. 'Sol [L1]')
    - Una estación física completa por su nombre (ej. 'Sol', 'Callao', 'la_elipa')
    - Una lista/conjunto de nombres o IDs
    """
    if isinstance(station_query, (list, tuple, set)):
        res = []
        for q in station_query:
            res.extend(resolve_station_nodes_for_removal(G, q))
        return list(dict.fromkeys(res))
        
    nodes, _ = find_candidate_stations(G, station_query)
    return nodes

def resolve_edge_detailed(G, source_query, target_query, linea=None):
    """
    Resuelve e identifica una arista (tramo de vía o pasillo de transbordo) en el grafo
    a partir de identificadores exactos o nombres de estaciones físicas.
    
    Retorna: (edge, error_message)
    - Si se encuentra: ((u, v), None)
    - Si no se encuentra: (None, mensaje_explicativo_con_sugerencias)
    """
    clean_line = clean_line_code(linea)
    
    # 1. Búsqueda directa si se pasan IDs exactos de nodo
    if G.has_edge(source_query, target_query):
        edge_data = G.get_edge_data(source_query, target_query)
        edge_line = clean_line_code(edge_data.get('linea', ''))
        if clean_line and edge_line and clean_line != edge_line:
            return None, (
                f"La arista directa entre '{source_query}' y '{target_query}' pertenece a la línea '{edge_line}', "
                f"pero se especificó el filtro de línea '{linea}'."
            )
        return (source_query, target_query), None
        
    # 2. Resolver andenes de origen y destino
    s_nodes, s_sug = find_candidate_stations(G, source_query)
    t_nodes, t_sug = find_candidate_stations(G, target_query)
    
    if not s_nodes:
        msg = f"No se encontró la estación de origen '{source_query}' en la red."
        if s_sug:
            msg += f" ¿Quizás quisiste decir '{s_sug}'?"
        return None, msg
        
    if not t_nodes:
        msg = f"No se encontró la estación de destino '{target_query}' en la red."
        if t_sug:
            msg += f" ¿Quizás quisiste decir '{t_sug}'?"
        return None, msg
        
    # 3. Buscar tramos directos existentes entre los andenes candidatos
    direct_edges = []
    for u in s_nodes:
        for v in t_nodes:
            if G.has_edge(u, v):
                direct_edges.append((u, v))
                
    if not direct_edges:
        s_nombre = G.nodes[s_nodes[0]].get('nombre', str(source_query))
        t_nombre = G.nodes[t_nodes[0]].get('nombre', str(target_query))
        
        # Obtener estaciones adyacentes a origen
        s_neighbors = get_station_neighbors_summary(G, source_query)
        vecinos_str = "\n".join([f"  - {nbr} (Líneas: {', '.join(sorted(list(lins)))})" 
                                for nbr, lins in list(s_neighbors.items())[:8]])
                                
        path_str = ""
        try:
            camino = nx.shortest_path(G, source=s_nodes[0], target=t_nodes[0], weight='weight')
            if camino:
                nombres_camino = [f"{G.nodes[n].get('nombre', n)} [{G.nodes[n].get('linea', '')}]" for n in camino]
                path_str = f"\nRuta de viaje existente entre ambas:\n  " + " -> ".join(nombres_camino) + "\n"
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass
            
        msg = (
            f"Las estaciones '{s_nombre}' y '{t_nombre}' existen en la red, pero NO comparten un tramo directo (arista).\n"
            f"Un tramo representa la vía directa entre dos estaciones adyacentes consecutivas.{path_str}\n"
            f"Estaciones directamente adyacentes a '{s_nombre}':\n{vecinos_str}"
        )
        return None, msg
        
    # 4. Si se especificó línea, filtrar
    if clean_line:
        filtered_edges = []
        for u, v in direct_edges:
            edge_data = G.get_edge_data(u, v)
            e_line = clean_line_code(edge_data.get('linea', ''))
            u_line = clean_line_code(G.nodes[u].get('linea', ''))
            v_line = clean_line_code(G.nodes[v].get('linea', ''))
            if clean_line in [e_line, u_line, v_line]:
                filtered_edges.append((u, v))
                
        if not filtered_edges:
            available_lines = set()
            for u, v in direct_edges:
                edge_data = G.get_edge_data(u, v)
                lin = edge_data.get('linea') or G.nodes[u].get('linea')
                if lin:
                    available_lines.add(lin)
            lines_str = ", ".join(sorted(list(available_lines)))
            return None, (
                f"Existe un tramo directo entre '{source_query}' y '{target_query}', pero en la(s) línea(s): {lines_str}. "
                f"No en la línea '{linea}'."
            )
        return filtered_edges[0], None
        
    return direct_edges[0], None

def resolve_edge(G, source_query, target_query, linea=None):
    """
    Resuelve e identifica una arista (tramo de vía o pasillo de transbordo) en el grafo
    a partir de identificadores exactos o nombres de estaciones físicas.
    Retorna la tupla (u, v) o None si no se encuentra.
    """
    edge, _ = resolve_edge_detailed(G, source_query, target_query, linea)
    return edge

def identify_articulation_points(G):
    """
    Identifica los puntos de articulación de la red a nivel de nodo (andén).
    Un punto de articulación es un nodo cuya eliminación desconecta el grafo.
    """
    return list(nx.articulation_points(G))

def identify_critical_stations(G, top_n=None):
    """
    Identifica qué estaciones físicas, al ser cerradas completamente
    (todos sus andenes y líneas asociadas), desconectan la red de metro.
    Retorna una lista ordenada de mayor a menor criticidad.
    """
    unique_stations = {}
    for n, d in G.nodes(data=True):
        nombre = d.get('nombre', n)
        if nombre not in unique_stations:
            unique_stations[nombre] = {'nodes': [], 'lineas': set()}
        unique_stations[nombre]['nodes'].append(n)
        if d.get('linea'):
            unique_stations[nombre]['lineas'].add(d.get('linea'))
            
    critical = []
    for nombre, info in unique_stations.items():
        st_nodes = info['nodes']
        G_copy = G.copy()
        G_copy.remove_nodes_from(st_nodes)
        
        n_comp = nx.number_connected_components(G_copy) if len(G_copy) > 0 else 0
        if n_comp > 1:
            components = sorted(list(nx.connected_components(G_copy)), key=len, reverse=True)
            isolated_count = sum(len(c) for c in components[1:])
            critical.append({
                'estacion': nombre,
                'num_andenes': len(st_nodes),
                'lineas': sorted(list(info['lineas'])),
                'num_components': n_comp,
                'isolated_stations_count': isolated_count,
                'andenes_eliminados': st_nodes
            })
            
    # Ordenar por número de componentes desconectados y luego por estaciones aisladas
    critical.sort(key=lambda x: (x['num_components'], x['isolated_stations_count']), reverse=True)
    
    if top_n is not None:
        return critical[:top_n]
    return critical

def identify_critical_edges(G, top_n=None):
    """
    Identifica todos los tramos de vía o transbordos críticos (puentes / bridges)
    cuya clausura desconecta la red de metro o aísla estaciones terminales.
    Retorna una lista ordenada de mayor a menor número de estaciones aisladas.
    """
    bridges = list(nx.bridges(G))
    bridge_info = []
    
    for u, v in bridges:
        edge_data = G.get_edge_data(u, v)
        G_temp = G.copy()
        G_temp.remove_edge(u, v)
        
        comps = sorted(list(nx.connected_components(G_temp)), key=len, reverse=True)
        isolated_count = sum(len(c) for c in comps[1:]) if len(comps) > 1 else 0
        
        bridge_info.append({
            'edge': (u, v),
            'source_station': G.nodes[u].get('nombre', u),
            'target_station': G.nodes[v].get('nombre', v),
            'source_node': u,
            'target_node': v,
            'linea': edge_data.get('linea', G.nodes[u].get('linea', '')),
            'tipo': edge_data.get('tipo', 'via'),
            'weight': FormattedTime(edge_data.get('weight', 0)),
            'isolated_nodes_count': isolated_count
        })
        
    bridge_info.sort(key=lambda x: x['isolated_nodes_count'], reverse=True)
    
    if top_n is not None:
        return bridge_info[:top_n]
    return bridge_info

def simulate_node_removal(G, station_or_node):
    """
    Simula la eliminación de una estación (completa con todos sus andenes)
    o de un andén específico y evalúa el impacto en la conectividad de la red.
    
    Parámetros:
    - G: Grafo de NetworkX.
    - station_or_node: Nombre de estación física ('Sol', 'Callao', 'Pueblo Nuevo'),
      ID de andén ('Sol [L1]') o lista de estaciones.
      
    Retorna:
    - Diccionario con el nuevo grafo y detalles de conectividad:
      'new_graph', 'is_connected', 'num_components', 'removed_nodes',
      'removed_station', 'num_removed_nodes', 'component_sizes', 'isolated_nodes'.
    """
    nodes_to_remove = resolve_station_nodes_for_removal(G, station_or_node)
    
    G_copy = G.copy()
    if nodes_to_remove:
        G_copy.remove_nodes_from(nodes_to_remove)
    elif station_or_node in G_copy:
        # Fallback de seguridad
        nodes_to_remove = [station_or_node]
        G_copy.remove_node(station_or_node)
        
    is_connected = nx.is_connected(G_copy) if len(G_copy) > 0 else False
    num_components = nx.number_connected_components(G_copy) if len(G_copy) > 0 else 0
    
    components = []
    component_sizes = []
    largest_component_size = 0
    isolated_nodes = []
    
    if num_components > 0:
        components = sorted(list(nx.connected_components(G_copy)), key=len, reverse=True)
        component_sizes = [len(c) for c in components]
        largest_component_size = component_sizes[0]
        for c in components[1:]:
            isolated_nodes.extend(list(c))
            
    # Nombre representativo para visualización y reporte
    if isinstance(station_or_node, (list, tuple, set)):
        nombre_representativo = ", ".join(str(s) for s in station_or_node)
    elif nodes_to_remove:
        nombres = list(dict.fromkeys(G.nodes[n].get('nombre', n) for n in nodes_to_remove))
        nombre_representativo = ", ".join(nombres)
    else:
        nombre_representativo = str(station_or_node)
        
    return {
        'new_graph': G_copy,
        'is_connected': is_connected,
        'num_components': num_components,
        'removed_nodes': nodes_to_remove,
        'removed_station': nombre_representativo,
        'num_removed_nodes': len(nodes_to_remove),
        'components': components,
        'component_sizes': component_sizes,
        'largest_component_size': largest_component_size,
        'isolated_nodes': isolated_nodes
    }

def simulate_station_removal(G, station_name):
    """
    Alias explícito de simulate_node_removal para eliminar una estación física completa.
    """
    return simulate_node_removal(G, station_name)

def simulate_edge_removal(G, source, target, linea=None):
    """
    Simula la eliminación de una arista (tramo de vía o pasillo de transbordo)
    y evalúa en detalle el impacto en la conectividad de la red.
    
    Parámetros:
    - G: Grafo de NetworkX.
    - source: Estación de origen o ID de nodo (ej. 'Sol', 'Sol [L1]').
    - target: Estación de destino o ID de nodo (ej. 'Gran Vía', 'Gran Vía [L1]').
    - linea (opcional): Filtro de línea en caso de haber varias opciones (ej. 'L1').
    
    Retorna un diccionario con:
    - 'new_graph': Grafo con la arista eliminada.
    - 'removed_edge': Tupla (u, v) de la arista removida.
    - 'source_node', 'target_node': Identificadores exactos de los andenes.
    - 'source_station', 'target_station': Nombres legibles de las estaciones.
    - 'linea': Línea a la que pertenece el tramo.
    - 'tipo': 'via' (vía de tren) o 'transbordo' (pasillo a pie).
    - 'original_time': Tiempo normal del tramo directo en formato mm:ss.
    - 'is_connected': Si la red global sigue siendo un único componente conexo.
    - 'num_components': Número de componentes conexas resultantes.
    - 'component_sizes': Tamaños de los componentes conexos resultantes.
    - 'is_bridge': True si la arista era un puente cuya eliminación fragmenta la red.
    - 'has_alternative_path': True si los pasajeros aún pueden viajar entre source y target.
    - 'alternative_path': Lista de estaciones de la ruta alternativa más rápida.
    - 'alternative_time': Tiempo total de la ruta alternativa en formato mm:ss.
    - 'time_increase': Tiempo extra requerido por el desvío (+mm:ss).
    """
    edge, err_msg = resolve_edge_detailed(G, source, target, linea)
    if not edge:
        raise ValueError(err_msg)
        
    u, v = edge
    edge_data = dict(G.get_edge_data(u, v))
    weight_original = edge_data.get('weight', 1.0)
    
    G_copy = G.copy()
    G_copy.remove_edge(u, v)
    
    is_connected = nx.is_connected(G_copy) if len(G_copy) > 0 else False
    num_components = nx.number_connected_components(G_copy) if len(G_copy) > 0 else 0
    
    components = []
    component_sizes = []
    largest_component_size = 0
    isolated_nodes = []
    
    if num_components > 0:
        components = sorted(list(nx.connected_components(G_copy)), key=len, reverse=True)
        component_sizes = [len(c) for c in components]
        largest_component_size = component_sizes[0]
        for c in components[1:]:
            isolated_nodes.extend(list(c))
            
    is_bridge = (num_components > 1)
    
    # Calcular ruta alternativa entre los dos andenes desconectados
    has_alternative = nx.has_path(G_copy, u, v)
    alternative_path = []
    alternative_time = None
    time_increase = None
    
    if has_alternative:
        alternative_path = nx.shortest_path(G_copy, source=u, target=v, weight='weight')
        alt_time_val = nx.shortest_path_length(G_copy, source=u, target=v, weight='weight')
        alternative_time = FormattedTime(alt_time_val)
        time_increase = FormattedTime(alt_time_val - weight_original)
        
    return {
        'new_graph': G_copy,
        'removed_edge': (u, v),
        'source_node': u,
        'target_node': v,
        'source_station': G.nodes[u].get('nombre', u),
        'target_station': G.nodes[v].get('nombre', v),
        'linea': edge_data.get('linea', G.nodes[u].get('linea', '')),
        'tipo': edge_data.get('tipo', 'via'),
        'original_time': FormattedTime(weight_original),
        'is_connected': is_connected,
        'num_components': num_components,
        'components': components,
        'component_sizes': component_sizes,
        'largest_component_size': largest_component_size,
        'isolated_nodes': isolated_nodes,
        'is_bridge': is_bridge,
        'has_alternative_path': has_alternative,
        'alternative_path': alternative_path,
        'alternative_time': alternative_time,
        'time_increase': time_increase
    }
