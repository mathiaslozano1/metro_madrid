
from src.graph_builder import load_data, build_metro_graph
from src.algorithms import compare_routes
from src.metrics import get_all_metrics, get_top_stations_by_degree, get_top_stations_by_betweenness
from src.robustness import identify_articulation_points, simulate_node_removal, simulate_edge_removal
from src.visualization import plot_failed_edge_matplotlib, plot_graph_matplotlib,plot_graph_pyvis,plot_route_matplotlib,plot_failed_station_matplotlib

data = load_data('./data/metro_madrid.json')
G = build_metro_graph(data)

print("Grafo del Metro de Madrid construido con éxito.")

while True:
    print("\n--- Menú de opciones ---")
    print("1. Comparar rutas entre dos estaciones")
    print("2. Obtener métricas de la red")
    print("3. Identificar puntos de articulación")
    print("4. Simular fallo de una estación o andén")
    print("5. Simular fallo de un tramo ferroviario")
    print("6. Visualizar grafo completo (matplotlib)")
    print("7. Visualizar grafo completo (pyvis)")
    print("8. Salir")

    opcion =  int(input("Seleccione una opción (1-8): "))

    if opcion == 1:
        origen = input("Ingrese la estación de origen: ")
        destino = input("Ingrese la estación de destino: ")
        rutas = compare_routes(G, origen, destino)
        print(f"\nRutas encontradas entre '{origen}' y '{destino}':")
        print(f"Número de rutas encontradas: {len(rutas)}")
        print("----Mejor ruta por tiempo estimado:----")
        for i in rutas['menor_tiempo']['path']:
            print(f" - {i}")
        print(f"\nTiempo estimado: {rutas['menor_tiempo']['tiempo_total_texto']} minutos")
        print(f"Tiempo en tren de {rutas['menor_tiempo']['tiempo_tren_formato']} minutos")
        print(f"Transbordos: {rutas['menor_tiempo']['num_transbordos']}")
        print(f"Tiempo aproximado en transbordo:{rutas['menor_tiempo']['tiempo_transbordo_formato']} minutos")

        print("\n----Mejor ruta por menor número de transbordos:----")
        for i in rutas['menores_transbordos']['path']:
            print(f" - {i}")
        print(f"Tiempo estimado: {rutas['menores_transbordos']['tiempo_total_formato']} minutos")
        print(f"Transbordos: {rutas['menores_transbordos']['num_transbordos']}")

        plot_route_matplotlib(G, rutas['menor_tiempo']['path'])

        

        
    elif opcion == 2:
        metrics = get_all_metrics(G)
        print("\nMétricas de la red:")

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
        origen = input("Ingrese la estación de origen del tramo: ")
        destino = input("Ingrese la estación de destino del tramo: ")
        linea = input("Ingrese la línea del tramo (ej. L1, L2, etc. Opcional): ")
        try:
            resultado = simulate_edge_removal(G, origen, destino, linea if linea.strip() else None)
            print(f"\nSimulación de eliminación del tramo '{resultado['source_station']} - {resultado['target_station']}' en la línea '{resultado['linea']}':")
            print(f"¿Sigue conectada la red? {'Sí' if resultado['is_connected'] else 'No'}")
            print(f"Número de componentes conectados: {resultado['num_components']}")
            print(f"Estaciones aisladas: {resultado['isolated_nodes']}")
            if resultado['has_alternative_path']:
                print(f"Ruta alternativa más rápida: {resultado['alternative_time']} (+{resultado['time_increase']} respecto al tramo directo)")

            plot_failed_edge_matplotlib(G, origen, destino, linea if linea.strip() else None)
        except ValueError as e:
            print(f"\n Error al simular tramo: {e}")

    elif opcion == 6:
        plot_graph_matplotlib(G)

    elif opcion == 7:
        plot_graph_pyvis(G)

    elif opcion == 8:
        print("Saliendo del programa.")
        break