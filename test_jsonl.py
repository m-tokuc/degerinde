import json
import itertools
with open('araba_verileri.jsonl') as f:
    for line in itertools.islice(f, 20):
        data = json.loads(line)
        print("Aciklama:", data.get('Aciklama', 'MISSING')[:50])
