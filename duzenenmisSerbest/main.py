# -*- coding: utf-8 -*- 

"""
Kırmızı Üçgen ve Mavi Altıgen Tespit Sistemi - Ana Başlatıcı

Bu betik, tüm sistemi başlatan ana giriş noktasıdır.
İki farklı modda çalışabilir:
1. 'folder': Belirtilen bir klasörü yeni resimler için izler,
             GPS verilerini okur ve sonuçları CSV'ye kaydeder.
2. 'webcam': Bilgisayarın varsayılan kamerasından canlı video akışı alır,
             şekilleri tespit eder ve ekranda gerçek zamanlı gösterir.

Çalıştırma Örnekleri:
# Klasör izleme modunda çalıştırmak için:
python main.py --mod folder

# Canlı webcam modunda çalıştırmak için (varsayılan kamera 0):
python main.py --mod webcam

# Belirli bir kamerayı seçmek için (örneğin /dev/video19):
python main.py --mod webcam --camera_index 19
"""

import os
import sys
import threading
import csv
import argparse

# Proje kök dizinini (duzenenmisSerbest) Python'un import yolu'na ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CIKTI_CSV, IZLENECEK_KLASOR
from file_watcher.watcher import resim_isleyici_worker, klasor_izleyici, is_kuyrugu
from video_processor import video_akisini_baslat

def sistem_hazirla():
    """
    Programın çalışması için gerekli olan klasörleri ve çıktı CSV dosyasını hazırlar.
    Bu fonksiyon özellikle 'folder' modu için gereklidir.
    """
    # Çıktı CSV dosyasının bulunduğu dizini oluştur
    os.makedirs(os.path.dirname(CIKTI_CSV), exist_ok=True)
    
    # İzlenecek resim klasörünü oluştur
    os.makedirs(IZLENECEK_KLASOR, exist_ok=True)

    # Eğer CSV dosyası boşsa veya yoksa, başlık satırını yaz
    if not os.path.exists(CIKTI_CSV) or os.stat(CIKTI_CSV).st_size == 0:
        with open(CIKTI_CSV, "w", newline="", encoding='utf-8') as f:
            yazici = csv.writer(f)
            yazici.writerow(["timestamp", "dosya_adi", "tip", "renk", "enlem", "boylam"])
        print(f"[BİLGİ] Çıktı dosyası oluşturuldu ve başlık yazıldı: {CIKTI_CSV}")

def main():
    """
    Ana fonksiyon: Komut satırı argümanlarını ayrıştırır ve seçilen moda göre
    ilgili işlemcileri başlatır.
    """
    # Komut satırı argümanlarını tanımla
    parser = argparse.ArgumentParser(
        description="Kırmızı Üçgen ve Mavi Altıgen Tespit Sistemi."
    )
    parser.add_argument(
        '--mod',
        type=str,
        choices=['folder', 'webcam'],
        required=True,
        help="Çalışma modunu seçin: 'folder' (klasör izleme) veya 'webcam' (canlı video)."
    )
    parser.add_argument(
        '--camera_index',
        type=int,
        default=0,
        help="Webcam modu için kullanılacak kamera indeksi (örn: 0, 1, 19)."
    )
    args = parser.parse_args()

    print("="*50)
    print(f"'{args.mod.upper()}' Modunda Sistem Başlatılıyor...")
    print("="*50)
    
    if args.mod == 'folder':
        # KLASÖR İZLEME MODU
        sistem_hazirla()
        
        worker_thread = threading.Thread(target=resim_isleyici_worker, daemon=True)
        worker_thread.start()
        print("[BİLGİ] Arka plan resim işleyici (worker) başlatıldı.")

        try:
            klasor_izleyici()
        except KeyboardInterrupt:
            print("\n[DURDURULUYOR] Kullanıcı tarafından işlem kesildi...")
            is_kuyrugu.put(None)
            worker_thread.join(timeout=5)
            print("[KAPATILDI] Program başarıyla sonlandırıldı.")
        
    elif args.mod == 'webcam':
        # CANLI VIDEO MODU
        print(f"[BİLGİ] Kamera indeksi {args.camera_index} kullanılıyor.")
        try:
            # Seçilen kamera indeksi ile video akışını başlat
            video_akisini_baslat(kaynak=args.camera_index)
        except KeyboardInterrupt:
            print("\n[DURDURULUYOR] Kullanıcı tarafından işlem kesildi...")
            print("[KAPATILDI] Program başarıyla sonlandırıldı.")

    print("="*50)

if __name__ == "__main__":
    main()