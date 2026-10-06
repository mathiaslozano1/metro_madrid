
from src.graph_builder import load_data, build_metro_graph
from src.algorithms import compare_routes, find_route_with_disruption
from src.metrics import get_all_metrics, get_top_stations_by_degree, get_top_stations_by_betweenness
from src.robustness import identify_articulation_points, simulate_node_removal, simulate_edge_removal
from src.visualization import plot_failed_edge_matplotlib, plot_graph_matplotlib, plot_graph_pyvis, plot_graph_presentation, plot_route_matplotlib, plot_failed_station_matplotlib, plot_contingency_route_matplotlib

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
    print("6. Calcular ruta alternativa ante incidencias (estación/tramo cerrado)")
    print("7. Visualizar grafo completo")
    print("8. Menú Interactivo ")
    print("9. Menú Interactivo para Presentación Final ")
    print("10. Salir")
    
    opcion = input("Seleccione una opción (1-10): ")
    try:
        opcion = int(opcion)
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
        
                print("\nTop 5 estaciones por conexiones entre estaciones:")
                
                for i in top_degree:
                    print(f"{i['nombre']}: {i['grado_total']} conexiones ({i['num_lineas']} líneas: {', '.join(i['lineas'])})")
        
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
                origen = input("Ingrese la estación de origen: ")
                destino = input("Ingrese la estación de destino: ")
                print("\nTipo de incidencia a evitar:")
                print("  a. Estación completa o andén específico")
                print("  b. Tramo de vía entre dos estaciones")
                tipo_inc = input("Seleccione (a/b): ").strip().lower()
                
                avoid_station = None
                avoid_line = None
                avoid_edge = None
                
                if tipo_inc == 'b':
                    tramo_orig = input("Estación 1 del tramo a evitar: ").strip()
                    tramo_dest = input("Estación 2 del tramo a evitar: ").strip()
                    tramo_linea = input("Línea del tramo (ej. L1, o Enter para cualquiera): ").strip()
                    avoid_edge = (tramo_orig, tramo_dest, tramo_linea if tramo_linea else None)
                else:
                    avoid_station = input("Estación a evitar: ").strip()
                    avoid_line = input("Línea específica a cerrar en esa estación (Enter para estación completa): ").strip() or None
                    
                try:
                    res = find_route_with_disruption(G, origen, destino, avoid_station=avoid_station, avoid_line=avoid_line, avoid_edge=avoid_edge)
                    
                    print("\n" + "=" * 80)
                    print("🚆 PLANIFICADOR DE CONTINGENCIA — RUTA ALTERNATIVA ANTE INCIDENCIAS")
                    print("=" * 80)
                    print(f"  • Estación Origen:     {res['origen']}")
                    print(f"  • Estación Destino:    {res['destino']}")
                    print(f"  • Incidencia Evitada:  {res['elementos_excluidos']}")
                    print("=" * 80)
        
                    if not res['es_posible']:
                        print("\n❌ NO EXISTE RUTA DISPONIBLE:")
                        print(f"   La clausura de '{res['elementos_excluidos']}' ha fragmentado la conectividad")
                        print(f"   entre '{res['origen']}' y '{res['destino']}'. No hay alternativas ferroviarias")
                        print("   activas disponibles en la red para completar este trayecto.")
                        print("=" * 80)
                    else:
                        det = res['ruta_desvio']
                        norm = res['ruta_normal']
                        
                        print("\n✅ ¡RUTA ALTERNATIVA DE CONTINGENCIA LOCALIZADA CON ÉXITO!")
                        print("-" * 80)
                        print("📊 CUADRO COMPARATIVO DE IMPACTO:")
                        print("-" * 80)
                        print(f"  {'Métrica':<25} {'Ruta Habitual':<20} {'Ruta Alternativa':<20} {'Impacto':<12}")
                        print(f"  {'-'*23} {'-'*18} {'-'*18} {'-'*10}")
                        
                        t_norm = norm['tiempo_total_texto'] if norm else 'N/A'
                        t_det = det['tiempo_total_texto']
                        impacto_t = f"+{res['sobrecosto_tiempo_texto']}" if norm else 'N/A'
                        print(f"  {'⏱️  Tiempo Total':<25} {t_norm:<20} {t_det:<20} {impacto_t:<12}")
        
                        tr_norm = f"{norm['tiempo_tren_formato']} min" if norm else 'N/A'
                        tr_det = f"{det['tiempo_tren_formato']} min"
                        print(f"  {'🚇 Tiempo en Tren':<25} {tr_norm:<20} {tr_det:<20} {'—':<12}")
        
                        tb_norm = f"{norm['tiempo_transbordo_formato']} min" if norm else 'N/A'
                        tb_det = f"{det['tiempo_transbordo_formato']} min"
                        print(f"  {'🚶 Tiempo Transbordos':<25} {tb_norm:<20} {tb_det:<20} {'—':<12}")
        
                        nb_norm = str(norm['num_transbordos']) if norm else 'N/A'
                        nb_det = str(det['num_transbordos'])
                        diff_tb = f"{det['num_transbordos'] - norm['num_transbordos']:+d}" if norm else 'N/A'
                        print(f"  {'🔄 Transbordos':<25} {nb_norm:<20} {nb_det:<20} {diff_tb:<12}")
        
                        np_norm = str(norm['num_paradas_tren']) if norm else 'N/A'
                        np_det = str(det['num_paradas_tren'])
                        diff_np = f"{det['num_paradas_tren'] - norm['num_paradas_tren']:+d}" if norm else 'N/A'
                        print(f"  {'🚉 Paradas en Tren':<25} {np_norm:<20} {np_det:<20} {diff_np:<12}")
                        print("-" * 80)
        
                        print("\n🗺️  ITINERARIO PASO A PASO DEL DESVÍO:")
                        for step_idx, inst in enumerate(det['instrucciones'], 1):
                            print(f"   {step_idx}. {inst}")
        
                        print("\n💡 EXPLICACIÓN DEL DESVÍO:")
                        lineas_usadas = ", ".join(f"Línea {l}" for l in det.get('lineas_usadas', []))
                        print(f"   Para sortear la incidencia en [{res['elementos_excluidos']}], la red")
                        print(f"   reencamina el viaje a través de: {lineas_usadas}.")
                        if norm:
                            print(f"   El pasajero experimenta un incremento de viaje de solo +{res['sobrecosto_tiempo_texto']}")
                            print(f"   frente al itinerario habitual ({norm['tiempo_total_texto']}).")
                        print("=" * 80)
        
                        ver_mapa = input("\n¿Desea visualizar el mapa de la ruta alternativa con el punto de corte? (s/n): ").strip().lower()
                        if ver_mapa == 's':
                            plot_contingency_route_matplotlib(G, res)
        
                except Exception as e:
                    print(f"\n❌ Error al calcular ruta con incidencia: {e}")
        
        elif opcion == 7:
                plot_graph_matplotlib(G)
        
        elif opcion == 8:
                plot_graph_pyvis(G)
        
        elif opcion == 9:
                plot_graph_presentation(G)
        
        elif opcion == 10:
                print("Saliendo del programa.")
                break
        
        else:
                print("Opción no válida. Por favor, seleccione una opción del 1 al 10.")
        
        
    except ValueError:
        print("Opción no válida. Por favor, seleccione una opción del 1 al 10.")
        continue

    