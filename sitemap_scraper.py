import xml.etree.ElementTree as ET
from curl_cffi import requests
import os

print("Fetching main sitemap index...")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

response = requests.get('https://www.arabam.com/sitemap.xml', headers=headers, impersonate="chrome110")
if response.status_code != 200:
    print(f"Failed to fetch sitemap index: {response.status_code}")
    exit(1)

root = ET.fromstring(response.text)
namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

# Extract all sitemap URLs
sitemap_urls = [elem.text for elem in root.findall('.//ns:loc', namespaces)]

target_keywords = ['otomobil', 'arazi-suv-pick-up', 'minivan-panelvan']
target_sitemaps = [url for url in sitemap_urls if any(keyword in url for keyword in target_keywords)]

print(f"Found {len(target_sitemaps)} relevant sitemaps. Downloading them now...")

# Load known links
known_links = set()
if os.path.exists('known_links.txt'):
    with open('known_links.txt', 'r', encoding='utf-8') as f:
        known_links = {line.strip() for line in f}

print(f"Loaded {len(known_links)} known links to skip.")

new_links_found = 0
with open('cleaned_links.txt', 'a', encoding='utf-8') as f_out:
    for sitemap_url in target_sitemaps:
        print(f"Fetching {sitemap_url} ...")
        resp = requests.get(sitemap_url, headers=headers, impersonate="chrome110")
        if resp.status_code == 200:
            try:
                sub_root = ET.fromstring(resp.text)
                for loc in sub_root.findall('.//ns:loc', namespaces):
                    link = loc.text.strip()
                    if link not in known_links:
                        f_out.write(link + '\n')
                        known_links.add(link)
                        new_links_found += 1
            except Exception as e:
                print(f"Failed to parse XML for {sitemap_url}: {e}")
        else:
            print(f"Failed {sitemap_url} (HTTP {resp.status_code})")

print(f"Done! Extracted {new_links_found} totally new car links in record time.")
