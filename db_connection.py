import psycopg2
from psycopg2 import pool
import json
import os
from typing import Dict, List, Optional

# PostgreSQL Bağlantı Havuzu
class DatabaseManager:
    def __init__(self):
        self.connection_pool = None
        
    def initialize_pool(self):
        """PostgreSQL bağlantı havuzunu başlat"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1,  # min_connections
                10,  # max_connections
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'arabam_db'),
                user=os.getenv('DB_USER', 'arabam_user'),
                password=os.getenv('DB_PASSWORD', 'your_secure_password'),
                port=os.getenv('DB_PORT', '5432')
            )
            print("PostgreSQL bağlantı havuzu başarıyla oluşturuldu.")
            return True
        except Exception as e:
            print(f"PostgreSQL bağlantı hatası: {e}")
            return False
    
    def get_connection(self):
        """Bağlantı havuzundan bağlantı al"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        return None
    
    def release_connection(self, connection):
        """Bağlantıyı havuza geri bırak"""
        if self.connection_pool and connection:
            self.connection_pool.putconn(connection)
    
    def close_all_connections(self):
        """Tüm bağlantıları kapat"""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("Tüm PostgreSQL bağlantıları kapatıldı.")


class IlanRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def ilan_kaydet(self, ilan_verisi: Dict) -> Optional[int]:
        """İlan verisini veritabanına kaydet"""
        conn = None
        ilan_id = None
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Ana ilan tablosuna kaydet
            insert_query = """
                INSERT INTO ilanlar (
                    url, fiyat, fiyat_birim, marka, model, yil, kilometre,
                    yakit_turu, vites_tipi, motor_gucu, motor_hacmi, cekis,
                    kasa_tipi, kimden, il, ilce, renk, garanti, takas,
                    ilan_no, ekspertiz_raporu, satici_aciklamasi, donanim_paketi,
                    kaza_durumu, boya_degisen, tramer_tutari
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (url) DO UPDATE SET
                    fiyat = EXCLUDED.fiyat,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            cursor.execute(insert_query, (
                ilan_verisi.get('URL'),
                self._fiyat_temizle(ilan_verisi.get('Fiyat')),
                self._fiyat_birim_al(ilan_verisi.get('Fiyat')),
                ilan_verisi.get('Marka'),
                ilan_verisi.get('Model'),
                self._integer_cevir(ilan_verisi.get('Yıl')),
                self._kilometre_temizle(ilan_verisi.get('Kilometre')),
                ilan_verisi.get('Yakıt Tipi'),
                ilan_verisi.get('Vites Tipi'),
                ilan_verisi.get('Motor Gücü'),
                ilan_verisi.get('Motor Hacmi'),
                ilan_verisi.get('Çekiş'),
                ilan_verisi.get('Kasa Tipi'),
                ilan_verisi.get('Kimden'),
                ilan_verisi.get('İl / İlçe'),
                ilan_verisi.get('İlçe'),
                ilan_verisi.get('Renk'),
                ilan_verisi.get('Garanti'),
                ilan_verisi.get('Takas'),
                ilan_verisi.get('İlan No'),
                ilan_verisi.get('Ekspertiz_Raporu'),
                ilan_verisi.get('Satıcı_Açıklaması'),
                ilan_verisi.get('Donanım Paketi'),
                ilan_verisi.get('Kaza Durumu'),
                ilan_verisi.get('Boya, Değişen'),
                self._tramer_temizle(ilan_verisi.get('Tramer Tutarı'))
            ))
            
            ilan_id = cursor.fetchone()[0]
            conn.commit()
            
            # Dinamik özellikleri kaydet
            self._dinamik_ozellikler_kaydet(cursor, ilan_id, ilan_verisi)
            
            conn.commit()
            return ilan_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"İlan kaydetme hatası: {e}")
            return None
        finally:
            if conn:
                self.db_manager.release_connection(conn)
    
    def _dinamik_ozellikler_kaydet(self, cursor, ilan_id: int, ilan_verisi: Dict):
        """Dinamik özellikleri ayrı tabloya kaydet"""
        sabit_anahtarlar = {
            'URL', 'Fiyat', 'Marka', 'Model', 'Yıl', 'Kilometre', 'Yakıt Tipi',
            'Vites Tipi', 'Motor Gücü', 'Motor Hacmi', 'Çekiş', 'Kasa Tipi',
            'Kimden', 'İl / İlçe', 'İlçe', 'Renk', 'Garanti', 'Takas', 'İlan No',
            'Ekspertiz_Raporu', 'Satıcı_Açıklaması', 'Donanım Paketi', 'Kaza Durumu',
            'Boya, Değişen', 'Tramer Tutarı'
        }
        
        for anahtar, deger in ilan_verisi.items():
            if anahtar not in sabit_anahtarlar and deger:
                try:
                    cursor.execute(
                        "INSERT INTO dinamik_ozellikler (ilan_id, ozellik_adi, ozellik_degeri) VALUES (%s, %s, %s)",
                        (ilan_id, anahtar, str(deger))
                    )
                except:
                    continue
    
    def _fiyat_temizle(self, fiyat: str) -> Optional[float]:
        """Fiyat string'ini sayıya çevir"""
        if not fiyat or fiyat == "Belirtilmedi":
            return None
        try:
            # TL, ₺, nokta, virgül karakterlerini temizle
            temiz = fiyat.replace('TL', '').replace('₺', '').replace('.', '').replace(',', '').strip()
            return float(temiz) if temiz else None
        except:
            return None
    
    def _fiyat_birim_al(self, fiyat: str) -> Optional[str]:
        """Fiyat birimini al"""
        if not fiyat:
            return None
        if 'TL' in fiyat or '₺' in fiyat:
            return 'TL'
        if '$' in fiyat:
            return 'USD'
        if '€' in fiyat:
            return 'EUR'
        return None
    
    def _integer_cevir(self, deger: str) -> Optional[int]:
        """String'i integer'a çevir"""
        if not deger:
            return None
        try:
            return int(str(deger).replace('.', '').replace(',', '').strip())
        except:
            return None
    
    def _kilometre_temizle(self, km: str) -> Optional[int]:
        """Kilometre değerini temizle"""
        if not km:
            return None
        try:
            temiz = str(km).replace('km', '').replace('.', '').replace(',', '').strip()
            return int(temiz) if temiz else None
        except:
            return None
    
    _tramer_temizle = _fiyat_temizle  # Tramer temizleme fiyat temizleme ile aynı


