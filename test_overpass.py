import requests

query = """
[out:json];
area[name="Madrid"]->.searchArea;
relation["route"="subway"](area.searchArea);
out tags;
"""

response = requests.get('https://overpass-api.de/api/interpreter', params={'data': query})
if response.status_code == 200:
    data = response.json()
    for el in data.get('elements', []):
        tags = el.get('tags', {})
        name = tags.get('name', 'Unknown')
        ref = tags.get('ref', '')
        print(f'Line: {ref} - {name}')
else:
    print('Failed', response.status_code)
