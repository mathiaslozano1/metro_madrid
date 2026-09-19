import requests

query = """
[out:json];
node(40.4168,-3.7038,40.4200,-3.7000)["station"="subway"];
out;
"""
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*'
}
response = requests.get('https://overpass-api.de/api/interpreter', params={'data': query}, headers=headers)
print(response.status_code)
print(response.text)
