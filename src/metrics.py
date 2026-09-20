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
    Agrupa las métricas calculadas a nivel de andén por estación física única.
    Permite obtener rankings de estaciones reales sin repeticiones por línea.
    """
    grados = calculate_degree(G)
    centralidades = calculate_betweenness_centrality(G)
    
    estaciones_grados = {}
    estaciones_centralidad = {}
    estaciones_lineas = {}
    
    for nodo, d in G.nodes(data=True):
        nombre = d.get('nombre', nodo)
        linea = d.get('linea', '')
        
        if nombre not in estaciones_lineas:
            estaciones_lineas[nombre] = set()
        if linea:
            estaciones_lineas[nombre].add(linea)
            
        estaciones_grados[nombre] = estaciones_grados.get(nombre, 0) + grados.get(nodo, 0)
        estaciones_centralidad[nombre] = estaciones_centralidad.get(nombre, 0.0) + centralidades.get(nodo, 0.0)
        
    return {
        'grados_estacion': estaciones_grados,
        'centralidad_estacion': estaciones_centralidad,
        'lineas_estacion': estaciones_lineas
    }

def get_top_stations_by_degree(G, n=5):
    """Devuelve las top N estaciones físicas únicas con mayor conectividad (sin repetición de línea)."""
    agg = aggregate_station_metrics(G)
    sorted_deg = sorted(agg['grados_estacion'].items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for nombre, grado in sorted_deg[:n]:
        lineas = sorted(list(agg['lineas_estacion'].get(nombre, [])))
        result.append({
            'nombre': nombre,
            'grado_total': grado,
            'num_lineas': len(lineas),
            'lineas': lineas
        })
    return result

def get_top_stations_by_betweenness(G, n=5):
    """Devuelve las top N estaciones físicas únicas más centrales (sin repetición de línea)."""
    agg = aggregate_station_metrics(G)
    sorted_bet = sorted(agg['centralidad_estacion'].items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for nombre, bet in sorted_bet[:n]:
        lineas = sorted(list(agg['lineas_estacion'].get(nombre, [])))
        result.append({
            'nombre': nombre,
            'centralidad': round(bet, 4),
            'num_lineas': len(lineas),
            'lineas': lineas
        })
    return result

def get_all_metrics(G):
    """Obtiene un diccionario con todas las métricas de la red a nivel de andén y de estación física."""
    station_agg = aggregate_station_metrics(G)
    return {
        'degree': calculate_degree(G),
        'betweenness_centrality': calculate_betweenness_centrality(G),
        'density': calculate_density(G),
        'diameter': calculate_diameter(G),
        'station_degree': station_agg['grados_estacion'],
        'station_betweenness': station_agg['centralidad_estacion'],
        'top_stations_degree': get_top_stations_by_degree(G, n=5),
        'top_stations_betweenness': get_top_stations_by_betweenness(G, n=5)
    }

if __name__ == "__main__":
    from graph_builder import load_data, build_metro_graph
    
    data = load_data('data/metro_madrid.json')
    G = build_metro_graph(data)
    
    print("=== TOP 5 ESTACIONES FÍSICAS ÚNICAS CON MAYOR GRADO ===")
    for idx, est in enumerate(get_top_stations_by_degree(G, 5), 1):
        lineas_txt = ", ".join(est['lineas'])
        print(f"  {idx}. {est['nombre']} -> {est['grado_total']} conexiones (Líneas: {lineas_txt})")
        
    print("\n=== TOP 5 ESTACIONES FÍSICAS ÚNICAS MÁS CENTRALES ===")
    for idx, est in enumerate(get_top_stations_by_betweenness(G, 5), 1):
        lineas_txt = ", ".join(est['lineas'])
        print(f"  {idx}. {est['nombre']} -> Centralidad: {est['centralidad']} (Líneas: {lineas_txt})")
