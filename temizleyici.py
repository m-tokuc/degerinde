import sys
import time
import os

INPUT_FILE = "scraped_links.txt"
OUTPUT_FILE = "cleaned_links.txt"

def is_valid_listing_url(url: str) -> bool:
    """
    Filter to verify if a URL is an actual car listing.
    Requirements:
    1. Must contain '/ilan/' in path.
    2. The final segment of the URL path must be a numeric listing ID.
    """
    if '/ilan/' not in url:
        return False
    
    # Strip query parameters or fragment anchors if any
    clean_url = url.split('?')[0].split('#')[0].rstrip('/')
    
    # Get last path component
    last_segment = clean_url.split('/')[-1]
    
    # Check if the last segment is a numeric listing ID (e.g. 42231653)
    return last_segment.isdigit()

def clean_scraped_links():
    if not os.path.exists(INPUT_FILE):
        print(f"Hata: '{INPUT_FILE}' bulunamadı.")
        return

    print(f"'{INPUT_FILE}' işlenmeye başlanıyor...")
    start_time = time.time()
    
    unique_links = set()
    total_lines = 0
    discarded_count = 0
    duplicate_count = 0
    
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            total_lines += 1
            url = line.strip()
            
            if not url:
                continue
                
            # Normalize URL if relative
            if url.startswith('/'):
                url = 'https://www.arabam.com' + url
                
            # Clean query parameters / fragments
            clean_url = url.split('?')[0].split('#')[0].rstrip('/')
            
            # Apply listing URL filter
            if not is_valid_listing_url(clean_url):
                discarded_count += 1
                continue
                
            # Deduplicate
            if clean_url in unique_links:
                duplicate_count += 1
            else:
                unique_links.add(clean_url)
                
            # Periodic status log for large files
            if total_lines % 5_000_000 == 0:
                elapsed = time.time() - start_time
                print(f"  -> {total_lines:,} satır işlendi... (Tekil Link: {len(unique_links):,}, Geçen Süre: {elapsed:.1f}sn)")

    print(f"\nTemizleme tamamlandı! Sonuçlar '{OUTPUT_FILE}' dosyasına yazılıyor...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        for link in unique_links:
            out_f.write(f"{link}\n")
            
    elapsed_total = time.time() - start_time
    print("=" * 60)
    print(f"İŞLEM RAPORU:")
    print(f"  • Okunan Toplam Satır      : {total_lines:,}")
    print(f"  • Elenen Çöp/Geçersiz Link  : {discarded_count:,}")
    print(f"  • Elenen Çift (Tekrar) Link : {duplicate_count:,}")
    print(f"  • Kalan TEKİL İLAN LİNKİ    : {len(unique_links):,}")
    print(f"  • Toplam Süre              : {elapsed_total:.2f} saniye")
    print(f"  • Çıktı Dosyası            : {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == '__main__':
    clean_scraped_links()
