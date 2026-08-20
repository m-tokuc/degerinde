import re

PARTS_MAPPING = {
    "kaput": [r"kaput", r"motor kaputu", r"ön kaput"],
    "tavan": [r"tavan"],
    "bagaj": [r"bagaj", r"arka kapak", r"bagaj kapağı"],
    "sol_on_camurluk": [r"sol ön çamurluk", r"sol ön camurluk"],
    "sag_on_camurluk": [r"sağ ön çamurluk", r"sag on camurluk", r"sag ön çamurluk", r"sağ ön camurluk"],
    "sol_arka_camurluk": [r"sol arka çamurluk", r"sol arka camurluk"],
    "sag_arka_camurluk": [r"sağ arka çamurluk", r"sag arka camurluk", r"sag arka çamurluk", r"sağ arka camurluk"],
    "sol_on_kapi": [r"sol ön kapı", r"sol ön kapi"],
    "sag_on_kapi": [r"sağ ön kapı", r"sag on kapi", r"sag ön kapi", r"sağ ön kapi"],
    "sol_arka_kapi": [r"sol arka kapı", r"sol arka kapi"],
    "sag_arka_kapi": [r"sağ arka kapı", r"sag arka kapi", r"sag arka kapi", r"sağ arka kapi"],
    "on_tampon": [r"ön tampon", r"on tampon"],
    "arka_tampon": [r"arka tampon"]
}

def parse_13_parts(text: str) -> dict:
    """
    NLP parser for extracting 13-part damage from Turkish car descriptions.
    0: Orijinal, 1: Lokal Boya, 2: Boyalı, 3: Değişen
    """
    if not isinstance(text, str):
        text = ""
    
    text = text.lower()
    
    # Initialize 13 parts as Orijinal (0)
    results = {k: 0 for k in PARTS_MAPPING.keys()}
    
    if not text.strip():
        return results

    # Global overrides
    if re.search(r"komple boyal[iı]", text):
        for k in results:
            results[k] = 2
        return results
        
    if re.search(r"bel alt[iı] boyal[iı]|tavan hari[cç] boyal[iı]", text):
        for k in results:
            if k != "tavan":
                results[k] = 2
        return results

    # Look for status keywords
    status_regex = r"(de[gğ]i[sş]en|boyal[iı]|lokal|s[oö]k\s*tak)"

    for part_key, keywords in PARTS_MAPPING.items():
        for kw in keywords:
            # 1. Forward match: part ... status (e.g. kaput değişen)
            pattern_fwd = rf"{kw}.{{0,40}}?{status_regex}"
            match_fwd = re.search(pattern_fwd, text)
            
            # 2. Backward match: status ... part (e.g. değişen parçalar: kaput)
            pattern_bwd = rf"{status_regex}.{{0,40}}?{kw}"
            match_bwd = re.search(pattern_bwd, text)
            
            # Use the closest match or the one that exists
            best_match = None
            if match_fwd and match_bwd:
                best_match = match_fwd.group(1) if (match_fwd.end() - match_fwd.start()) < (match_bwd.end() - match_bwd.start()) else match_bwd.group(1)
            elif match_fwd:
                best_match = match_fwd.group(1)
            elif match_bwd:
                best_match = match_bwd.group(1)
            
            if best_match:
                if "lokal" in best_match:
                    results[part_key] = 1
                elif "boyal" in best_match:
                    results[part_key] = 2
                elif "değiş" in best_match or "degis" in best_match or "sök" in best_match or "sok" in best_match:
                    results[part_key] = 3
                break

    return results
