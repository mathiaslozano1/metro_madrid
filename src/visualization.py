import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

try:
    from robustness import resolve_station_nodes_for_removal, resolve_edge, simulate_edge_removal
    from html_generator import generate_metro_interactive_html
except ImportError:
    from src.robustness import resolve_station_nodes_for_removal, resolve_edge, simulate_edge_removal
    from src.html_generator import generate_metro_interactive_html

# Diccionario de colores oficiales del Metro de Madrid (soporta formato '1', 'L1', etc.)
COLORES_LINEAS = {
    '1': '#0097D6', 'L1': '#0097D6',
    '2': '#FF2A14', 'L2': '#FF2A14',
    '3': '#FFD100', 'L3': '#FFD100',
    '4': '#93351C', 'L4': '#93351C',
    '5': '#80C23D', 'L5': '#80C23D',
    '6': '#A8A9AD', 'L6': '#A8A9AD',
    '7': '#F68315', 'L7': '#F68315',
    '8': '#E35F92', 'L8': '#E35F92',
    '9': '#8B1E91', 'L9': '#8B1E91',
    '10': '#0039A6', 'L10': '#0039A6',
    '11': '#009139', 'L11': '#009139',
    '12': '#A19100', 'L12': '#A19100',
    'R': '#FFFFFF', 'LR': '#FFFFFF'
}

def get_geographic_layout(G, jitter_radius=0.0014, is_pyvis=False, pyvis_scale=12000):
    """
    Calcula la posición (x, y) de cada nodo basándose en sus coordenadas GPS reales (lat, lon).
    - Para estaciones físicas con múltiples andenes (transbordos), aplica un desplazamiento radial
      equidistante para evitar solapamientos y visualizar con claridad los pasillos peatonales.
    - Para PyVis (HTML Canvas), centra las coordenadas e invierte el eje Y para que el Norte quede arriba.
    - Para Matplotlib, utiliza directamente longitud en X y latitud en Y con corrección de aspecto.
    """
    station_nodes = {}
    for node, data in G.nodes(data=True):
        nombre = data.get('nombre', node)
        station_nodes.setdefault(nombre, []).append(node)
        
    pos = {}
    
    if is_pyvis:
        lats = [d.get('lat', 40.4168) for _, d in G.nodes(data=True)]
        lons = [d.get('lon', -3.7038) for _, d in G.nodes(data=True)]
        center_lat = (min(lats) + max(lats)) / 2.0
        center_lon = (min(lons) + max(lons)) / 2.0
        cos_lat = np.cos(np.radians(center_lat))
        
        for nombre, nodes in station_nodes.items():
            k = len(nodes)
            base_lat = G.nodes[nodes[0]].get('lat', center_lat)
            base_lon = G.nodes[nodes[0]].get('lon', center_lon)
            
            for i, node in enumerate(nodes):
                if k == 1:
                    d_lon, d_lat = 0.0, 0.0
                else:
                    angle = 2 * np.pi * i / k
                    d_lon = (jitter_radius / cos_lat) * np.cos(angle)
                    d_lat = jitter_radius * np.sin(angle)
                    
                cur_lon = base_lon + d_lon
                cur_lat = base_lat + d_lat
                
                # Canvas HTML: X hacia la derecha, Y invertido (hacia arriba es Norte)
                x = (cur_lon - center_lon) * cos_lat * pyvis_scale
                y = -(cur_lat - center_lat) * pyvis_scale
                pos[node] = (x, y)
    else:
        cos_lat = np.cos(np.radians(40.42))
        for nombre, nodes in station_nodes.items():
            k = len(nodes)
            base_lat = G.nodes[nodes[0]].get('lat', 40.4168)
            base_lon = G.nodes[nodes[0]].get('lon', -3.7038)
            
            for i, node in enumerate(nodes):
                if k == 1:
                    d_lon, d_lat = 0.0, 0.0
                else:
                    angle = 2 * np.pi * i / k
                    d_lon = (jitter_radius / cos_lat) * np.cos(angle)
                    d_lat = jitter_radius * np.sin(angle)
                    
                pos[node] = (base_lon + d_lon, base_lat + d_lat)
                
    return pos

