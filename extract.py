import re
import json

with open('kadikoy_pazar_analizi.html', 'r', encoding='utf-8') as f:
    text = f.read()

circles = []
for m in re.finditer(r'L\.circle\(\s*\[([-\d\.]+),\s*([-\d\.]+)\]', text):
    circles.append({"lat": float(m.group(1)), "lon": float(m.group(2))})

# deduplicate circles
unique_circles = []
seen = set()
for c in circles:
    k = (c['lat'], c['lon'])
    if k not in seen:
        seen.add(k)
        unique_circles.append(c)

markers = []
for m in re.finditer(r'L\.marker\(\s*\[([-\d\.]+),\s*([-\d\.]+)\]', text):
    lat, lon = float(m.group(1)), float(m.group(2))
    
    start = m.start()
    end = min(start + 1000, len(text))
    chunk = text[start:end]
    
    color = "unknown"
    if '"markerColor": "green"' in chunk:
        color = "green"
    elif '"markerColor": "blue"' in chunk:
        color = "blue"
    elif '"markerColor": "red"' in chunk:
        color = "red"
        
    kind = "Waste" if "Atık" in chunk or "Waste" in chunk or color == "green" else "Repair"
    
    name = "Nokta"
    html_match = re.search(r'<div[^>]*>(.*?)</div>', chunk)
    if html_match:
        name = html_match.group(1).strip()
    elif 'Terzi' in chunk:
        name = "Terzi"
    elif 'Elektronik' in chunk:
        name = "Elektronik Tamiri"
        
    markers.append({"lat": lat, "lon": lon, "name": name, "type": kind})

data = {"markers": markers, "buffers": [{"lat": c["lat"], "lon": c["lon"]} for c in unique_circles]}

with open('map_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(markers)} markers and {len(unique_circles)} circles.")
