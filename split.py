import os

def split_links():
    with open('cleaned_links.txt', 'r', encoding='utf-8') as f:
        all_links = set(line.strip() for line in f if line.strip())
        
    processed = set()
    if os.path.exists('islenen_linkler.txt'):
        with open('islenen_linkler.txt', 'r', encoding='utf-8') as f:
            processed = set(line.strip() for line in f if line.strip())
            
    remaining = list(all_links - processed)
    
    half = len(remaining) // 2
    
    mac_links = remaining[:half]
    oracle_links = remaining[half:]
    
    with open('mac_kalan.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(mac_links))
        
    with open('oracle_kalan.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(oracle_links))
        
    print(f"Total remaining: {len(remaining)}")
    print(f"Mac links: {len(mac_links)}")
    print(f"Oracle links: {len(oracle_links)}")

if __name__ == '__main__':
    split_links()
