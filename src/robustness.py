import networkx as nx
import unicodedata

def normalize_name(s):
    """Normaliza un texto quitando tildes, reemplazando guiones bajos y pasando a minúsculas."""
    if not isinstance(s, str):
        return ""
    s = s.replace('_', ' ').strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

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
        
    if station_query in G:
        return [station_query]
        
    norm = normalize_name(station_query)
    if not norm:
        return []
        
    # 1. Búsqueda exacta normalizada por atributo 'nombre' de la estación física
    matches = [n for n, d in G.nodes(data=True) if normalize_name(d.get('nombre', '')) == norm]
    if matches:
        return matches
        
    # 2. Búsqueda por coincidencia en el ID del nodo normalizado
    matches = [n for n in G.nodes() if norm in normalize_name(n)]
    if matches:
        return matches
        
    return []

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

def simulate_edge_removal(G, source, target):
    """
    Simula la eliminación de una arista (tramo o transbordo) y evalúa el impacto en la conectividad.
    """
    G_copy = G.copy()
    if G_copy.has_edge(source, target):
        G_copy.remove_edge(source, target)
        
    is_connected = nx.is_connected(G_copy) if len(G_copy) > 0 else False
    num_components = nx.number_connected_components(G_copy) if len(G_copy) > 0 else 0
    
    components = []
    component_sizes = []
    if num_components > 0:
        components = sorted(list(nx.connected_components(G_copy)), key=len, reverse=True)
        component_sizes = [len(c) for c in components]
        
    return {
        'new_graph': G_copy,
        'is_connected': is_connected,
        'num_components': num_components,
        'component_sizes': component_sizes
    }
