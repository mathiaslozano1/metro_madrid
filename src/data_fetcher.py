import requests
import json
import math
import os
from itertools import combinations

def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en kilómetros entre dos coordenadas GPS."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def estimate_time(dist_km):
    """Estima el tiempo de viaje en tren (mínimo 1.2 min, velocidad media 30 km/h)."""
    tiempo_min = dist_km / 0.5
    return round(max(1.2, tiempo_min), 1)

def build_station_line_dataset(transfer_penalty_minutes=4, output_file='data/metro_madrid.json'):
    """
    Construye el dataset oficial del modelo Estación-Línea del Metro de Madrid.
    - Cada nodo es un andén: '{Estación} [{Línea}]'.
    - Aristas tipo 'via': Tramos ferroviarios en tren.
    - Aristas tipo 'transbordo': Caminata y espera entre andenes de la misma estación.
    """
    print("Iniciando construcción del modelo Estación-Línea...")
    
    # Comprobar si tenemos datos previos descargados en data/metro_madrid.json
    raw_data = None
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception:
            raw_data = None
            
    # Intentar consultar Overpass si no hay datos o si se desea refrescar
    downloaded_data = False
    query = """
    [out:json][timeout:250];
    area[name="Comunidad de Madrid"]->.searchArea;
    relation["route"="subway"]["network"="Metro de Madrid"](area.searchArea);
    out body;
    >;
    out body qt;
    """
    headers = {
        'User-Agent': 'MetroMadridModeler/2.0 (student.project@madrid.edu)',
        'Accept': 'application/json'
    }
    
    # Si no tenemos estaciones válidas en raw_data, probamos Overpass
    if not raw_data or 'estaciones' not in raw_data or len(raw_data['estaciones']) < 10:
        for url in ['https://overpass.kumi.systems/api/interpreter', 'https://lz4.overpass-api.de/api/interpreter']:
            try:
                print(f"Intentando descargar desde {url}...")
                resp = requests.post(url, data={'data': query}, headers=headers, timeout=60)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    downloaded_data = True
                    print("Descarga exitosa desde Overpass.")
                    break
            except Exception as e:
                print(f"No se pudo conectar a {url}: {e}")

    # Si se descargaron datos crudos de OSM (con elements)
    if raw_data and 'elements' in raw_data:
        elements = raw_data['elements']
        nodes_geo = {el['id']: el for el in elements if el['type'] == 'node'}
        relations = [el for el in elements if el['type'] == 'relation']
        
        estaciones_dict = {}
        estaciones_por_nombre = {}
        conexiones_vias_set = set()
        conexiones_list = []
        
        for rel in relations:
            tags = rel.get('tags', {})
            line_ref = tags.get('ref', tags.get('name', ''))
            line_id = line_ref.replace('Línea ', '').replace('Linea ', '').strip()
            if not line_id:
                continue
                
            line_stations = []
            for member in rel.get('members', []):
                if member['type'] == 'node':
                    nid = member['ref']
                    if nid in nodes_geo:
                        line_stations.append(nodes_geo[nid])
                        
            if len(line_stations) < 2:
                continue
                
            for node in line_stations:
                raw_name = node.get('tags', {}).get('name')
                if not raw_name:
                    continue
                name = raw_name.strip()
                node_id = f"{name} [{line_id}]"
                
                if node_id not in estaciones_dict:
                    estaciones_dict[node_id] = {
                        "id": node_id,
                        "nombre": name,
                        "linea": line_id,
                        "lat": node['lat'],
                        "lon": node['lon']
                    }
                if name not in estaciones_por_nombre:
                    estaciones_por_nombre[name] = set()
                estaciones_por_nombre[name].add(line_id)
                
            for i in range(len(line_stations) - 1):
                n1, n2 = line_stations[i], line_stations[i+1]
                name1 = n1.get('tags', {}).get('name')
                name2 = n2.get('tags', {}).get('name')
                if not name1 or not name2 or name1.strip() == name2.strip():
                    continue
                id1 = f"{name1.strip()} [{line_id}]"
                id2 = f"{name2.strip()} [{line_id}]"
                edge_id = tuple(sorted([id1, id2]))
                if edge_id not in conexiones_vias_set:
                    conexiones_vias_set.add(edge_id)
                    d_km = haversine(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
                    conexiones_list.append({
                        "origen": id1,
                        "destino": id2,
                        "tiempo": estimate_time(d_km),
                        "linea": line_id,
                        "tipo": "via"
                    })
    else:
        # Si ya teníamos la extracción limpia previa en raw_data, transformamos al modelo Estación-Línea
        print("Transformando la base de datos existente al modelo Estación-Línea...")
        estaciones_dict = {}
        estaciones_por_nombre = {}
        conexiones_vias_set = set()
        conexiones_list = []
        
        # Mapeo de coordenadas y líneas
        for est in raw_data.get('estaciones', []):
            nombre = est['nombre']
            lineas = est.get('lineas', [])
            lat = est.get('lat', 40.4168)
            lon = est.get('lon', -3.7038)
            
            for linea in lineas:
                node_id = f"{nombre} [{linea}]"
                estaciones_dict[node_id] = {
                    "id": node_id,
                    "nombre": nombre,
                    "linea": linea,
                    "lat": lat,
                    "lon": lon
                }
            estaciones_por_nombre[nombre] = set(lineas)
            
        # Conexiones de vía
        for con in raw_data.get('conexiones', []):
            orig = con['origen']
            dest = con['destino']
            linea = con['linea']
            tiempo = con.get('tiempo', 2.0)
            
            id1 = f"{orig} [{linea}]"
            id2 = f"{dest} [{linea}]"
            
            # Asegurar que ambos nodos existan
            if id1 not in estaciones_dict:
                estaciones_dict[id1] = {"id": id1, "nombre": orig, "linea": linea, "lat": 40.4168, "lon": -3.7038}
                if orig not in estaciones_por_nombre:
                    estaciones_por_nombre[orig] = set()
                estaciones_por_nombre[orig].add(linea)
            if id2 not in estaciones_dict:
                estaciones_dict[id2] = {"id": id2, "nombre": dest, "linea": linea, "lat": 40.4168, "lon": -3.7038}
                if dest not in estaciones_por_nombre:
                    estaciones_por_nombre[dest] = set()
                estaciones_por_nombre[dest].add(linea)
                
            edge_id = tuple(sorted([id1, id2]))
            if edge_id not in conexiones_vias_set:
                conexiones_vias_set.add(edge_id)
                conexiones_list.append({
                    "origen": id1,
                    "destino": id2,
                    "tiempo": tiempo,
                    "linea": linea,
                    "tipo": "via"
                })

    # Generar aristas de transbordo entre andenes de la misma estación
    transbordos_generados = 0
    for nombre, lineas in estaciones_por_nombre.items():
        if len(lineas) > 1:
            for l1, l2 in combinations(sorted(lineas), 2):
                id1 = f"{nombre} [{l1}]"
                id2 = f"{nombre} [{l2}]"
                conexiones_list.append({
                    "origen": id1,
                    "destino": id2,
                    "tiempo": transfer_penalty_minutes,
                    "linea": "Transbordo",
                    "tipo": "transbordo"
                })
                transbordos_generados += 1

    dataset_final = {
        "modelo": "estacion_linea",
        "descripcion": "Red del Metro de Madrid modelada como grafo Estación-Línea con transbordos a pie",
        "total_estaciones_linea": len(estaciones_dict),
        "total_estaciones_fisicas": len(estaciones_por_nombre),
        "total_conexiones_via": len(conexiones_vias_set),
        "total_conexiones_transbordo": transbordos_generados,
        "tiempo_transbordo_min": transfer_penalty_minutes,
        "estaciones": list(estaciones_dict.values()),
        "conexiones": conexiones_list
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset_final, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*55)
    print("MODELO ESTACIÓN-LÍNEA GENERADO CON ÉXITO")
    print(f"• Total Nodos (Estaciones-Línea): {len(estaciones_dict)}")
    print(f"• Total Estaciones Físicas: {len(estaciones_por_nombre)}")
    print(f"• Tramos de Vía (Tren): {len(conexiones_vias_set)}")
    print(f"• Aristas de Transbordo (A pie): {transbordos_generados}")
    print(f"• Total Aristas en el Grafo: {len(conexiones_list)}")
    print(f"• Guardado en: {output_file}")
    print("="*55)
    return True

if __name__ == "__main__":
    build_station_line_dataset()