def plot_graph_matplotlib(G, title="Red del Metro de Madrid (Modelo Estación-Línea - Geográfico)"):
    """
    Dibuja el grafo en matplotlib diferenciando vías de tren de pasillos de transbordo
    respetando la disposición geográfica real.
    """
    plt.figure(figsize=(32, 28), facecolor='#121212')
    ax = plt.gca()
    ax.set_facecolor('#121212')
    
    pos = get_geographic_layout(G)
    
    # Separar aristas de vía y de transbordo
    via_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('tipo') == 'via']
    trans_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('tipo') == 'transbordo']
    
    # Colores de nodos según su línea
    node_colors = []
    for _, d in G.nodes(data=True):
        linea = d.get('linea', '')
        node_colors.append(COLORES_LINEAS.get(linea, '#00E5FF'))
        
    grados = dict(G.degree())
    node_sizes = [v * 35 + 50 for v in grados.values()]
    
    # 1. Dibujar aristas de transbordo (líneas punteadas blancas suaves)
    nx.draw_networkx_edges(G, pos, edgelist=trans_edges, width=1.5, 
                           style='dashed', edge_color='#FFFFFF', alpha=0.85)
    
    # 2. Dibujar aristas de vía férrea
    nx.draw_networkx_edges(G, pos, edgelist=via_edges, width=1.8, 
                           edge_color='#888888', alpha=0.6)
    
    # 3. Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                           node_color=node_colors, edgecolors='#FFFFFF', linewidths=0.8)
    
    # 4. Etiquetas de texto para TODOS los nodos de la red sin excepción
    labels = {n: f"{d.get('nombre', n)}" for n, d in G.nodes(data=True)}
    pos_labels = {k: (v[0], v[1] + 0.0018) for k, v in pos.items()}
    nx.draw_networkx_labels(G, pos_labels, labels, font_size=6.0, 
                            font_color='#FFFFFF', font_weight='bold',
                            font_family='sans-serif')
    
    # Corrección de aspecto geográfico para evitar deformaciones
    ax.set_aspect(1.0 / np.cos(np.radians(40.42)))
    
    plt.title(f"{title}\n(Disposición Geográfica Real | Nodos = Andenes | Líneas punteadas = Transbordos)", 
              fontsize=22, fontweight='bold', color='white', pad=25)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def plot_graph_pyvis(G, output_file="metro_madrid_pyvis.html"):
    """
    Genera una visualización interactiva Premium con Vis.js bajo el modelo Estación-Línea y coordenadas geográficas.
    Incluye:
    - Buscador interactivo de estaciones con autocompletado y zoom automático.
    - Leyenda oficial de líneas con filtro interactivo y aislamiento de líneas.
    - Calculador de rutas óptimas (menor tiempo y menor transbordo) con itinerario detallado paso a paso.
    - Simulador visual de resiliencia y fallos (cierre de estaciones o tramos) con rutas alternativas.
    - Modo oscuro unificado y dependencias CDN 100% autónomas.
    """
    pos = get_geographic_layout(G, is_pyvis=True, pyvis_scale=12000)
    generate_metro_interactive_html(G, pos, output_file=output_file)



