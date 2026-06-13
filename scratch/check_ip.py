import urllib.request
import json
import ipaddress

ip_to_check = "13.209.26.207"

try:
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    target_ip = ipaddress.ip_address(ip_to_check)
    matched_prefixes = []
    
    for prefix in data.get('prefixes', []):
        net = ipaddress.ip_network(prefix['ip_prefix'])
        if target_ip in net:
            matched_prefixes.append(prefix)
            
    for prefix in data.get('ipv6_prefixes', []):
        net = ipaddress.ip_network(prefix['ipv6_prefix'])
        if target_ip in net:
            matched_prefixes.append(prefix)
            
    print(f"IP {ip_to_check} matches the following prefixes:")
    for p in matched_prefixes:
        print(f"Prefix: {p.get('ip_prefix') or p.get('ipv6_prefix')}, Region: {p.get('region')}, Service: {p.get('service')}, Network Border Group: {p.get('network_border_group')}")
except Exception as e:
    print(f"Error checking IP: {e}")
