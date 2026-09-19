import requests
import urllib.parse

query = """
[out:json];
area[name="Comunidad de Madrid"]->.searchArea;
relation["route"="subway"]["network"="Metro de Madrid"](area.searchArea);
out body;
>;
out body qt;
"""

url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
headers = {'User-Agent': 'MetroMadridProject/1.0 (contact@example.com)'}

print(f"Testing URL: {url[:100]}...")
resp = requests.get(url, headers=headers)
print(resp.status_code)
if resp.status_code == 200:
    print(f"Success! Elements: {len(resp.json().get('elements', []))}")
else:
    print(resp.text[:200])
