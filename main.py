import sys
import os

from src.graph_builder import load_data, build_metro_graph
from src.algorithms import compare_routes
from src.metrics import get_all_metrics, get_top_stations_by_degree, get_top_stations_by_betweenness
from src.robustness import identify_articulation_points, simulate_node_removal
from src.visualization import plot_graph_matplotlib,plot_graph_pyvis,plot_route_matplotlib,plot_failed_station_matplotlib

data = load_data('./data/metro_madrid.json')
G = build_metro_graph(data)

print("Grafo del Metro de Madrid construido con éxito.")

while True:
    print("\n--- Menú de opciones ---")
    print("1. Comparar rutas entre dos estaciones")
    print("2. Obtener métricas de la red")
    print("3. Identificar puntos de articulación")
    print("4. Simular fallo de una estación o andén")
    print("5. Visualizar grafo completo (matplotlib)")
    print("6. Visualizar grafo completo (pyvis)")
    print("7. Salir")

    opcion =  int(input("Seleccione una opción (1-7): "))

    if opcion == 1:
        origen = input("Ingrese la estación de origen: ")
        destino = input("Ingrese la estación de destino: ")
        rutas = compare_routes(G, origen, destino)
        if rutas:
            for i, ruta in enumerate(rutas):
                print(f"Ruta {i+1}: {' -> '.join(ruta)}")
                plot_route_matplotlib(G, ruta)
        else:
            print(f"No se encontraron rutas entre '{origen}' y '{destino}'.")

    elif opcion == 2:
        metrics = get_all_metrics(G)
        print("\nMétricas de la red:")
        #for key, value in metrics.items():
        #    print(f"{key}: {value}")

        top_degree = get_top_stations_by_degree(G)
        top_betweenness = get_top_stations_by_betweenness(G)

        print("\nTop 5 estaciones por grado:")
        
        for i in top_degree:
            print(f"{i['nombre']}: {i['grado_total']}")

        print("\nTop 5 estaciones por centralidad de intermediación:")
        for i in top_betweenness:
            print(f"{i['nombre']}: {i['centralidad']:.4f}")

    elif opcion == 3:
        puntos_articulacion = identify_articulation_points(G)
        print("\nPuntos de articulación:")
        for point in puntos_articulacion:
            print(f" - {point}")

    elif opcion == 4:
        station_or_node = input("Ingrese la estación o andén a eliminar: ")
        resultado = simulate_node_removal(G, station_or_node)
        print(f"\nSimulación de eliminación de '{station_or_node}':")
        print(f"¿Sigue conectada la red? {'Sí' if resultado['is_connected'] else 'No'}")
        print(f"Número de componentes conectados: {resultado['num_components']}")
        print(f"Estaciones aisladas: {resultado['isolated_nodes']}")

        plot_failed_station_matplotlib(G, station_or_node)  

    elif opcion == 5:
        plot_graph_matplotlib(G)

    elif opcion == 6:
        plot_graph_pyvis(G)

    elif opcion == 7:
        print("Saliendo del programa.")
        break