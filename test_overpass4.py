import urllib.request
import urllib.parse
import json

query = """
[out:json];
area[name="Comunidad de Madrid"]->.searchArea;
relation["route"="subway"]["network"="Metro de Madrid"](area.searchArea);
out body;
>;
out skel qt;
"""

url = "https://lz4.overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"Success! Found {len(data.get('elements', []))} elements.")
except Exception as e:
    print(f"Error: {e}")