# JSONL'den PostgreSQL'e veri aktarma fonksiyonu
def jsonl_to_postgresql(jsonl_dosyasi: str, db_manager: DatabaseManager):
    """JSONL dosyasını okuyup PostgreSQL'e aktar"""
    repo = IlanRepository(db_manager)
    
    with open(jsonl_dosyasi, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                ilan_verisi = json.loads(line.strip())
                ilan_id = repo.ilan_kaydet(ilan_verisi)
                
                if ilan_id:
                    print(f"İlan kaydedildi: ID {ilan_id} - {ilan_verisi.get('URL', 'N/A')}")
                else:
                    print(f"İlan kaydedilemedi: {ilan_verisi.get('URL', 'N/A')}")
                    
            except json.JSONDecodeError:
                print("Geçersiz JSON satırı atlandı")
                continue
            except Exception as e:
                print(f"Hata: {e}")
                continue


if __name__ == "__main__":
    # Test bağlantısı
    db_manager = DatabaseManager()
    
    if db_manager.initialize_pool():
        print("Veritabanı bağlantısı başarılı!")
        
        # JSONL'den veri aktarımı
        if os.path.exists("dev_veriseti.jsonl"):
            print("JSONL dosyası PostgreSQL'e aktarılıyor...")
            jsonl_to_postgresql("dev_veriseti.jsonl", db_manager)
        else:
            print("dev_veriseti.jsonl dosyası bulunamadı!")
        
        db_manager.close_all_connections()
    else:
        print("Veritabanı bağlantısı başarısız!")
