import asyncio
from curl_cffi.requests import AsyncSession

raw_proxies = [
    "31.59.20.176:6754:zbhayjsb:qlg21ds8s8w0",
    "31.56.127.193:7684:zbhayjsb:qlg21ds8s8w0",
    "45.38.107.97:6014:zbhayjsb:qlg21ds8s8w0",
    "198.105.121.200:6462:zbhayjsb:qlg21ds8s8w0",
    "64.137.96.74:6641:zbhayjsb:qlg21ds8s8w0",
    "198.23.243.226:6361:zbhayjsb:qlg21ds8s8w0",
    "38.154.185.97:6370:zbhayjsb:qlg21ds8s8w0",
    "84.247.60.125:6095:zbhayjsb:qlg21ds8s8w0",
    "142.111.67.146:5611:zbhayjsb:qlg21ds8s8w0",
    "191.96.254.138:6185:zbhayjsb:qlg21ds8s8w0"
]

proxies = []
for p in raw_proxies:
    ip, port, user, pwd = p.split(":")
    proxies.append(f"http://{user}:{pwd}@{ip}:{port}")

async def test_proxy(proxy):
    try:
        async with AsyncSession(impersonate="chrome120", proxies={"http": proxy, "https": proxy}, timeout=10) as session:
            resp = await session.get("https://www.arabam.com/ikinci-el", timeout=10)
            if resp.status_code == 200:
                print(f"✅ ÇALIŞIYOR: {proxy.split('@')[1]} -> Status: {resp.status_code}")
            else:
                print(f"⚠️ YANIT VAR AMA ENGELLENDİ/HATA: {proxy.split('@')[1]} -> Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ BAŞARISIZ: {proxy.split('@')[1]} -> Hata: {type(e).__name__}")

async def main():
    print("Yeni yetkilendirmeli proxy'ler test ediliyor...\n")
    await asyncio.gather(*[test_proxy(p) for p in proxies])

if __name__ == '__main__':
    asyncio.run(main())
