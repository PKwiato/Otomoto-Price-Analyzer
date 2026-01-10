import requests
from bs4 import BeautifulSoup

# Try the most likely parameter
url = "https://www.otomoto.pl/osobowe/bmw/seria-3?search[filter_enum_accident_free]=1"
print(f"Checking URL: {url}")

headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Dump all input names containing 'accident', 'damage', 'wypad'
inputs = soup.find_all("input")
found = False
for i in inputs:
    name = i.get("name", "")
    if any(x in name.lower() for x in ["accident", "damage", "wypad", "collision"]):
        print(f"Found candidate input: {name} (Value: {i.get('value')})")
        found = True

if not found:
    print("No obvious input candidates found in HTML.")

# Also check a few articles to see if they mention it?
# Providing the parameter is accepted, the filter input verification is usually enough.
