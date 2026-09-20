import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

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

def plot_graph_matplotlib(G, title="Red del Metro de Madrid (Modelo Estación-Línea)"):
    """
    Dibuja el grafo en matplotlib diferenciando vías de tren de pasillos de transbordo.
    """
    plt.figure(figsize=(36, 36), facecolor='#121212')
    
    # Layout más espaciado para que los 291 nombres se distribuyan limpiamente
    pos = nx.spring_layout(G, k=0.25, iterations=80, seed=42)
    
    # Separar aristas de vía y de transbordo
    via_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('tipo') == 'via']
    trans_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('tipo') == 'transbordo']
    
    # Colores de nodos según su línea
    node_colors = []
    for _, d in G.nodes(data=True):
        linea = d.get('linea', '')
        node_colors.append(COLORES_LINEAS.get(linea, '#00E5FF'))
        
    grados = dict(G.degree())
    node_sizes = [v * 50 + 70 for v in grados.values()]
    
    # 1. Dibujar aristas de transbordo (líneas punteadas blancas suaves)
    nx.draw_networkx_edges(G, pos, edgelist=trans_edges, width=1.5, 
                           style='dashed', edge_color='#E0E0E0', alpha=0.7)
    
    # 2. Dibujar aristas de vía férrea
    nx.draw_networkx_edges(G, pos, edgelist=via_edges, width=1.8, 
                           edge_color='#888888', alpha=0.6)
    
    # 3. Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                           node_color=node_colors, edgecolors='#FFFFFF', linewidths=1.0)
    
    # 4. Etiquetas de texto para TODOS los nodos de la red sin excepción
    labels = {n: f"{d.get('nombre', n)}" for n, d in G.nodes(data=True)}
    pos_labels = {k: (v[0], v[1]+0.009) for k, v in pos.items()}
    nx.draw_networkx_labels(G, pos_labels, labels, font_size=6.5, 
                            font_color='#FFFFFF', font_weight='bold',
                            font_family='sans-serif')
    
    plt.title(f"{title}\n(Todos los nodos con nombre | Nodos = Andenes | Líneas punteadas = Transbordos)", 
              fontsize=22, fontweight='bold', color='white', pad=25)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def plot_graph_pyvis(G, output_file="metro_madrid_pyvis.html"):
    """
    Genera una visualización interactiva Premium con Pyvis bajo el modelo Estación-Línea.
    """
    net = Network(height="950px", width="100%", bgcolor="#141420", font_color="#e0e0e0", 
                  select_menu=True, filter_menu=True)
    
    grados = dict(G.degree())
    
    # Nodos
    # Calcular posiciones fijas para que no pierda la forma
    pos = nx.spring_layout(G, k=0.18, iterations=100, seed=42)
    
    for node, d in G.nodes(data=True):
        nombre = d.get('nombre', node)
        linea = d.get('linea', '')
        color = COLORES_LINEAS.get(linea, '#00E5FF')
        grado = grados.get(node, 1)
        
        tamanio = grado * 3.5 + 14
        titulo_html = (
            f"<div style='font-family: Arial; padding: 5px; color: #222;'>"
            f"<b>{nombre}</b><br>"
            f"Línea: <b>{linea}</b><br>"
            f"Conexiones (Grado): {grado}"
            f"</div>"
        )
        
        # Multiplicamos la coordenada por un factor para que se expanda bien
        x = pos[node][0] * 1000
        y = pos[node][1] * 1000
        
        net.add_node(
            node, 
            label=f"{nombre} ({linea})", 
            title=titulo_html, 
            color=color, 
            size=tamanio, 
            font={'size': 13, 'color': '#ffffff', 'face': 'arial', 'strokeWidth': 2, 'strokeColor': '#000000'},
            borderWidth=2, 
            borderWidthSelected=4, 
            shape='dot',
            x=x,
            y=y
        )
        
    # Función auxiliar para formatear tiempo (min:seg)
    def format_time(peso):
        m = int(peso)
        s = int(round((peso - m) * 60))
        return f"{m}:{s:02d}"

    # Aristas
    for u, v, data in G.edges(data=True):
        peso = data.get('tiempo', 2.0)
        linea = data.get('linea', '')
        tipo = data.get('tipo', 'via')
        
        tiempo_formateado = format_time(peso)
        
        if tipo == 'transbordo':
            # Pasillo peatonal
            net.add_edge(
                u, v, 
                value=2.0, 
                title=f"Pasillo de Transbordo a pie: {tiempo_formateado} min", 
                color="#FFFFFF", 
                dashes=True, 
                width=2
            )
        else:
            # Tramo ferroviario
            color = COLORES_LINEAS.get(linea, '#888888')
            net.add_edge(
                u, v, 
                value=peso, 
                title=f"Tramo Línea {linea}: {tiempo_formateado} min", 
                color=color, 
                width=3.5
            )
        
    # Físicas desactivadas para que no se mueva el grafo
    net.set_options("""
    var options = {
      "physics": {
        "enabled": false
      }
    }
    """)
    
    # Generar el HTML y escribirlo usando UTF-8 para arreglar las tildes
    html_content = net.generate_html(notebook=False)
    # Insertar la etiqueta meta charset="utf-8" si no la tiene
    if "<meta charset=\"utf-8\">" not in html_content.lower():
        html_content = html_content.replace("<head>", "<head>\n<meta charset=\"utf-8\">")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Visualización interactiva guardada en: {output_file}")


