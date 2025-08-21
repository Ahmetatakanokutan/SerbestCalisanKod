# -*- coding: utf-8 -*- 

"""
Kırmızı Üçgen ve Mavi Altıgen Tespit Sistemi - Ana Başlatıcı
"""

import os
import sys
import threading
import csv

# Proje kök dizinini (duzenenmisSerbest) Python'un import yolu'na ekle
# Bu sayede alt modüllere (config, gps, vb.) sorunsuz erişilebilir.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CIKTI_CSV, IZLENECEK_KLASOR
from file_watcher.watcher import resim_isleyici_worker, klasor_izleyici, is_kuyrugu

def sistem_hazirla():
    """
    Programın çalışması için gerekli olan klasörleri ve çıktı CSV dosyasını hazırlar.
    """
    os.makedirs(os.path.dirname(CIKTI_CSV), exist_ok=True)
    os.makedirs(IZLENECEK_KLASOR, exist_ok=True)

    if not os.path.exists(CIKTI_CSV) or os.stat(CIKTI_CSV).st_size == 0:
        with open(CIKTI_CSV, "w", newline="", encoding='utf-8') as f:
            yazici = csv.writer(f)
            yazici.writerow(["timestamp", "dosya_adi", "tip", "renk", "enlem", "boylam"])
        print(f"[BİLGİ] Çıktı dosyası oluşturuldu ve başlık yazıldı: {CIKTI_CSV}")

def main():
    """
    Ana fonksiyon: Sistemi hazırlar, worker thread'i ve klasör izleyiciyi başlatır.
    """
    print("="*50)
    print("Kırmızı Üçgen ve Mavi Altıgen Tespit Sistemi Başlatılıyor...")
    print("="*50)
    
    sistem_hazirla()

    worker_thread = threading.Thread(target=resim_isleyici_worker, daemon=True)
    worker_thread.start()
    print("[BİLGİ] Arka plan resim işleyici (worker) başlatıldı.")

    try:
        klasor_izleyici()
    except KeyboardInterrupt:
        print("\n[DURDURULUYOR] Kullanıcı tarafından işlem kesildi. Program kapatılıyor...")
        is_kuyrugu.put(None)
        worker_thread.join(timeout=5)
        print("[KAPATILDI] Program başarıyla sonlandırıldı.")
    except Exception as e:
        print(f"[KRİTİK HATA] Beklenmedik bir hata oluştu: {e}")
    finally:
        print("="*50)

if __name__ == "__main__":
    main()