def plot_route_matplotlib(G, path, title="Ruta Óptima"):
    """
    Genera una visualización estática destacando la ruta óptima usando matplotlib sobre el mapa geográfico.
    path es una lista de nodos en el orden del recorrido.
    """
    plt.figure(figsize=(26, 24), facecolor='#121212')
    ax = plt.gca()
    ax.set_facecolor('#121212')
    
    pos = get_geographic_layout(G)
    
    path_edges = set(zip(path[:-1], path[1:]))
    path_edges.update([(v, u) for u, v in path_edges])
    
    # Separar aristas que pertenecen a la ruta y las que no
    route_edges = [(u, v) for u, v in G.edges() if (u, v) in path_edges]
    other_edges = [(u, v) for u, v in G.edges() if (u, v) not in path_edges]
    
    # Nodos de la ruta y otros nodos
    route_nodes = [n for n in G.nodes() if n in path]
    other_nodes = [n for n in G.nodes() if n not in path]
    
    # Colores base
    node_colors_other = [COLORES_LINEAS.get(G.nodes[n].get('linea', ''), '#00E5FF') for n in other_nodes]
    
    # 1. Dibujar el resto de la red (atenuado)
    nx.draw_networkx_edges(G, pos, edgelist=other_edges, width=1.0, edge_color='#444444', alpha=0.3)
    nx.draw_networkx_nodes(G, pos, nodelist=other_nodes, node_size=30, node_color=node_colors_other, alpha=0.2)
    
    # 2. Dibujar la ruta (resaltada)
    nx.draw_networkx_edges(G, pos, edgelist=route_edges, width=4.5, edge_color='#00FF00', alpha=0.9)
    nx.draw_networkx_nodes(G, pos, nodelist=route_nodes, node_size=150, node_color='#00FF00', edgecolors='#FFFFFF', linewidths=2)
    
    # 3. Etiquetas de texto sólo para los nodos de la ruta
    labels = {n: G.nodes[n].get('nombre', str(n)) for n in route_nodes}
    pos_labels = {k: (v[0], v[1] + 0.0025) for k, v in pos.items() if k in route_nodes}
    nx.draw_networkx_labels(G, pos_labels, labels, font_size=11, font_color='#00FF00', font_weight='bold')
    
    # 4. Resaltar inicio y fin
    if path:
        start_node, end_node = path[0], path[-1]
        nx.draw_networkx_nodes(G, pos, nodelist=[start_node], node_size=300, node_color='#FFFF00', edgecolors='#FFFFFF')
        nx.draw_networkx_nodes(G, pos, nodelist=[end_node], node_size=300, node_color='#FF0000', edgecolors='#FFFFFF')
        
        pos_start = {start_node: (pos[start_node][0], pos[start_node][1] - 0.0035)}
        pos_end = {end_node: (pos[end_node][0], pos[end_node][1] - 0.0035)}
        nx.draw_networkx_labels(G, pos_start, {start_node: 'INICIO'}, font_size=13, font_color='#FFFF00', font_weight='bold')
        nx.draw_networkx_labels(G, pos_end, {end_node: 'FIN'}, font_size=13, font_color='#FF0000', font_weight='bold')
    
    ax.set_aspect(1.0 / np.cos(np.radians(40.42)))
    plt.title(f"{title} (Mapa Geográfico)", fontsize=22, fontweight='bold', color='white', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def plot_failed_station_matplotlib(G, failed_station_or_node, title=None, resolve_station_nodes_for_removal=resolve_station_nodes_for_removal):
    """
    Visualiza el impacto del fallo de una estación (física completa o andén individual) sobre el mapa geográfico.
    Muestra los andenes caídos en rojo con una 'X' y colorea de forma diferenciada
    los fragmentos desconectados que quedan (componentes conexas).
    """
    failed_nodes = resolve_station_nodes_for_removal(G, failed_station_or_node)
    if not failed_nodes:
        if failed_station_or_node in G:
            failed_nodes = [failed_station_or_node]
        else:
            print(f"Error: La estación '{failed_station_or_node}' no fue encontrada en la red.")
            return

    plt.figure(figsize=(26, 24), facecolor='#121212')
    ax = plt.gca()
    ax.set_facecolor('#121212')
    pos = get_geographic_layout(G)

    # Crear una copia simulando el fallo
    G_broken = G.copy()
    G_broken.remove_nodes_from(failed_nodes)

    # Identificar componentes conexas resultantes
    components = sorted(list(nx.connected_components(G_broken)), key=len, reverse=True)
    
    # Dibujar aristas que siguen funcionando
    nx.draw_networkx_edges(G_broken, pos, edge_color='#444444', width=1.5, alpha=0.5)

    # Colorear nodos activos: si hay partición, colorear por componente; si no, por línea
    if len(components) > 1:
        try:
            cmap = plt.get_cmap('tab10')
        except AttributeError:
            import matplotlib.cm as cm
            cmap = cm.get_cmap('tab10')
            
        for i, comp in enumerate(components):
            node_list = list(comp)
            color = cmap(i % 10)
            nx.draw_networkx_nodes(G, pos, nodelist=node_list, 
                                   node_size=80, node_color=[color], 
                                   edgecolors='white', linewidths=0.5)
    else:
        # Una sola componente (red sigue conectada) -> colores de línea
        node_colors = [COLORES_LINEAS.get(G.nodes[n].get('linea', ''), '#00E5FF') for n in G_broken.nodes()]
        nx.draw_networkx_nodes(G_broken, pos, nodelist=list(G_broken.nodes()), 
                               node_size=80, node_color=node_colors, 
                               edgecolors='white', linewidths=0.5)

    # Dibujar las vías rotas hacia los andenes fallidos
    broken_edges = [(u, v) for u, v in G.edges() if (u in failed_nodes or v in failed_nodes)]
    nx.draw_networkx_edges(G, pos, edgelist=broken_edges, 
                           edge_color='#FF3333', width=2.5, style='dashed', alpha=0.85)
                           
    # Dibujar los andenes fallidos como grandes X rojas
    nx.draw_networkx_nodes(G, pos, nodelist=failed_nodes, 
                           node_size=900, node_color='#FF0000', 
                           node_shape='X', edgecolors='white', linewidths=1.5)
                           
    # Obtener nombre común de la estación
    nombres_estaciones = list(dict.fromkeys(G.nodes[n].get('nombre', n) for n in failed_nodes))
    nombre_display = ", ".join(nombres_estaciones)
    
    # Etiquetar los andenes caídos
    for fn in failed_nodes:
        pos_label = {fn: (pos[fn][0], pos[fn][1] + 0.0035)}
        lbl = f"{fn} (CAÍDA)"
        nx.draw_networkx_labels(G, pos_label, {fn: lbl}, 
                                font_size=12, font_color='#FF5555', font_weight='bold')

    # Etiquetar todas las estaciones restantes con letra pequeña para ubicación
    context_nodes = list(G_broken.nodes())
    context_labels = {n: G_broken.nodes[n].get('nombre', str(n)) for n in context_nodes}
    pos_context = {k: (v[0], v[1] + 0.0018) for k, v in pos.items() if k in context_nodes}
    nx.draw_networkx_labels(G_broken, pos_context, context_labels, font_size=7.5, font_color='#888888')

    num_comp = len(components)
    if num_comp > 1:
        aisladas = sum(len(c) for c in components[1:])
        estado = f"¡ALERTA! La red se dividió en {num_comp} fragmentos desconectados ({aisladas} andenes aislados)."
    else:
        estado = "La red SIGUE CONECTADA. Los usuarios pueden tomar rutas alternativas."
        
    if not title:
        titulo = f"Simulación de Cierre: {nombre_display} ({len(failed_nodes)} andén(es) afectado(s))\n{estado}"
    else:
        titulo = f"{title}\n{estado}"
        
    ax.set_aspect(1.0 / np.cos(np.radians(40.42)))
    plt.title(titulo, fontsize=20, fontweight='bold', color='white', pad=25)
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def plot_failed_edge_matplotlib(G, source, target, linea=None, title=None):
    """
    Visualiza el impacto del cierre o remoción de un tramo (arista) de vía o transbordo sobre el mapa geográfico.
    - Muestra el tramo cerrado en rojo discontinuo grueso con una marca de corte 'X'.
    - Resalta las estaciones de origen y destino del tramo.
    - Si existe una ruta alternativa, la dibuja y resalta en verde brillante.
    - Si la red se desconecta (arista puente), colorea los componentes desconectados.
    """
    try:
        res = simulate_edge_removal(G, source, target, linea)
    except ValueError as e:
        print("\n" + "=" * 75)
        print("[!] ERROR EN LA SIMULACIÓN DE CIERRE DE TRAMO:")
        print(str(e))
        print("=" * 75 + "\n")
        return None
        
    u, v = res['removed_edge']
    G_broken = res['new_graph']
    
    plt.figure(figsize=(26, 24), facecolor='#121212')
    ax = plt.gca()
    ax.set_facecolor('#121212')
    pos = get_geographic_layout(G)
    
    # 1. Aristas normales de la red
    other_edges = [e for e in G_broken.edges() if e != (u, v) and e != (v, u)]
    nx.draw_networkx_edges(G_broken, pos, edgelist=other_edges, edge_color='#333333', width=1.4, alpha=0.4)
    
    # 2. Si hay ruta alternativa, dibujarla en verde brillante
    if res.get('has_alternative_path') and len(res.get('alternative_path', [])) > 1:
        alt_path = res['alternative_path']
        alt_edges = list(zip(alt_path[:-1], alt_path[1:]))
        nx.draw_networkx_edges(G_broken, pos, edgelist=alt_edges, edge_color='#00FF00', width=4.5, alpha=0.9)
        nx.draw_networkx_nodes(G_broken, pos, nodelist=alt_path, node_size=120, node_color='#00FF00', edgecolors='white', linewidths=1.0)
        
        # Etiquetas de la ruta alternativa
        alt_labels = {n: G.nodes[n].get('nombre', n) for n in alt_path}
        pos_alt = {k: (v_pos[0], v_pos[1] + 0.0025) for k, v_pos in pos.items() if k in alt_path}
        nx.draw_networkx_labels(G_broken, pos_alt, alt_labels, font_size=10, font_color='#00FF00', font_weight='bold')
    
    # 3. Colorear nodos generales
    components_list = res.get('components', [])
    if res.get('num_components', 1) > 1 and components_list:
        try:
            cmap = plt.get_cmap('tab10')
        except AttributeError:
            import matplotlib.cm as cm
            cmap = cm.get_cmap('tab10')
        for i, comp in enumerate(components_list):
            comp_nodes = list(comp)
            color = cmap(i % 10)
            nx.draw_networkx_nodes(G_broken, pos, nodelist=comp_nodes, node_size=80, 
                                   node_color=[color] * len(comp_nodes), edgecolors='white', linewidths=0.5)
    else:
        node_colors = [COLORES_LINEAS.get(G.nodes[n].get('linea', ''), '#00E5FF') for n in G_broken.nodes()]
        nx.draw_networkx_nodes(G_broken, pos, nodelist=list(G_broken.nodes()), node_size=80, 
                               node_color=node_colors, edgecolors='white', linewidths=0.5)
                               
    # 4. Dibujar el tramo cortado en rojo grueso discontinuo
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color='#FF0000', width=5.0, style='dashed', alpha=0.95)
    
    # Punto medio del tramo cortado con una 'X' roja
    mid_x = (pos[u][0] + pos[v][0]) / 2.0
    mid_y = (pos[u][1] + pos[v][1]) / 2.0
    plt.scatter([mid_x], [mid_y], s=1200, c='#FF0000', marker='X', edgecolors='white', linewidths=2.0, zorder=10)
    
    # 5. Resaltar los extremos del tramo cortado
    nx.draw_networkx_nodes(G, pos, nodelist=[u], node_size=400, node_color='#FFFF00', edgecolors='white', linewidths=2)
    nx.draw_networkx_nodes(G, pos, nodelist=[v], node_size=400, node_color='#FF6600', edgecolors='white', linewidths=2)
    
    nx.draw_networkx_labels(G, {u: (pos[u][0], pos[u][1] - 0.0035)}, {u: f"{u} [CORTE]"}, 
                            font_size=11, font_color='#FFFF00', font_weight='bold')
    nx.draw_networkx_labels(G, {v: (pos[v][0], pos[v][1] - 0.0035)}, {v: f"{v} [CORTE]"}, 
                            font_size=11, font_color='#FF6600', font_weight='bold')
                            
    # 6. Etiquetas de contexto de estaciones
    alt_set = set(res.get('alternative_path', [])) if res.get('has_alternative_path') else set()
    context_nodes = [n for n in G_broken.nodes() if n not in [u, v] and n not in alt_set]
    context_labels = {n: G_broken.nodes[n].get('nombre', str(n)) for n in context_nodes}
    pos_context = {k: (val[0], val[1] + 0.0018) for k, val in pos.items() if k in context_nodes}
    nx.draw_networkx_labels(G_broken, pos_context, context_labels, font_size=7.5, font_color='#888888')
    
    # 7. Título y estado
    linea_info = f" (Línea {res['linea']})" if res.get('linea') else ""
    if res.get('has_alternative_path'):
        estado = (f"El tramo está CERRADO pero la red sigue conectada.\n"
                  f"Ruta alternativa más rápida: {res['alternative_time']} (+{res['time_increase']} respecto al tramo directo).")
    else:
        aisladas = sum(len(c) for c in components_list[1:]) if len(components_list) > 1 else len(res.get('isolated_nodes', []))
        estado = f"¡ALERTA TRAMO PUENTE! La clausura dividió la red en {res['num_components']} componentes ({aisladas} andenes aislados)."
        
    full_title = title if title else f"Simulación de Cierre de Tramo: {res['source_station']} <---> {res['target_station']}{linea_info}\n{estado}"
    
    ax.set_aspect(1.0 / np.cos(np.radians(40.42)))
    plt.title(full_title, fontsize=20, fontweight='bold', color='white', pad=25)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