def plot_route_matplotlib(G, path, title="Ruta Óptima"):
    """
    Genera una visualización estática destacando la ruta óptima usando matplotlib.
    path es una lista de nodos en el orden del recorrido.
    """
    plt.figure(figsize=(24, 24), facecolor='#121212')
    
    pos = nx.spring_layout(G, k=0.18, iterations=60, seed=42)
    
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
    nx.draw_networkx_edges(G, pos, edgelist=route_edges, width=5.0, edge_color='#00FF00', alpha=0.9)
    nx.draw_networkx_nodes(G, pos, nodelist=route_nodes, node_size=150, node_color='#00FF00', edgecolors='#FFFFFF', linewidths=2)
    
    # 3. Etiquetas de texto sólo para los nodos de la ruta
    labels = {n: G.nodes[n].get('nombre', str(n)) for n in route_nodes}
    pos_labels = {k: (v[0], v[1]+0.015) for k, v in pos.items() if k in route_nodes}
    nx.draw_networkx_labels(G, pos_labels, labels, font_size=12, font_color='#00FF00', font_weight='bold')
    
    # 4. Resaltar inicio y fin
    if path:
        start_node, end_node = path[0], path[-1]
        nx.draw_networkx_nodes(G, pos, nodelist=[start_node], node_size=300, node_color='#FFFF00', edgecolors='#FFFFFF')
        nx.draw_networkx_nodes(G, pos, nodelist=[end_node], node_size=300, node_color='#FF0000', edgecolors='#FFFFFF')
        
        pos_start = {start_node: (pos[start_node][0], pos[start_node][1]-0.02)}
        pos_end = {end_node: (pos[end_node][0], pos[end_node][1]-0.02)}
        nx.draw_networkx_labels(G, pos_start, {start_node: 'INICIO'}, font_size=14, font_color='#FFFF00', font_weight='bold')
        nx.draw_networkx_labels(G, pos_end, {end_node: 'FIN'}, font_size=14, font_color='#FF0000', font_weight='bold')
    
    plt.title(title, fontsize=24, fontweight='bold', color='white', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()


def plot_failed_station_matplotlib(G, failed_node):
    """
    Visualiza cómo se divide la red si una estación específica falla.
    Muestra la estación caída y colorea de forma distinta los fragmentos
    desconectados que quedan (componentes conexas).
    """
    if failed_node not in G:
        print(f"Error: La estación '{failed_node}' no existe en el grafo.")
        return

    plt.figure(figsize=(24, 24), facecolor='#121212')
    pos = nx.spring_layout(G, k=0.25, iterations=60, seed=42)

    # Crear una copia simulando el fallo
    G_broken = G.copy()
    G_broken.remove_node(failed_node)

    # Identificar componentes conexas resultantes
    components = list(nx.connected_components(G_broken))
    
    # Dibujar aristas que siguen funcionando
    nx.draw_networkx_edges(G_broken, pos, edge_color='#666666', width=1.5, alpha=0.5)

    # Obtener una paleta de colores para diferenciar las partes rotas
    try:
        cmap = plt.get_cmap('Set1')
    except AttributeError:
        # Fallback por compatibilidad
        import matplotlib.cm as cm
        cmap = cm.get_cmap('Set1')
        
    for i, comp in enumerate(components):
        node_list = list(comp)
        # Asignar un color distinto a cada fragmento desconectado
        color = cmap(i % 9) # Set1 tiene 9 colores discretos
        nx.draw_networkx_nodes(G, pos, nodelist=node_list, 
                               node_size=80, node_color=[color], 
                               edgecolors='white', linewidths=0.5)
                               
    # Dibujar las vías/conexiones rotas hacia la estación fallida
    broken_edges = list(G.edges(failed_node))
    nx.draw_networkx_edges(G, pos, edgelist=broken_edges, 
                           edge_color='red', width=2.5, style='dashed', alpha=0.8)
                           
    # Dibujar la estación fallida como una gran X roja
    nx.draw_networkx_nodes(G, pos, nodelist=[failed_node], 
                           node_size=800, node_color='red', 
                           node_shape='X', edgecolors='white', linewidths=1)
                           
    # Etiquetar la estación caída
    nombre_fallo = G.nodes[failed_node].get('nombre', str(failed_node))
    pos_labels = {failed_node: (pos[failed_node][0], pos[failed_node][1] + 0.02)}
    nx.draw_networkx_labels(G, pos_labels, {failed_node: f"{nombre_fallo} (CAÍDA)"}, 
                            font_size=16, font_color='red', font_weight='bold')

    # Etiquetar algunas de las estaciones restantes para dar contexto
    grados = dict(G_broken.degree())
    context_nodes = [n for n in G_broken.nodes() ]
    context_labels = {n: G_broken.nodes[n].get('nombre', str(n)) for n in context_nodes}
    pos_context = {k: (v[0], v[1] + 0.01) for k, v in pos.items() if k in context_nodes}
    nx.draw_networkx_labels(G_broken, pos_context, context_labels, font_size=8, font_color='#AAAAAA')

    estado = f"La red se dividió en {len(components)} partes separadas." if len(components) > 1 else "La red sigue conectada (sin divisiones)."
    titulo = f"Impacto de Fallo en Estación: {nombre_fallo}\n{estado}"
    
    plt.title(titulo, fontsize=24, fontweight='bold', color='white', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()
