import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

# Diccionario de colores oficiales aproximados del Metro de Madrid
COLORES_LINEAS = {
    '1': '#0097D6', '2': '#FF2A14', '3': '#FFD100', '4': '#93351C',
    '5': '#80C23D', '6': '#A8A9AD', '7': '#F68315', '8': '#E35F92',
    '9': '#8B1E91', '10': '#0039A6', '11': '#009139', '12': '#A19100',
    'R': '#FFFFFF'
}

def plot_graph_matplotlib(G, title="Red del Metro de Madrid"):
    """
    Dibuja el grafo de matplotlib de forma más espaciada y estilizada.
    """
    plt.figure(figsize=(24, 24), facecolor='#f4f4f4')
    
    # Layout más orgánico para grafos grandes
    pos = nx.spring_layout(G, k=0.15, iterations=50, seed=42)
    
    # Tamaños dinámicos basados en la cantidad de conexiones (grado)
    grados = dict(G.degree())
    node_sizes = [v * 100 + 150 for v in grados.values()]
    
    labels = nx.get_node_attributes(G, 'nombre')
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                           node_color='#ff5a5f', edgecolors='white', linewidths=2)
    
    # Dibujar aristas suaves
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.4, edge_color='#888888')
    
    # Etiquetas de nodos con un pequeño offset para no superponerse tanto
    pos_labels = {k: (v[0], v[1]+0.015) for k, v in pos.items()}
    nx.draw_networkx_labels(G, pos_labels, labels, font_size=9, font_family='sans-serif', font_weight='bold')
    
    plt.title(title, fontsize=24, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def plot_graph_pyvis(G, output_file="metro_madrid_pyvis.html"):
    """
    Genera una visualización interactiva Premium usando pyvis.
    """
    net = Network(height="900px", width="100%", bgcolor="#1a1a2e", font_color="#e9e9e9", 
                  select_menu=True, filter_menu=True)
    
    grados = dict(G.degree())
    
    # Nodos
    for node in G.nodes():
        nombre = G.nodes[node].get('nombre', node)
        lineas = list(G.nodes[node].get('lineas', []))
        
        # Color del nodo basado en su primera línea, tamaño basado en conexiones
        color = COLORES_LINEAS.get(lineas[0], '#ffffff') if lineas else '#ffffff'
        tamanio = grados[node] * 3 + 15
        
        titulo_html = f"<b>{nombre}</b><br>Líneas: {', '.join(lineas)}<br>Conexiones: {grados[node]}"
        
        net.add_node(node, label=nombre, title=titulo_html, color=color, 
                     size=tamanio, borderWidth=2, borderWidthSelected=4, shape='dot')
        
    # Aristas
    for u, v, data in G.edges(data=True):
        peso = data.get('weight', 1)
        linea = data.get('linea', '')
        color = COLORES_LINEAS.get(linea, '#888888')
        
        titulo_arista = f"Línea {linea} ({peso} min)"
        net.add_edge(u, v, value=peso, title=titulo_arista, color=color, alpha=0.6)
        
    # Físicas optimizadas para que la red se expanda correctamente y no se amontone
    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -15000,
          "centralGravity": 0.2,
          "springLength": 100,
          "springConstant": 0.05,
          "damping": 0.09
        },
        "minVelocity": 0.75
      }
    }
    """)
    
    net.show(output_file, notebook=False)
    print(f"Visualización interactiva premium guardada en: {output_file}")
