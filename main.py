"""
PROYECTO DE AULA: METRO DE MADRID CON TEORÍA DE GRAFOS
Programa Principal Integral (Flujo Completo)
Asignaturas: Algoritmos y Programación - Matemáticas Discretas
"""

import sys
import os

# Asegurar que Python encuentre los módulos de la carpeta src
sys.path.append(os.path.abspath('src'))

from graph_builder import load_data, build_metro_graph, get_all_physical_stations
from algorithms import compare_routes, find_best_route, shortest_path_dijkstra, shortest_path_bfs
from metrics import get_all_metrics, calculate_betweenness_centrality, calculate_degree
from robustness import identify_articulation_points, simulate_node_removal
from visualization import plot_graph_pyvis, plot_route_matplotlib, plot_failed_station_matplotlib


def format_min_sec(minutos_float):
    """Convierte minutos decimales a formato MM:SS."""
    m = int(minutos_float)
    s = int(round((minutos_float - m) * 60))
    return f"{m:02d}:{s:02d} min"


def main():
    print("=" * 70)
    print("🚇 MODELADO Y ANÁLISIS DEL METRO DE MADRID MEDIANTE TEORÍA DE GRAFOS")
    print("=" * 70)

    # 1. Carga de datos y construcción del Grafo
    data_path = os.path.join('data', 'metro_madrid.json')
    if not os.path.exists(data_path):
        print(f"❌ Error: No se encontró el archivo de datos en {data_path}")
        return

    print("\n[1/5] 🏗️  Cargando datos y construyendo el grafo topológico...")
    raw_data = load_data(data_path)
    G = build_metro_graph(raw_data)
    
    num_nodos = G.number_of_nodes()
    num_aristas = G.number_of_edges()
    estaciones_fisicas = get_all_physical_stations(G)
    
    print(f"     ✅ Grafo construido exitosamente:")
    print(f"        • Nodos (Andenes): {num_nodos}")
    print(f"        • Aristas (Vías y Pasillos): {num_aristas}")
    print(f"        • Estaciones físicas únicas: {len(estaciones_fisicas)}")

    # 2. Búsqueda y Comparación de Rutas Óptimas (Dijkstra vs BFS)
    origen = "Sol"
    destino = "Nuevos Ministerios"
    print(f"\n[2/5] 🧭 Calculando y comparando rutas de '{origen}' a '{destino}'...")
    
    resultado = compare_routes(G, origen, destino)
    
    r_tiempo = resultado.get('menor_tiempo')
    r_transb = resultado.get('menores_transbordos')
    
    if r_tiempo:
        print("\n     ⚡ RUTA 1: MENOR TIEMPO (Algoritmo de Dijkstra)")
        print(f"        • Tiempo total estimado: {format_min_sec(r_tiempo['tiempo_total'])}")
        print(f"        • Tiempo en tren:        {format_min_sec(r_tiempo['tiempo_tren'])}")
        print(f"        • Tiempo en transbordos: {format_min_sec(r_tiempo['tiempo_transbordo'])}")
        print(f"        • Paradas de tren:       {r_tiempo['num_paradas_tren']}")
        print(f"        • Transbordos a pie:     {r_tiempo['num_transbordos']}")
        print(f"        • Líneas utilizadas:     {', '.join(r_tiempo['lineas_usadas'])}")
        print("        • Itinerario paso a paso:")
        for paso, instruccion in enumerate(r_tiempo['instrucciones'], 1):
            print(f"          {paso}. {instruccion}")

    if r_transb:
        print("\n     🔄 RUTA 2: MENORES TRANSBORDOS (Algoritmo BFS)")
        print(f"        • Tiempo total estimado: {format_min_sec(r_transb['tiempo_total'])}")
        print(f"        • Transbordos a pie:     {r_transb['num_transbordos']}")
        print(f"        • Paradas de tren:       {r_transb['num_paradas_tren']}")
        print(f"        • Líneas utilizadas:     {', '.join(r_transb['lineas_usadas'])}")

    # 3. Métricas Topológicas y Centralidad
    print("\n[3/5] 📊 Calculando métricas estructurales de la red...")
    metricas = get_all_metrics(G)
    
    print(f"     • Densidad de la red: {metricas.get('density', 0.0):.6f}")
    print(f"     • Diámetro de la red: {metricas.get('diameter', 0)} tramos")
    
    # Top 5 estaciones con mayor Centralidad de Intermediación (Betweenness)
    bc_estaciones = metricas.get('station_betweenness', {})
    top_bc = sorted(bc_estaciones.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n     ⭐ TOP 5 ESTACIONES MÁS IMPORTANTES (Betweenness Centrality):")
    for i, (est, valor) in enumerate(top_bc, 1):
        print(f"        {i}. {est:<25} Centralidad: {valor:.4f}")

    # Top 5 estaciones con mayor Grado (Conexiones físicas)
    grado_estaciones = metricas.get('station_degree', {})
    top_deg = sorted(grado_estaciones.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n     🔗 TOP 5 ESTACIONES CON MAYOR NÚMERO DE CONEXIONES (Grado):")
    for i, (est, valor) in enumerate(top_deg, 1):
        print(f"        {i}. {est:<25} Grado: {valor} vías/transbordos")

    # 4. Análisis de Robustez y Fallos
    print("\n[4/5] 🛡️  Evaluando robustez y puntos críticos de la red...")
    puntos_articulacion = identify_articulation_points(G)
    print(f"     • Total de puntos de corte (Puntos de Articulación): {len(puntos_articulacion)} andenes")
    
    # Simulación de caída de una estación
    nodo_prueba = "Sol [L1]"
    if nodo_prueba in G:
        simulacion = simulate_node_removal(G, nodo_prueba)
        print(f"\n     ⚠️  Simulación de fallo en '{nodo_prueba}':")
        print(f"        • ¿La red permanece conexa?: {'Sí' if simulacion['is_connected'] else 'No'}")
        print(f"        • Componentes conexas resultantes: {simulacion['num_components']}")

    # 5. Generación de Visualizaciones
    print("\n[5/5] 🎨 Generando visualizaciones gráficas...")
    
    # Generar HTML con Pyvis
    html_output = os.path.join("output", "figures", "metro_madrid_pyvis.html")
    os.makedirs(os.path.dirname(html_output), exist_ok=True)
    plot_graph_pyvis(G, output_file=html_output)
    print(f"     ✅ Mapa interactivo web guardado en: {html_output}")

    # Preguntar si desea abrir las ventanas gráficas de Matplotlib
    print("\n" + "=" * 70)
    print("🎉 ¡EJECUCIÓN DEL PROGRAMA COMPLETO FINALIZADA CON ÉXITO!")
    print("=" * 70)
    
    opcion = input("\n¿Deseas mostrar los gráficos de Matplotlib (Ruta y Fallo)? [s/N]: ").strip().lower()
    if opcion in ['s', 'si', 'y', 'yes']:
        if r_tiempo and 'path' in r_tiempo:
            print("Mostrando visualización de la Ruta Óptima...")
            plot_route_matplotlib(G, r_tiempo['path'], title=f"Ruta Óptima: {origen} -> {destino}")
            
        print(f"Mostrando simulación visual de fallo en '{nodo_prueba}'...")
        plot_failed_station_matplotlib(G, nodo_prueba)


if __name__ == "__main__":
    main()
