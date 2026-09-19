import requests
import json
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en kilómetros entre dos puntos."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def estimate_time(dist_km):
    """Estima el tiempo en minutos asumiendo una velocidad promedio de 30 km/h."""
    tiempo_min = dist_km / 0.5
    return round(max(1.0, tiempo_min), 1)

def fetch_metro_madrid():
    print("Consultando la API de Overpass para descargar la red completa...")
    
    query = """
    [out:json][timeout:250];
    area[name="Comunidad de Madrid"]->.searchArea;
    relation["route"="subway"]["network"="Metro de Madrid"](area.searchArea);
    out body;
    >;
    out body qt;
    """
    
    headers = {
        'User-Agent': 'MetroMadridExtractor/1.0 (contact@example.com)',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(
            'https://overpass.kumi.systems/api/interpreter', 
            data={'data': query},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP de Overpass: {e}")
        print("Asegúrate de no tener bloqueos de red o intenta nuevamente más tarde.")
        return
    except Exception as e:
        print(f"Error general de conexión: {e}")
        return
        
    nodes = {}
    relations = []
    
    for el in data.get('elements', []):
        if el['type'] == 'node':
            nodes[el['id']] = el
        elif el['type'] == 'relation':
            relations.append(el)
            
    estaciones_dict = {}
    conexiones_set = set()
    conexiones_list = []
    
    for rel in relations:
        tags = rel.get('tags', {})
        line_ref = tags.get('ref', tags.get('name', 'Unknown'))
        line_id = line_ref.replace('Línea ', '').replace('Linea ', '')
        
        line_stations = []
        for member in rel.get('members', []):
            if member['type'] == 'node':
                role = member.get('role', '')
                if role in ['stop', 'station', 'stop_entry_only', 'stop_exit_only', '']:
                    node_id = member['ref']
                    if node_id in nodes:
                        line_stations.append(nodes[node_id])
                        
        if len(line_stations) < 2:
            continue
            
        for node in line_stations:
            nid = str(node['id'])
            name = node.get('tags', {}).get('name', f'Estación {nid}')
            
            if nid not in estaciones_dict:
                estaciones_dict[nid] = {
                    "id": nid,
                    "nombre": name,
                    "lineas": set(),
                    "lat": node['lat'],
                    "lon": node['lon']
                }
            estaciones_dict[nid]["lineas"].add(line_id)
            
        for i in range(len(line_stations) - 1):
            n1 = line_stations[i]
            n2 = line_stations[i+1]
            
            id1 = str(n1['id'])
            id2 = str(n2['id'])
            
            conexion_id = tuple(sorted([id1, id2]))
            
            if conexion_id not in conexiones_set:
                conexiones_set.add(conexion_id)
                dist_km = haversine(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
                tiempo = estimate_time(dist_km)
                
                conexiones_list.append({
                    "origen": id1,
                    "destino": id2,
                    "tiempo": tiempo,
                    "linea": line_id
                })

    estaciones_list = []
    for est in estaciones_dict.values():
        est["lineas"] = list(est["lineas"])
        estaciones_list.append(est)
        
    resultado = {
        "estaciones": estaciones_list,
        "conexiones": conexiones_list
    }
    
    with open('./data/metro_madrid.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
        
    print(f"Extracción completada con éxito.")
    print(f"Total de Estaciones extraídas: {len(estaciones_list)}")
    print(f"Total de Conexiones generadas: {len(conexiones_list)}")
    print("El archivo data/metro_madrid.json ha sido actualizado con los datos reales.")

if __name__ == "__main__":
    fetch_metro_madrid()
