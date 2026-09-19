import requests

query = "[out:json];node(50.745,7.17,50.75,7.18)[amenity=cafe];out;"
headers = {
    'User-Agent': 'MetroMadridExtractor/1.0 (contact@example.com)'
}
try:
    response = requests.post('https://overpass.kumi.systems/api/interpreter', data={'data': query}, headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        print(len(response.json().get('elements', [])))
    else:
        print(response.text[:200])
except Exception as e:
    print(e)
