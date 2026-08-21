from curl_cffi import requests
import gzip
from bs4 import BeautifulSoup
import io

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}
response = requests.get('https://www.arabam.com/sitemap.xml', headers=headers, impersonate="chrome110")
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print(response.text[:500])
