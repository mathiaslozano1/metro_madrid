# Dos herramientas para consultar el metro
#   1. mostrar_vecinas: ver a qué estaciones se llega directamente
#   2. opcion_ruta_con_parada: ruta de origen a destino pasando por una estación intermedia elegida por el usuario

def pedir_estacion(G, mensaje):
    # Le pide una estación al usuario.
    # Si la escribe mal, se la vuelve a pedir hasta que la escriba bien.
    while True:
        nombre = input(mensaje).strip()

        if nombre in G.nodes:
            return nombre

        print("Esa estación no existe. Intente de nuevo.")

# 1. ESTACIONES VECINAS

def mostrar_vecinas(G):
    # Esta es la función que se llama desde el menú de main.py
    seguir = "s"

    # Repetimos mientras el usuario quiera consultar otra estación
    while seguir == "s":

        estacion = input("Escriba el nombre de una estación: ").strip()

        if estacion in G.nodes:                    # ¿existe en el mapa?
            vecinas = list(G.neighbors(estacion))  # estaciones conectadas a ella

            print(f"Desde {estacion} se puede llegar a {len(vecinas)} estaciones:")

            # Mostramos las vecinas una por una, contando desde 0
            contador = 0
            while contador < len(vecinas):
                print(" -", vecinas[contador])
                contador = contador + 1            # pasamos a la siguiente
        else:
            print("Esa estación no existe.")

        seguir = input("¿Desea consultar otra estación? (s/n): ").strip().lower()

        # Si no responde 's' ni 'n', se lo volvemos a preguntar
        while seguir != "s" and seguir != "n":
            seguir = input("Responda solo 's' o 'n': ").strip().lower()

    print("Consulta finalizada.")


# 2. RUTA PASANDO POR UNA ESTACIÓN INTERMEDIA

def buscar_ruta(G, origen, destino):
    # Busca el camino con menos estaciones entre origen y destino.
    caminos_pendientes = [[origen]]      # caminos que faltan por revisar
    estaciones_visitadas = [origen]      # estaciones por las que ya pasamos

    # Repetimos mientras todavía quede algún camino por revisar
    while len(caminos_pendientes) > 0:

        camino = caminos_pendientes.pop(0)   # primer camino de la lista
        estacion_actual = camino[-1]         # su última estación

        if estacion_actual == destino:       # ¿ya llegamos?
            return camino

        for vecina in G.neighbors(estacion_actual):
            if vecina not in estaciones_visitadas:
                estaciones_visitadas.append(vecina)
                caminos_pendientes.append(camino + [vecina])

    return None                              # no hay ruta


def opcion_ruta_con_parada(G):
    origen = pedir_estacion(G, "Estación de origen: ")
    parada = pedir_estacion(G, "Estación por la que desea pasar: ")
    destino = pedir_estacion(G, "Estación de destino: ")

    # El viaje se divide en dos partes: origen -> parada y parada -> destino
    primera_parte = buscar_ruta(G, origen, parada)
    segunda_parte = buscar_ruta(G, parada, destino)

    if primera_parte is None or segunda_parte is None:
        print("No hay ruta pasando por esa estación.")
        return

    # Unimos las dos partes (quitamos la parada repetida en la segunda)
    ruta_completa = primera_parte + segunda_parte[1:]

    print(f"Ruta pasando por {parada}:")
    for estacion in ruta_completa:
        print(" -", estacion)

    print(f"Total de estaciones recorridas: {len(ruta_completa)}")
