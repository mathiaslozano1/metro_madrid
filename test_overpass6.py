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

data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data)
req.add_header("User-Agent", "Mozilla/5.0")
try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        print(f"Success! Found {len(res.get('elements', []))} elements.")
except Exception as e:
    print(f"Error: {e}")
