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
    plt.figure(figsize=(24, 24), facecolor='#121212')
    
    pos = nx.spring_layout(G, k=0.18, iterations=60, seed=42)
    
    # Separar aristas de vía y de transbordo
    via_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('tipo') == 'via']
    trans_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('tipo') == 'transbordo']
    
    # Colores de nodos según su línea
    node_colors = []
    for _, d in G.nodes(data=True):
        linea = d.get('linea', '')
        node_colors.append(COLORES_LINEAS.get(linea, '#00E5FF'))
        
    grados = dict(G.degree())
    node_sizes = [v * 60 + 80 for v in grados.values()]
    
    # 1. Dibujar aristas de transbordo (líneas punteadas blancas suaves)
    nx.draw_networkx_edges(G, pos, edgelist=trans_edges, width=1.8, 
                           style='dashed', edge_color='#E0E0E0', alpha=0.7)
    
    # 2. Dibujar aristas de vía férrea
    nx.draw_networkx_edges(G, pos, edgelist=via_edges, width=2.0, 
                           edge_color='#888888', alpha=0.6)
    
    # 3. Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                           node_color=node_colors, edgecolors='#FFFFFF', linewidths=1.2)
    
    # 4. Etiquetas de texto para estaciones con transbordo o terminales
    labels = {n: d.get('nombre', n) for n, d in G.nodes(data=True) if grados[n] >= 3}
    pos_labels = {k: (v[0], v[1]+0.012) for k, v in pos.items()}
    nx.draw_networkx_labels(G, pos_labels, labels, font_size=8, 
                            font_color='#FFFFFF', font_weight='bold')
    
    plt.title(f"{title}\n(Nodos = Andenes | Líneas punteadas = Transbordos a pie)", 
              fontsize=20, fontweight='bold', color='white', pad=20)
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
        
        net.add_node(
            node, 
            label=f"{nombre} ({linea})", 
            title=titulo_html, 
            color=color, 
            size=tamanio, 
            borderWidth=2, 
            borderWidthSelected=4, 
            shape='dot'
        )
        
    # Aristas
    for u, v, data in G.edges(data=True):
        peso = data.get('tiempo', 2.0)
        linea = data.get('linea', '')
        tipo = data.get('tipo', 'via')
        
        if tipo == 'transbordo':
            # Pasillo peatonal
            net.add_edge(
                u, v, 
                value=2.0, 
                title=f"Pasillo de Transbordo a pie: {peso:.1f} min", 
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
                title=f"Tramo Línea {linea}: {peso:.1f} min", 
                color=color, 
                width=3.5
            )
        
    # Físicas optimizadas
    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.25,
          "springLength": 80,
          "springConstant": 0.05,
          "damping": 0.09
        },
        "minVelocity": 0.75
      }
    }
    """)
    
    net.show(output_file, notebook=False)
    print(f"Visualización interactiva guardada en: {output_file}")
