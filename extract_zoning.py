import re
import json

with open('/Users/ilgin/Desktop/514scrapping/kadikoy_zoning_master_analiz.html', 'r', encoding='utf-8') as f:
    text = f.read()

layers = {
    "buffers": "feature_group_e200728eb732e185c964b650364cd3f3",
    "tamirciler": "feature_group_6529b019cffa9a9cd3334df438384137",
    "atik": "feature_group_1902a192f26390d3c7f030ad571f6cd0",
    "parklar": "feature_group_5b4fd8b8f2062441536d95f7fab0194d",
    "kamu": "feature_group_9d2908300ba112e3987a7614379c10f5"
}

data = {
    "buffers": [],
    "tamirciler": [],
    "atik": [],
    "parklar": [],
    "kamu": []
}

# Find circles
circle_pattern = re.compile(r'L\.circle\(\s*\[([-\d\.]+),\s*([-\d\.]+)\][\s\S]*?addTo\((feature_group_[a-f0-9]+)\);')
for m in circle_pattern.finditer(text):
    lat = float(m.group(1))
    lon = float(m.group(2))
    fg = m.group(3)
    for layer_name, layer_fg in layers.items():
        if layer_fg == fg:
            data[layer_name].append({"lat": lat, "lon": lon, "radius": 400})

# Find markers
marker_pattern = re.compile(r'var (marker_[a-f0-9]+)\s*=\s*L\.marker\(\s*\[([-\d\.]+),\s*([-\d\.]+)\][\s\S]*?addTo\((feature_group_[a-f0-9]+)\);')
for m in marker_pattern.finditer(text):
    marker_id = m.group(1)
    lat = float(m.group(2))
    lon = float(m.group(3))
    fg = m.group(4)
    
    layer_match = None
    for layer_name, layer_fg in layers.items():
        if layer_fg == fg:
            layer_match = layer_name
            break
            
    if not layer_match:
        continue
        
    start = m.start()
    chunk = text[start:start+1500]
    
    name = "Nokta"
    html_match = re.search(r'<div[^>]*id="html_[a-f0-9]+"[^>]*>(.*?)</div>', chunk, re.IGNORECASE | re.DOTALL)
    if html_match:
        clean_name = re.sub(r'<[^>]+>', '', html_match.group(1)).strip()
        if clean_name:
            name = clean_name
            
    data[layer_match].append({"lat": lat, "lon": lon, "name": name})

def deduplicate(arr):
    unique = []
    seen = set()
    for item in arr:
        k = (item['lat'], item['lon'])
        if k not in seen:
            seen.add(k)
            unique.append(item)
    return unique

data['buffers'] = deduplicate(data['buffers'])

with open('/Users/ilgin/Desktop/voucher/map_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

for k, v in data.items():
    print(f"Extracted {len(v)} items for {k}")
